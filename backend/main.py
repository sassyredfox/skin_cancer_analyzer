from pathlib import Path
import io
import os
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from torchvision import models, transforms


CLASS_ORDER = ["nv", "mel", "bkl", "bcc", "akiec", "vasc", "df"]
CLASS_DETAILS: Dict[str, Dict[str, object]] = {
    "nv": {"name": "Melanocytic nevus", "benign": True, "severity": "low"},
    "mel": {"name": "Melanoma", "benign": False, "severity": "high"},
    "bkl": {"name": "Benign keratosis", "benign": True, "severity": "low"},
    "bcc": {"name": "Basal cell carcinoma", "benign": False, "severity": "medium"},
    "akiec": {"name": "Actinic keratosis", "benign": False, "severity": "high"},
    "vasc": {"name": "Vascular lesion", "benign": True, "severity": "low"},
    "df": {"name": "Dermatofibroma", "benign": True, "severity": "low"},
}

# Lower default threshold for presentation mode while keeping it configurable.
UNCERTAINTY_THRESHOLD = float(os.getenv("UNCERTAINTY_THRESHOLD", "0.35"))
LESION_FOCUS_MIN_RATIO = float(os.getenv("LESION_FOCUS_MIN_RATIO", "1.05"))
STRONG_CONFIDENCE_OVERRIDE = float(os.getenv("STRONG_CONFIDENCE_OVERRIDE", "0.95"))
MODEL_PATH = Path(__file__).resolve().parent / "best_model.pt"
DEFAULT_IMAGE_SIZE = 224


def resolve_inference_device() -> Tuple[torch.device, str, str]:
    if torch.cuda.is_available():
        return torch.device("cuda"), "cuda", torch.cuda.get_device_name(0)

    try:
        import torch_directml

        return torch_directml.device(), "directml", "DirectML GPU"
    except Exception:
        return torch.device("cpu"), "cpu", "CPU"


DEVICE, DEVICE_BACKEND, DEVICE_NAME = resolve_inference_device()

MODEL = None
IDX_TO_CLASS: Dict[int, str] = {i: c for i, c in enumerate(CLASS_ORDER)}


def build_preprocess(image_size: int):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


PREPROCESS = build_preprocess(DEFAULT_IMAGE_SIZE)


def build_model(num_classes: int) -> nn.Module:
    model = models.resnet18(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model


def load_trained_model() -> nn.Module:
    global MODEL, IDX_TO_CLASS, PREPROCESS

    if MODEL is not None:
        return MODEL

    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Trained model not found at {MODEL_PATH}. Run train_model.py before starting the API."
        )

    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    checkpoint_idx_to_class = checkpoint.get("idx_to_class")
    checkpoint_image_size = int(checkpoint.get("image_size", DEFAULT_IMAGE_SIZE))
    if checkpoint_idx_to_class:
        IDX_TO_CLASS = {int(k): v for k, v in checkpoint_idx_to_class.items()}

    PREPROCESS = build_preprocess(checkpoint_image_size)

    model = build_model(num_classes=len(IDX_TO_CLASS))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(DEVICE)
    model.eval()

    MODEL = model
    return MODEL


def preprocess_image(image_data: Image.Image) -> torch.Tensor:
    if image_data.mode != "RGB":
        image_data = image_data.convert("RGB")
    tensor = PREPROCESS(image_data).unsqueeze(0)
    return tensor


def compute_lesion_focus_ratio(image_data: Image.Image, size: int = 224) -> float:
    """Estimate whether the most distinctive region is centered like a lesion close-up."""
    if image_data.mode != "RGB":
        image_data = image_data.convert("RGB")

    arr = np.asarray(image_data.resize((size, size)), dtype=np.float32) / 255.0
    med = np.median(arr.reshape(-1, 3), axis=0)
    dist = np.linalg.norm(arr - med, axis=2)

    h, w = dist.shape
    y, x = np.ogrid[:h, :w]
    radius = (min(h, w) * 0.28) ** 2
    center_mask = ((x - (w / 2)) ** 2 + (y - (h / 2)) ** 2) <= radius

    border = max(8, int(min(h, w) * 0.18))
    border_mask = (x < border) | (x >= (w - border)) | (y < border) | (y >= (h - border))

    center_mean = float(dist[center_mask].mean())
    border_mean = float(dist[border_mask].mean())
    return center_mean / (border_mean + 1e-6)


app = FastAPI(title="Skin Lesion Analyzer", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        load_trained_model()
        print(f"Model loaded from {MODEL_PATH}")
        print(f"Inference backend: {DEVICE_BACKEND}")
        print(f"Inference device: {DEVICE_NAME}")
    except Exception as exc:
        print(f"Startup warning: {exc}")


@app.get("/health")
async def health_check() -> Dict[str, object]:
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "model_path": str(MODEL_PATH),
        "device_backend": DEVICE_BACKEND,
        "device": str(DEVICE),
        "device_name": DEVICE_NAME,
        "uncertainty_threshold": UNCERTAINTY_THRESHOLD,
        "lesion_focus_min_ratio": LESION_FOCUS_MIN_RATIO,
        "strong_confidence_override": STRONG_CONFIDENCE_OVERRIDE,
    }


@app.post("/analyze")
async def analyze_lesion(file: UploadFile = File(...)) -> JSONResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        model = load_trained_model()

        image_bytes = await file.read()
        image_data = Image.open(io.BytesIO(image_bytes))
        input_tensor = preprocess_image(image_data).to(DEVICE)

        with torch.no_grad():
            logits = model(input_tensor)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]

        predicted_idx = int(np.argmax(probabilities))
        predicted_code = IDX_TO_CLASS[predicted_idx]
        max_confidence = float(probabilities[predicted_idx])
        lesion_focus_ratio = compute_lesion_focus_ratio(image_data)

        all_scores: List[Dict[str, object]] = []
        for idx, prob in enumerate(probabilities):
            code = IDX_TO_CLASS[idx]
            all_scores.append({"code": code, "confidence": float(prob)})
        all_scores.sort(key=lambda item: item["confidence"], reverse=True)

        uncertain_reasons: List[str] = []
        if max_confidence < UNCERTAINTY_THRESHOLD:
            uncertain_reasons.append("low_confidence")
        if lesion_focus_ratio < LESION_FOCUS_MIN_RATIO and max_confidence < STRONG_CONFIDENCE_OVERRIDE:
            uncertain_reasons.append("low_lesion_focus")

        if uncertain_reasons:
            return JSONResponse(
                {
                    "uncertain": True,
                    "all_scores": all_scores,
                    "confidence": max_confidence,
                    "lesion_focus_ratio": lesion_focus_ratio,
                    "reasons": uncertain_reasons,
                }
            )

        details = CLASS_DETAILS[predicted_code]
        return JSONResponse(
            {
                "prediction": predicted_code,
                "name": details["name"],
                "confidence": max_confidence,
                "severity": details["severity"],
                "benign": details["benign"],
                "all_scores": all_scores,
                "lesion_focus_ratio": lesion_focus_ratio,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
