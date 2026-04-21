import argparse
import json
from pathlib import Path

import torch
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader

from train_model import (
    CLASS_ORDER,
    build_datasets,
    build_model,
    evaluate_test,
    resolve_dataset,
)

try:
    import torch_directml
except ImportError:
    torch_directml = None


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate HAM10000 checkpoint on test split")
    parser.add_argument("--data-dir", type=str, default="data/HAM10000")
    parser.add_argument("--model-path", type=str, default="best_model.pt")
    parser.add_argument("--output-path", type=str, default="evaluation_metrics.json")
    parser.add_argument("--batch-size", type=int, default=64)
    return parser.parse_args()


def resolve_device():
    if torch.cuda.is_available():
        return torch.device("cuda"), "cuda", torch.cuda.get_device_name(0)
    if torch_directml is not None:
        return torch_directml.device(), "directml", "DirectML GPU"
    return torch.device("cpu"), "cpu", "CPU"


def collect_predictions(model, loader, device):
    model.eval()
    y_true = []
    y_pred = []
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device, non_blocking=False)
            logits = model(images)
            preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
            y_pred.extend(preds)
            y_true.extend(labels.numpy().tolist())
    return y_true, y_pred


def main():
    args = parse_args()
    base_dir = Path(__file__).resolve().parent
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = base_dir / data_dir
    model_path = Path(args.model_path)
    if not model_path.is_absolute():
        model_path = base_dir / model_path
    output_path = Path(args.output_path)
    if not output_path.is_absolute():
        output_path = base_dir / output_path

    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    device, backend, device_name = resolve_device()

    checkpoint = torch.load(model_path, map_location=device)
    image_size = int(checkpoint.get("image_size", 192))

    dataframe = resolve_dataset(data_dir)
    _, _, test_ds, _, _, _ = build_datasets(
        dataframe,
        image_size=image_size,
        cache_images=False,
    )
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = build_model(num_classes=len(CLASS_ORDER)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics = evaluate_test(model, test_loader, device)
    y_true, y_pred = collect_predictions(model, test_loader, device)

    report = classification_report(
        y_true,
        y_pred,
        target_names=CLASS_ORDER,
        output_dict=True,
        zero_division=0,
    )

    payload = {
        "runtime": {
            "device": str(device),
            "device_backend": backend,
            "device_name": device_name,
            "image_size": image_size,
        },
        "test": test_metrics,
        "classification_report": report,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("=" * 80)
    print("Checkpoint Evaluation")
    print("=" * 80)
    print(f"Device backend: {backend}")
    print(f"Device name: {device_name}")
    print(f"Test accuracy: {test_metrics['test_accuracy']:.4f}")
    print(f"Test precision (weighted): {test_metrics['test_precision_weighted']:.4f}")
    print(f"Test recall (weighted): {test_metrics['test_recall_weighted']:.4f}")
    print(f"Test F1 (weighted): {test_metrics['test_f1_weighted']:.4f}")
    print(f"Saved report: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
