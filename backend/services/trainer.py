"""Custom-dataset training service.

Lets a teacher upload a YOLOv8-format dataset (a .zip exported from Roboflow,
Kaggle, Google Open Images, etc.), train a YOLOv8s detector on it in a
background thread, and have the resulting model become the live detector used
by the Vision tab and the `camera sees` block.

Workflow:
  1. upload_dataset(zip_bytes)  -> unzip, locate + validate data.yaml, return
                                   detected class names + image counts.
  2. start_training(epochs, imgsz) -> launch YOLO().train() in a daemon thread.
  3. get_status()               -> poll progress for the UI.
  On success the new best.pt is copied to models/lego_detector.pt (the canonical
  deploy path that get_model_path() finds first) and detection.reload() is
  called so /detect uses it immediately, no server restart.

Per-project storage under projects/<name>/training/:
  - dataset/        the unzipped uploaded dataset (data.yaml + images/ + labels/)
  - runs/           ultralytics training output
"""

import shutil
import sys
import threading
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import MODEL_PATH

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ── shared training state (single active job; this is a classroom tool) ──────
_lock = threading.Lock()
_state = {
    "state": "idle",          # idle | training | done | error
    "epoch": 0,
    "total_epochs": 0,
    "message": "",
    "metrics": {},            # populated on completion
    "classes": [],
}


def _project_dir(project_name: str) -> Path:
    d = _ROOT / "projects" / project_name / "training"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _dataset_dir(project_name: str) -> Path:
    return _project_dir(project_name) / "dataset"


def _find_data_yaml(root: Path) -> Optional[Path]:
    """Locate data.yaml in the unzipped tree (top level first, then anywhere)."""
    direct = root / "data.yaml"
    if direct.exists():
        return direct
    candidates = sorted(root.rglob("data.yaml"), key=lambda p: len(p.parts))
    return candidates[0] if candidates else None


def _resolve_paths_in_yaml(data_yaml: Path) -> dict:
    """Load data.yaml and rewrite train/val/test to absolute paths.

    Roboflow/Kaggle exports use relative paths like '../train/images' that only
    resolve from the yaml's own folder. We rewrite them to absolute paths so
    ultralytics finds the images regardless of its working directory, then write
    the resolved copy back to disk.
    """
    cfg = yaml.safe_load(data_yaml.read_text(encoding="utf-8")) or {}
    base = data_yaml.parent

    def _abs(val):
        p = Path(val)
        if not p.is_absolute():
            p = (base / p).resolve()
        return str(p)

    for split in ("train", "val", "test"):
        if cfg.get(split):
            cfg[split] = _abs(cfg[split])

    # 'path' (dataset root) is honored by ultralytics; pin it to the yaml folder.
    cfg["path"] = str(base.resolve())

    data_yaml.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return cfg


def _class_names(cfg: dict) -> list:
    """Extract ordered class names from a YOLO data.yaml 'names' field.

    'names' may be a list (['a','b']) or a dict ({0:'a', 1:'b'}).
    """
    names = cfg.get("names", [])
    if isinstance(names, dict):
        return [names[k] for k in sorted(names, key=lambda x: int(x))]
    return list(names)


def _count_images(root: Path) -> int:
    return sum(
        1 for p in root.rglob("*")
        if p.suffix.lower() in IMAGE_EXTENSIONS and "labels" not in p.parts
    )


