import argparse
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

try:
    import torch_directml
except ImportError:
    torch_directml = None


CLASS_ORDER = ["nv", "mel", "bkl", "bcc", "akiec", "vasc", "df"]
CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_ORDER)}
IDX_TO_CLASS = {idx: name for name, idx in CLASS_TO_IDX.items()}


@dataclass
class EpochMetrics:
    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float
    val_accuracy: float
    lr: float
    elapsed_seconds: float


class HAM10000Dataset(Dataset):
    def __init__(
        self,
        frame: pd.DataFrame,
        transform: transforms.Compose,
        cache_images: bool = False,
        cache_image_size: int = 224,
    ):
        self.frame = frame.reset_index(drop=True)
        self.transform = transform
        self.cache_images = cache_images
        self.cache_image_size = cache_image_size
        self.cached_arrays = None

        if self.cache_images:
            self.cached_arrays = []
            total = len(self.frame)
            print(f"Caching {total} images into memory at {self.cache_image_size}x{self.cache_image_size}...")
            for idx, row in self.frame.iterrows():
                image = Image.open(row["image_path"]).convert("RGB")
                image = image.resize((self.cache_image_size, self.cache_image_size), Image.Resampling.BILINEAR)
                self.cached_arrays.append(np.asarray(image, dtype=np.uint8))
                if (idx + 1) % 1000 == 0 or (idx + 1) == total:
                    print(f"  cached {idx + 1}/{total}")

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int):
        row = self.frame.iloc[index]
        if self.cached_arrays is not None:
            image = Image.fromarray(self.cached_arrays[index], mode="RGB")
        else:
            image = Image.open(row["image_path"]).convert("RGB")
        tensor = self.transform(image)
        label = int(row["class_idx"])
        return tensor, label


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve_dataset(data_dir: Path) -> pd.DataFrame:
    metadata_path = data_dir / "HAM10000_metadata.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found at {metadata_path}")

    metadata = pd.read_csv(metadata_path)
    metadata = metadata[metadata["dx"].isin(CLASS_ORDER)].copy()

    part_1 = data_dir / "HAM10000_images_part_1"
    part_2 = data_dir / "HAM10000_images_part_2"

    def image_path_for_id(image_id: str) -> str:
        candidate_1 = part_1 / f"{image_id}.jpg"
        candidate_2 = part_2 / f"{image_id}.jpg"
        if candidate_1.exists():
            return str(candidate_1)
        if candidate_2.exists():
            return str(candidate_2)
        return ""

    metadata["image_path"] = metadata["image_id"].apply(image_path_for_id)
    metadata = metadata[metadata["image_path"] != ""].copy()
    metadata["class_idx"] = metadata["dx"].map(CLASS_TO_IDX)

    if metadata.empty:
        raise RuntimeError("No valid images found after resolving dataset paths.")

    return metadata