def upload_dataset(project_name: str, zip_bytes: bytes) -> dict:
    """Unzip an uploaded YOLOv8 dataset and validate it.

    Returns {classes, num_classes, num_images, data_yaml} on success.
    Raises ValueError with a teacher-friendly message on any problem.
    """
    if not zip_bytes:
        raise ValueError("Empty upload — choose a .zip dataset file.")

    try:
        zf = zipfile.ZipFile(BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise ValueError("That file isn't a valid .zip archive.")

    dataset = _dataset_dir(project_name)
    if dataset.exists():
        shutil.rmtree(dataset)
    dataset.mkdir(parents=True, exist_ok=True)

    # Guard against zip-slip: reject entries that escape the target dir.
    for member in zf.namelist():
        target = (dataset / member).resolve()
        if not str(target).startswith(str(dataset.resolve())):
            raise ValueError("Unsafe path in zip archive; aborting.")
    zf.extractall(dataset)

    data_yaml = _find_data_yaml(dataset)
    if data_yaml is None:
        raise ValueError(
            "No data.yaml found in the zip. Export your dataset in "
            "'YOLOv8' format (it includes a data.yaml file)."
        )

    cfg = _resolve_paths_in_yaml(data_yaml)
    classes = _class_names(cfg)
    if not classes:
        raise ValueError("data.yaml has no class names. Re-export in YOLOv8 format.")

    num_images = _count_images(dataset)
    if num_images == 0:
        raise ValueError("No images found in the dataset. Check the zip contents.")

    with _lock:
        _state.update(state="idle", epoch=0, total_epochs=0,
                      message="Dataset ready to train.", metrics={}, classes=classes)

    return {
        "classes": classes,
        "num_classes": len(classes),
        "num_images": num_images,
        "data_yaml": str(data_yaml),
    }


def _train_worker(project_name: str, epochs: int, imgsz: int):
    """Background training job. Updates _state as it runs."""
    try:
        from ultralytics import YOLO
        import torch

        dataset = _dataset_dir(project_name)
        data_yaml = _find_data_yaml(dataset)
        if data_yaml is None:
            raise RuntimeError("Dataset not found. Upload a dataset first.")

        cfg = yaml.safe_load(data_yaml.read_text(encoding="utf-8")) or {}
        classes = _class_names(cfg)
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        with _lock:
            _state.update(state="training", epoch=0, total_epochs=epochs,
                          message=f"Training on {device}...", classes=classes)

        model = YOLO("yolov8s.pt")  # start from pretrained COCO weights (small: more accurate than n, still real-time)

        def _on_epoch_end(trainer):
            with _lock:
                _state["epoch"] = int(getattr(trainer, "epoch", 0)) + 1
                _state["message"] = f"Epoch {_state['epoch']}/{epochs}"

        model.add_callback("on_fit_epoch_end", _on_epoch_end)

        runs_dir = _project_dir(project_name) / "runs"
        model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            device=device,
            project=str(runs_dir),
            name="custom",
            exist_ok=True,
            verbose=False,
            plots=False,
        )

        best = runs_dir / "custom" / "weights" / "best.pt"
        if not best.exists():
            raise RuntimeError("Training finished but no best.pt was produced.")

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, MODEL_PATH)

        # Swap the live detector over to the new model without a restart.
        from backend.services import detection
        detection.reload()

        with _lock:
            _state.update(
                state="done",
                epoch=epochs,
                message=f"Done — your model is now live with {len(classes)} classes.",
                classes=classes,
            )

    except Exception as e:  # noqa: BLE001 — surface any failure to the UI
        with _lock:
            _state.update(state="error", message=f"Training failed: {e}")


def start_training(project_name: str = "default", epochs: int = 20,
                   imgsz: int = 640) -> dict:
    """Kick off training in a background thread. Rejects if one is running."""
    with _lock:
        if _state["state"] == "training":
            raise ValueError("Training is already in progress.")
        if not _find_data_yaml(_dataset_dir(project_name)):
            raise ValueError("Upload a dataset before training.")
        _state.update(state="training", epoch=0, total_epochs=epochs,
                      message="Starting...", metrics={})

    t = threading.Thread(
        target=_train_worker, args=(project_name, epochs, imgsz), daemon=True
    )
    t.start()
    return {"state": "training", "total_epochs": epochs}


def get_status() -> dict:
    with _lock:
        return dict(_state)


def get_classes(project_name: str = "default") -> list:
    """Class names of the currently uploaded/trained dataset, if any."""
    with _lock:
        if _state["classes"]:
            return list(_state["classes"])
    data_yaml = _find_data_yaml(_dataset_dir(project_name))
    if data_yaml:
        cfg = yaml.safe_load(data_yaml.read_text(encoding="utf-8")) or {}
        return _class_names(cfg)
    return []