def build_datasets(dataframe: pd.DataFrame, image_size: int, cache_images: bool):
    train_df, temp_df = train_test_split(
        dataframe,
        test_size=0.20,
        random_state=42,
        stratify=dataframe["class_idx"],
    )
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=42,
        stratify=temp_df["class_idx"],
    )

    train_steps = []
    if not cache_images:
        train_steps.append(transforms.Resize((image_size, image_size)))
    train_steps.extend(
        [
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=8),
            transforms.ColorJitter(brightness=0.08, contrast=0.08, saturation=0.06, hue=0.0),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    train_tfms = transforms.Compose(train_steps)

    eval_steps = []
    if not cache_images:
        eval_steps.append(transforms.Resize((image_size, image_size)))
    eval_steps.extend(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    eval_tfms = transforms.Compose(eval_steps)

    return (
        HAM10000Dataset(train_df, train_tfms, cache_images=cache_images, cache_image_size=image_size),
        HAM10000Dataset(val_df, eval_tfms, cache_images=cache_images, cache_image_size=image_size),
        HAM10000Dataset(test_df, eval_tfms, cache_images=cache_images, cache_image_size=image_size),
        train_df,
        val_df,
        test_df,
    )


def build_model(num_classes: int) -> nn.Module:
    try:
        weights = models.ResNet18_Weights.IMAGENET1K_V1
        model = models.resnet18(weights=weights)
        print("Loaded ImageNet pretrained ResNet18 weights.")
    except Exception:
        model = models.resnet18(weights=None)
        print("Warning: Could not load pretrained weights, training from scratch.")

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    # Stage 1: train classification head first.
    for param in model.parameters():
        param.requires_grad = False
    for param in model.fc.parameters():
        param.requires_grad = True

    return model


def unfreeze_backbone(model: nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = True


def build_optimizer(
    model: nn.Module,
    device_backend: str,
    lr: float,
    weight_decay: float,
):
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    if device_backend == "directml":
        return torch.optim.SGD(
            trainable_params,
            lr=lr,
            weight_decay=weight_decay,
            momentum=0.9,
            nesterov=True,
        )
    return torch.optim.AdamW(trainable_params, lr=lr, weight_decay=weight_decay)


def build_dataloaders(
    train_ds: Dataset,
    val_ds: Dataset,
    test_ds: Dataset,
    batch_size: int,
    num_workers: int,
    pin_memory: bool,
):
    common = {
        "batch_size": batch_size,
        "num_workers": num_workers,
        "pin_memory": pin_memory,
        "persistent_workers": num_workers > 0,
    }
    train_loader = DataLoader(train_ds, shuffle=True, **common)
    val_loader = DataLoader(val_ds, shuffle=False, **common)
    test_loader = DataLoader(test_ds, shuffle=False, **common)
    return train_loader, val_loader, test_loader


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer,
    device: torch.device,
    scaler: torch.cuda.amp.GradScaler,
    train: bool,
    use_amp: bool,
) -> Tuple[float, float]:
    if train:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    preds_all: List[int] = []
    labels_all: List[int] = []

    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        if train:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(train):
            with torch.amp.autocast("cuda", enabled=use_amp):
                logits = model(images)
                loss = criterion(logits, labels)

            if train:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()

        total_loss += loss.item() * images.size(0)
        preds_all.extend(torch.argmax(logits, dim=1).detach().cpu().numpy().tolist())
        labels_all.extend(labels.detach().cpu().numpy().tolist())

    epoch_loss = total_loss / len(loader.dataset)
    epoch_accuracy = accuracy_score(labels_all, preds_all)
    return epoch_loss, epoch_accuracy


def evaluate_test(model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, float]:
    model.eval()
    preds_all: List[int] = []
    labels_all: List[int] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            logits = model(images)
            preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
            preds_all.extend(preds)
            labels_all.extend(labels.numpy().tolist())

    accuracy = accuracy_score(labels_all, preds_all)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels_all,
        preds_all,
        average="weighted",
        zero_division=0,
    )

    return {
        "test_accuracy": float(accuracy),
        "test_precision_weighted": float(precision),
        "test_recall_weighted": float(recall),
        "test_f1_weighted": float(f1),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Train production CNN model on HAM10000")
    parser.add_argument("--data-dir", type=str, default="data/HAM10000")
    parser.add_argument("--image-size", type=int, default=192)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument(
        "--batch-size-unfreeze",
        type=int,
        default=64,
        help="Batch size to use after unfreezing backbone (<=0 keeps initial batch size)",
    )
    parser.add_argument("--lr-head", type=float, default=1e-3)
    parser.add_argument("--lr-finetune", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--unfreeze-epoch", type=int, default=4)
    parser.add_argument("--target-val-acc", type=float, default=0.80)
    parser.add_argument("--min-epochs", type=int, default=6)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--no-cache-images", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-model", type=str, default="best_model.pt")
    parser.add_argument("--output-metrics", type=str, default="training_metrics.json")
    parser.add_argument("--resume-checkpoint", type=str, default="")
    parser.add_argument("--allow-cpu", action="store_true", help="Allow CPU training if CUDA is unavailable")
    return parser.parse_args()


def resolve_training_device(allow_cpu: bool):
    if torch.cuda.is_available():
        device = torch.device("cuda")
        return device, "cuda", torch.cuda.get_device_name(0)

    if torch_directml is not None:
        device = torch_directml.device()
        return device, "directml", "DirectML GPU"

    if not allow_cpu:
        raise RuntimeError(
            "No GPU backend available. Install CUDA-enabled PyTorch or torch-directml, then retry."
        )

    return torch.device("cpu"), "cpu", None


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    device, device_backend, gpu_name = resolve_training_device(args.allow_cpu)

    print("=" * 80)
    print("HAM10000 Production Training")
    print("=" * 80)
    print(f"PyTorch version: {torch.__version__}")
    print(f"Training device: {device}")
    print(f"Device backend: {device_backend}")
    if gpu_name:
        print(f"GPU name: {gpu_name}")
    if device_backend == "cuda":
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = Path(__file__).resolve().parent / data_dir

    dataframe = resolve_dataset(data_dir)
    cache_images = not args.no_cache_images
    train_ds, val_ds, test_ds, train_df, val_df, test_df = build_datasets(
        dataframe,
        args.image_size,
        cache_images,
    )

    print(f"Total images: {len(dataframe)}")
    print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    pin_memory = device_backend == "cuda"
    current_batch_size = args.batch_size
    train_loader, val_loader, test_loader = build_dataloaders(
        train_ds,
        val_ds,
        test_ds,
        batch_size=current_batch_size,
        num_workers=args.num_workers,
        pin_memory=pin_memory,
    )
    print(f"Initial batch size: {current_batch_size}")

    model = build_model(num_classes=len(CLASS_ORDER)).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = build_optimizer(model, device_backend, args.lr_head, args.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=2, min_lr=1e-6
    )
    scaler = torch.amp.GradScaler("cuda", enabled=device_backend == "cuda")
    use_amp = device_backend == "cuda"

    history: List[EpochMetrics] = []
    best_val_loss = float("inf")
    best_val_acc = 0.0
    best_epoch = -1
    start_epoch = 1
    bad_epochs = 0
    backbone_unfrozen = False

    output_model = Path(__file__).resolve().parent / args.output_model
    output_metrics = Path(__file__).resolve().parent / args.output_metrics

    resume_checkpoint_path = None
    if args.resume_checkpoint:
        candidate = Path(args.resume_checkpoint)
        resume_checkpoint_path = candidate if candidate.is_absolute() else Path(__file__).resolve().parent / candidate

    if resume_checkpoint_path and resume_checkpoint_path.exists():
        print(f"Resuming from checkpoint: {resume_checkpoint_path}")
        resume_ckpt = torch.load(resume_checkpoint_path, map_location=device)
        model.load_state_dict(resume_ckpt["model_state_dict"])
        best_val_loss = float(resume_ckpt.get("best_val_loss", best_val_loss))
        best_val_acc = float(resume_ckpt.get("best_val_accuracy", best_val_acc))
        best_epoch = int(resume_ckpt.get("best_epoch", best_epoch))
        start_epoch = best_epoch + 1 if best_epoch > 0 else 1
        print(
            f"Resume state: best_epoch={best_epoch}, best_val_loss={best_val_loss:.4f}, "
            f"best_val_accuracy={best_val_acc:.4f}"
        )

        # If resuming after unfreeze epoch, continue with full fine-tuning.
        if best_epoch >= args.unfreeze_epoch:
            unfreeze_backbone(model)
            backbone_unfrozen = True
            if args.batch_size_unfreeze > 0 and args.batch_size_unfreeze < current_batch_size:
                current_batch_size = args.batch_size_unfreeze
                train_loader, val_loader, test_loader = build_dataloaders(
                    train_ds,
                    val_ds,
                    test_ds,
                    batch_size=current_batch_size,
                    num_workers=args.num_workers,
                    pin_memory=pin_memory,
                )
                print(f"Reduced batch size for fine-tuning: {current_batch_size}")
            optimizer = build_optimizer(model, device_backend, args.lr_finetune, args.weight_decay)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="max", factor=0.5, patience=2, min_lr=1e-6
            )

    if start_epoch > args.epochs:
        print(
            f"Requested epochs ({args.epochs}) already reached by checkpoint best epoch ({best_epoch}). "
            f"Set a higher --epochs value to continue training."
        )
        start_epoch = args.epochs + 1

    start = time.time()
    for epoch in range(start_epoch, args.epochs + 1):
        if (not backbone_unfrozen) and epoch >= args.unfreeze_epoch:
            print(f"Unfreezing backbone at epoch {epoch} for full fine-tuning...")
            unfreeze_backbone(model)
            backbone_unfrozen = True
            if args.batch_size_unfreeze > 0 and args.batch_size_unfreeze < current_batch_size:
                current_batch_size = args.batch_size_unfreeze
                train_loader, val_loader, test_loader = build_dataloaders(
                    train_ds,
                    val_ds,
                    test_ds,
                    batch_size=current_batch_size,
                    num_workers=args.num_workers,
                    pin_memory=pin_memory,
                )
                print(f"Reduced batch size for fine-tuning: {current_batch_size}")
            optimizer = build_optimizer(model, device_backend, args.lr_finetune, args.weight_decay)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="max", factor=0.5, patience=2, min_lr=1e-6
            )

        while True:
            epoch_start = time.time()
            try:
                train_loss, train_acc = run_epoch(
                    model=model,
                    loader=train_loader,
                    criterion=criterion,
                    optimizer=optimizer,
                    device=device,
                    scaler=scaler,
                    train=True,
                    use_amp=use_amp,
                )
                val_loss, val_acc = run_epoch(
                    model=model,
                    loader=val_loader,
                    criterion=criterion,
                    optimizer=optimizer,
                    device=device,
                    scaler=scaler,
                    train=False,
                    use_amp=use_amp,
                )
                break
            except RuntimeError as err:
                message = str(err).lower()
                if "out of memory" not in message or current_batch_size <= 16:
                    raise

                new_batch_size = max(16, current_batch_size // 2)
                if new_batch_size == current_batch_size:
                    raise

                print(
                    f"OOM at batch_size={current_batch_size}. Retrying epoch {epoch} with batch_size={new_batch_size}..."
                )
                current_batch_size = new_batch_size
                if device_backend == "cuda":
                    torch.cuda.empty_cache()
                optimizer.zero_grad(set_to_none=True)
                train_loader, val_loader, test_loader = build_dataloaders(
                    train_ds,
                    val_ds,
                    test_ds,
                    batch_size=current_batch_size,
                    num_workers=args.num_workers,
                    pin_memory=pin_memory,
                )

        scheduler.step(val_acc)
        lr = optimizer.param_groups[0]["lr"]
        elapsed = time.time() - epoch_start

        row = EpochMetrics(
            epoch=epoch,
            train_loss=float(train_loss),
            train_accuracy=float(train_acc),
            val_loss=float(val_loss),
            val_accuracy=float(val_acc),
            lr=float(lr),
            elapsed_seconds=float(elapsed),
        )
        history.append(row)

        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | lr={lr:.7f}"
        )

        improved = val_acc > best_val_acc
        if improved:
            best_val_loss = val_loss
            best_val_acc = val_acc
            best_epoch = epoch
            bad_epochs = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_to_idx": CLASS_TO_IDX,
                    "idx_to_class": IDX_TO_CLASS,
                    "model_name": "resnet18",
                    "image_size": args.image_size,
                    "normalization": {
                        "mean": [0.485, 0.456, 0.406],
                        "std": [0.229, 0.224, 0.225],
                    },
                    "best_val_loss": float(best_val_loss),
                    "best_val_accuracy": float(best_val_acc),
                    "best_epoch": int(best_epoch),
                    "timestamp_unix": int(time.time()),
                },
                output_model,
            )
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                print(f"Early stopping triggered at epoch {epoch}.")
                break

        if epoch >= args.min_epochs and best_val_acc >= args.target_val_acc:
            print(
                f"Target validation accuracy reached: {best_val_acc:.4f} >= {args.target_val_acc:.4f}."
            )
            break

    training_seconds = time.time() - start

    checkpoint = torch.load(output_model, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)

    test_metrics = evaluate_test(model, test_loader, device)

    metrics_payload = {
        "config": {
            "epochs_requested": args.epochs,
            "batch_size": args.batch_size,
            "batch_size_unfreeze": args.batch_size_unfreeze,
            "effective_batch_size": current_batch_size,
            "lr_head": args.lr_head,
            "lr_finetune": args.lr_finetune,
            "weight_decay": args.weight_decay,
            "patience": args.patience,
            "unfreeze_epoch": args.unfreeze_epoch,
            "target_val_acc": args.target_val_acc,
            "min_epochs": args.min_epochs,
            "cache_images": cache_images,
            "seed": args.seed,
            "allow_cpu": args.allow_cpu,
        },
        "dataset": {
            "total": int(len(dataframe)),
            "train": int(len(train_df)),
            "val": int(len(val_df)),
            "test": int(len(test_df)),
            "image_size": int(args.image_size),
            "class_order": CLASS_ORDER,
        },
        "runtime": {
            "device": str(device),
            "device_backend": device_backend,
            "gpu_name": gpu_name,
            "training_seconds": float(training_seconds),
            "best_epoch": int(best_epoch),
            "best_val_loss": float(best_val_loss),
            "best_val_accuracy": float(best_val_acc),
        },
        "history": [asdict(row) for row in history],
        "test": test_metrics,
    }

    with open(output_metrics, "w", encoding="utf-8") as fp:
        json.dump(metrics_payload, fp, indent=2)

    print("=" * 80)
    print("Training complete")
    print(f"Best model: {output_model}")
    print(f"Metrics file: {output_metrics}")
    print(
        f"Final test metrics: accuracy={test_metrics['test_accuracy']:.4f}, "
        f"precision={test_metrics['test_precision_weighted']:.4f}, "
        f"recall={test_metrics['test_recall_weighted']:.4f}, "
        f"f1={test_metrics['test_f1_weighted']:.4f}"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
