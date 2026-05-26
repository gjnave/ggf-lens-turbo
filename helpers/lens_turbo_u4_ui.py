from __future__ import annotations

import contextlib
import ctypes
import io
import json
import os
import random
import sys
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QThread, Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

MODEL_ID = "WaveCut/Lens-Turbo-SDNQ-uint4-static"
DEFAULT_THEME = "Get Going Fast"
MAX_SAVED_FINISHED = 10
RESOLUTION_PRESETS = {
    "1:1": [
        ("1024 (base res)", "base", 1024, 1024, 1024),
        ("1440 (base res)", "base", 1440, 1440, 1440),
        ("Custom", "custom", 0, 1024, 1024),
    ],
    "16:9": [
        ("1024 (base res)", "base", 1024, 1376, 768),
        ("1440 (base res)", "base", 1440, 1936, 1088),
        ("Custom", "custom", 0, 1280, 704),
    ],
    "9:16": [
        ("1024 (base res)", "base", 1024, 768, 1376),
        ("1440 (base res)", "base", 1440, 1088, 1936),
        ("Custom", "custom", 0, 704, 1280),
    ],
}
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION_PRESET = "1024 (base res)"
CUSTOM_RESOLUTION_LABEL = "Custom"

THEMES = {
    "Get Going Fast": """
        QWidget { background-color: #0a0a0a; color: #f0f0f0; font-family: "Segoe UI", Arial, sans-serif; }
        QMainWindow, QTabWidget::pane, QScrollArea { background-color: #0a0a0a; }
        QLabel#brandTitle { color: #00e676; font-size: 22px; font-weight: 700; letter-spacing: 1px; }
        QLabel#brandSubtitle { color: #b0b0b0; font-size: 12px; }
        QLabel#brandLink { color: #f0f0f0; }
        QLabel#brandLink a { color: #00e676; }
        QGroupBox { background-color: #1a1a1a; border: 1px solid #343434; border-radius: 12px; margin-top: 12px; padding-top: 10px; font-weight: 600; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #00e676; background-color: #0a0a0a; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background-color: #141414; color: #f0f0f0; border: 1px solid #4a4a4a; border-radius: 8px; padding: 5px; selection-background-color: #00e676; selection-color: #07130b; }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #00e676; }
        QPushButton { background-color: #00e676; color: #07130b; border: 1px solid #00e676; border-radius: 9px; padding: 7px 12px; font-weight: 600; }
        QPushButton:hover { background-color: #35f18b; }
        QPushButton:pressed { background-color: #00bd60; }
        QPushButton:disabled { color: #7c887f; background-color: #242824; border-color: #3b453d; }
        QTabBar::tab { background-color: #1a1a1a; color: #b0b0b0; padding: 9px 15px; border: 1px solid #343434; border-bottom: none; border-top-left-radius: 9px; border-top-right-radius: 9px; }
        QTabBar::tab:selected { background-color: #202820; color: #00e676; border-color: #00e676; }
        QTabBar::tab:hover { color: #f0f0f0; }
        QCheckBox { spacing: 7px; }
    """,
    "Dark": """
        QWidget { background-color: #1f1f1f; color: #eeeeee; }
        QMainWindow, QTabWidget::pane, QScrollArea { background-color: #1f1f1f; }
        QGroupBox { border: 1px solid #4a4a4a; border-radius: 7px; margin-top: 12px; padding-top: 10px; font-weight: 600; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background-color: #2b2b2b; color: #f1f1f1; border: 1px solid #555; border-radius: 5px; padding: 4px; selection-background-color: #3d6fb6; }
        QPushButton { background-color: #3a3a3a; color: #f1f1f1; border: 1px solid #666; border-radius: 6px; padding: 6px 10px; }
        QPushButton:hover { background-color: #474747; }
        QPushButton:disabled { color: #888; background-color: #292929; border-color: #444; }
        QTabBar::tab { background-color: #2a2a2a; color: #e5e5e5; padding: 8px 14px; border: 1px solid #444; border-bottom: none; }
        QTabBar::tab:selected { background-color: #383838; }
        QCheckBox { spacing: 6px; }
    """,
    "Midnight": """
        QWidget { background-color: #111827; color: #e5e7eb; }
        QMainWindow, QTabWidget::pane, QScrollArea { background-color: #111827; }
        QGroupBox { border: 1px solid #374151; border-radius: 7px; margin-top: 12px; padding-top: 10px; font-weight: 600; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background-color: #1f2937; color: #f9fafb; border: 1px solid #4b5563; border-radius: 5px; padding: 4px; selection-background-color: #2563eb; }
        QPushButton { background-color: #243244; color: #f9fafb; border: 1px solid #4b5563; border-radius: 6px; padding: 6px 10px; }
        QPushButton:hover { background-color: #2f4058; }
        QPushButton:disabled { color: #6b7280; background-color: #1a2230; border-color: #374151; }
        QTabBar::tab { background-color: #1f2937; color: #e5e7eb; padding: 8px 14px; border: 1px solid #374151; border-bottom: none; }
        QTabBar::tab:selected { background-color: #273449; }
        QCheckBox { spacing: 6px; }
    """,
    "Slate": """
        QWidget { background-color: #263238; color: #eceff1; }
        QMainWindow, QTabWidget::pane, QScrollArea { background-color: #263238; }
        QGroupBox { border: 1px solid #607d8b; border-radius: 7px; margin-top: 12px; padding-top: 10px; font-weight: 600; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background-color: #37474f; color: #ffffff; border: 1px solid #78909c; border-radius: 5px; padding: 4px; selection-background-color: #00897b; }
        QPushButton { background-color: #455a64; color: #ffffff; border: 1px solid #78909c; border-radius: 6px; padding: 6px 10px; }
        QPushButton:hover { background-color: #546e7a; }
        QPushButton:disabled { color: #90a4ae; background-color: #314047; border-color: #546e7a; }
        QTabBar::tab { background-color: #37474f; color: #eceff1; padding: 8px 14px; border: 1px solid #607d8b; border-bottom: none; }
        QTabBar::tab:selected { background-color: #455a64; }
        QCheckBox { spacing: 6px; }
    """,
    "Neon Purple": """
        QWidget { background-color: #170b25; color: #fff36b; }
        QMainWindow, QTabWidget::pane, QScrollArea { background-color: #170b25; }
        QGroupBox { border: 1px solid #6d35a8; border-radius: 9px; margin-top: 12px; padding-top: 10px; font-weight: 600; color: #fff36b; background-color: #1c0e2e; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #fff36b; background-color: #170b25; }
        QLabel { color: #fff36b; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background-color: #331653; color: #fff36b; border: 1px solid #6f3ca0; border-radius: 6px; padding: 4px; selection-background-color: #bb22ff; selection-color: #ffffff; }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #ff3bd4; }
        QPushButton { background-color: #35165a; color: #fff36b; border: 1px solid #6f3ca0; border-radius: 8px; padding: 6px 10px; }
        QPushButton:hover { background-color: #4b2180; border-color: #ff3bd4; color: #ffffff; }
        QPushButton:pressed { background-color: #21c064; color: #101010; border-color: #27f075; }
        QPushButton:disabled { color: #8e80a8; background-color: #241337; border-color: #4a2d65; }
        QTabBar::tab { background-color: #2a0f45; color: #f4e6ff; padding: 8px 14px; border: 1px solid #5d2d89; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
        QTabBar::tab:selected { background-color: #441b72; color: #fff36b; border-color: #17d85f; }
        QTabBar::tab:hover { background-color: #572192; }
        QCheckBox { spacing: 6px; color: #fff36b; }
        QCheckBox::indicator { width: 15px; height: 15px; }
        QScrollBar:vertical { background: #241337; width: 14px; margin: 0px; }
        QScrollBar::handle:vertical { background: #6d35a8; min-height: 24px; border-radius: 6px; }
        QScrollBar::handle:vertical:hover { background: #9d45e8; }
        QScrollBar:horizontal { background: #241337; height: 14px; margin: 0px; }
        QScrollBar::handle:horizontal { background: #6d35a8; min-width: 24px; border-radius: 6px; }
        QScrollBar::handle:horizontal:hover { background: #9d45e8; }
    """,
    "Light": """
        QWidget { background-color: #f5f5f5; color: #202020; }
        QMainWindow, QTabWidget::pane, QScrollArea { background-color: #f5f5f5; }
        QGroupBox { border: 1px solid #b8b8b8; border-radius: 7px; margin-top: 12px; padding-top: 10px; font-weight: 600; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background-color: #ffffff; color: #202020; border: 1px solid #b0b0b0; border-radius: 5px; padding: 4px; selection-background-color: #9ec5fe; }
        QPushButton { background-color: #e9ecef; color: #202020; border: 1px solid #b0b0b0; border-radius: 6px; padding: 6px 10px; }
        QPushButton:hover { background-color: #dee2e6; }
        QPushButton:disabled { color: #999; background-color: #eeeeee; border-color: #cccccc; }
        QTabBar::tab { background-color: #e9ecef; color: #202020; padding: 8px 14px; border: 1px solid #b8b8b8; border-bottom: none; }
        QTabBar::tab:selected { background-color: #ffffff; }
        QCheckBox { spacing: 6px; }
    """,
}


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def env_python(root: Path) -> Path:
    env = root / "environments" / ".lens_turbo_u4"
    p1 = env / "python.exe"
    p2 = env / "Scripts" / "python.exe"
    return p1 if p1.exists() else p2


def configure_runtime_env(root: Path, offline: bool = False) -> Path:
    base = root / "models" / "lens"
    dirs = {
        "hf_home": base / "hf_home",
        "hf_hub_cache": base / "hf_cache",
        "transformers_cache": base / "transformers_cache",
        "hf_modules_cache": base / "hf_modules",
        "triton_cache": base / "triton_cache",
        "kernels_cache": base / "kernels_cache",
        "torch_home": base / "torch_home",
        "xdg_cache_home": base / "xdg_cache",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(dirs["hf_home"])
    os.environ["HF_HUB_CACHE"] = str(dirs["hf_hub_cache"])
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(dirs["hf_hub_cache"])
    os.environ["TRANSFORMERS_CACHE"] = str(dirs["transformers_cache"])
    os.environ["HF_MODULES_CACHE"] = str(dirs["hf_modules_cache"])
    os.environ["TRITON_CACHE_DIR"] = str(dirs["triton_cache"])
    os.environ["KERNELS_CACHE"] = str(dirs["kernels_cache"])
    os.environ["TORCH_HOME"] = str(dirs["torch_home"])
    os.environ["XDG_CACHE_HOME"] = str(dirs["xdg_cache_home"])
    if offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    else:
        os.environ.pop("HF_HUB_OFFLINE", None)
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
    return dirs["hf_hub_cache"]


KERNEL_REPO_ID = "kernels-community/gpt-oss-triton-kernels"


def _is_hf_offline() -> bool:
    return os.environ.get("HF_HUB_OFFLINE", "").upper() in {"1", "ON", "YES", "TRUE"}


def _find_local_lens_kernel(root: Path) -> Path | None:
    cache_root = root / "models" / "lens" / "kernels_cache"
    repo_cache = cache_root / "models--kernels-community--gpt-oss-triton-kernels"

    candidates: list[Path] = []
    snapshots = repo_cache / "snapshots"
    if snapshots.exists():
        candidates.extend(sorted(snapshots.glob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True))

    if cache_root.exists():
        candidates.extend(
            sorted(
                {p.parent for p in cache_root.rglob("metadata.json") if "gpt-oss-triton-kernels" in str(p)},
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True,
            )
        )

    for candidate in candidates:
        try:
            if (candidate / "build").exists() or (candidate / "metadata.json").exists():
                return candidate
        except OSError:
            continue
    return None


def patch_transformers_kernel_trust(root: Path | None = None) -> None:
    try:
        import importlib

        hub_kernels = importlib.import_module("transformers.integrations.hub_kernels")
        original = getattr(hub_kernels, "get_kernel_hub", None)
        if original is None or getattr(original, "_lens_offline_kernel_patch", False):
            return

        def trusted_get_kernel_hub(kernel_name, *args, **kwargs):
            if kernel_name == KERNEL_REPO_ID:
                kwargs["trust_remote_code"] = True
                if root is not None and _is_hf_offline():
                    local_kernel = _find_local_lens_kernel(root)
                    if local_kernel is not None:
                        from kernels import get_local_kernel
                        print(f"Lens offline kernel local load: {local_kernel}")
                        return get_local_kernel(local_kernel)
                    raise FileNotFoundError(
                        "Lens offline kernel cache is missing for "
                        f"{KERNEL_REPO_ID}. Turn Offline off once and run the installer/generation online "
                        "so models/lens/kernels_cache can be prepared, then offline mode will work after restart."
                    )
            try:
                return original(kernel_name, *args, **kwargs)
            except TypeError as exc:
                if "trust_remote_code" in str(exc) and "trust_remote_code" in kwargs:
                    kwargs.pop("trust_remote_code", None)
                    return original(kernel_name, *args, **kwargs)
                raise

        trusted_get_kernel_hub._lens_offline_kernel_patch = True
        hub_kernels.get_kernel_hub = trusted_get_kernel_hub

        mxfp4 = sys.modules.get("transformers.integrations.mxfp4")
        if mxfp4 is not None and hasattr(mxfp4, "get_kernel"):
            mxfp4.get_kernel = trusted_get_kernel_hub

        print("Lens offline kernel patch active for kernels-community/gpt-oss-triton-kernels")
    except Exception as exc:
        print("Lens offline kernel patch warning:", repr(exc))


class StreamToSignal(io.TextIOBase):
    def __init__(self, signal: Signal):
        super().__init__()
        self.signal = signal
        self._buf = ""

    def writable(self) -> bool:
        return True

    def write(self, s: str) -> int:
        if not s:
            return 0
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self.signal.emit(line)
        return len(s)

    def flush(self) -> None:
        if self._buf.strip():
            self.signal.emit(self._buf.rstrip())
        self._buf = ""


class LensGenerationWorker(QThread):
    log = Signal(str)
    image_saved = Signal(str)
    used_seed = Signal(str)
    failed = Signal(str)
    done = Signal()
    pipe_ready = Signal(object, object)  # (pipe, pipe_key) -- for main window to cache

    def __init__(self, root: Path, params: dict, pipe=None):
        super().__init__()
        self.root = root
        self.params = params
        self.pipe = pipe  # pre-loaded pipeline; None = load fresh

    def run(self) -> None:
        stream = StreamToSignal(self.log)
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            try:
                paths = self.generate_inline()
                for path in paths:
                    self.image_saved.emit(str(path))
                    print(f"IMAGE_SAVED::{path}")
                self.done.emit()
            except Exception as exc:
                print("ERROR:", exc)
                traceback.print_exc()
                self.failed.emit(str(exc))
            finally:
                stream.flush()

    def generate_inline(self) -> list[Path]:
        import torch

        prompt = self.params["prompt"]
        steps = int(self.params["steps"])
        cfg = float(self.params["cfg"])
        base_resolution = int(self.params.get("base_resolution") or 1024)
        aspect_ratio = str(self.params["aspect_ratio"])
        use_custom_resolution = bool(self.params.get("use_custom_resolution", False))
        custom_width = int(self.params.get("custom_width") or 0)
        custom_height = int(self.params.get("custom_height") or 0)
        seed = int(self.params["seed"])
        repo_id = self.params.get("repo_id") or MODEL_ID
        offload = bool(self.params.get("offload", False))
        offline = bool(self.params.get("offline", False))
        output_dir = Path(self.params.get("output_dir") or (self.root / "output" / "lens_turbo_u4"))
        negative = str(self.params.get("negative") or "").strip()
        images = int(self.params.get("images") or 1)
        max_sequence_length = int(self.params.get("max_seq_len") or 512)

        lens_repo = self.root / "models" / "lens" / "repos" / "Lens"
        model_cache = configure_runtime_env(self.root, offline=offline)
        out_dir = output_dir
        model_cache.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not (lens_repo / "lens").exists():
            raise RuntimeError(f"Lens repo not found: {lens_repo}. Run install.bat first.")
        if str(lens_repo) not in sys.path:
            sys.path.insert(0, str(lens_repo))

        print("UI inline generator: no generate.py, no test-file call.")
        print("torch", torch.__version__)
        print("torch cuda", torch.version.cuda)
        print("cuda available", torch.cuda.is_available())
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available. This test requires NVIDIA CUDA PyTorch.")
        print("gpu", torch.cuda.get_device_name(0))

        missing = []
        try:
            import triton
            print("triton", getattr(triton, "__version__", "unknown"))
        except Exception as e:
            print("ERROR: triton import failed:", repr(e))
            missing.append("triton-windows<3.7")
        try:
            import kernels
            print("kernels", getattr(kernels, "__version__", "ok"))
        except Exception as e:
            print("ERROR: kernels import failed:", repr(e))
            missing.append("kernels")
        try:
            import bitsandbytes as bnb
            print("bitsandbytes", getattr(bnb, "__version__", "unknown"))
        except Exception as e:
            print("ERROR: bitsandbytes import failed:", repr(e))
            missing.append("bitsandbytes")
        try:
            import sdnq  # noqa: F401
            print("sdnq import ok")
        except Exception as e:
            print("ERROR: sdnq import failed:", repr(e))
            missing.append("sdnq")
        if missing:
            raise RuntimeError("Missing quantization support package(s): " + ", ".join(missing) + ". Run install.bat again before testing.")

        patch_transformers_kernel_trust(self.root)
        from lens import LensGptOssEncoder, LensPipeline

        pipe_key = (repo_id, offload, offline)
        if self.pipe is not None:
            pipe = self.pipe
            print("Using cached pipeline -- skipping model load.")
        else:
            print("Loading", repo_id)
            print("portable cache", model_cache)
            print("If Transformers prints 'defaulting the model to bf16', stop the run: MXFP4/quant kernels are still not active.")
            t0 = time.time()
            text_encoder_kwargs = {
                "subfolder": "text_encoder",
                "dtype": torch.bfloat16,
                "cache_dir": str(model_cache),
                "local_files_only": offline,
                "trust_remote_code": True,
            }
            try:
                from transformers import Mxfp4Config
                try:
                    text_encoder_kwargs["quantization_config"] = Mxfp4Config(dequantize=False, trust_remote_code=True)
                except TypeError:
                    text_encoder_kwargs["quantization_config"] = Mxfp4Config(dequantize=False)
            except Exception as e:
                print("Mxfp4Config unavailable", repr(e))

            text_encoder = LensGptOssEncoder.from_pretrained(repo_id, **text_encoder_kwargs)
            pipe = LensPipeline.from_pretrained(
                repo_id,
                text_encoder=text_encoder,
                torch_dtype=torch.bfloat16,
                cache_dir=str(model_cache),
                local_files_only=offline,
                trust_remote_code=True,
            )
            if offload:
                print("Low-VRAM CPU offload enabled: modules are released after each image and repeated generations will be slower.")
                pipe.enable_model_cpu_offload()
            else:
                print("Fast mode: keeping the Lens pipeline resident on the GPU between queued jobs.")
                pipe.to("cuda")
            print(f"loaded in {time.time() - t0:.2f}s")
            self.pipe_ready.emit(pipe, pipe_key)

        self.used_seed.emit(str(seed))
        print(f"USED_SEED::{seed}")
        gen = torch.Generator("cuda").manual_seed(seed)
        print("Generating...")
        t1 = time.time()
        call_kwargs = dict(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=gen,
            max_sequence_length=max_sequence_length,
        )
        if use_custom_resolution:
            if custom_width <= 0 or custom_height <= 0:
                raise RuntimeError("Custom resolution is enabled but width/height are invalid.")
            call_kwargs["width"] = custom_width
            call_kwargs["height"] = custom_height
            print(f"Resolution mode: custom {custom_width} x {custom_height}")
        else:
            call_kwargs["base_resolution"] = base_resolution
            call_kwargs["aspect_ratio"] = aspect_ratio
            print(f"Resolution mode: base_resolution={base_resolution}, aspect_ratio={aspect_ratio}")
        if negative:
            call_kwargs["negative_prompt"] = negative
        if images != 1:
            call_kwargs["num_images_per_prompt"] = images
        result = pipe(**call_kwargs)
        print(f"generated in {time.time() - t1:.2f}s")

        saved_paths: list[Path] = []
        stamp = time.strftime("%Y%m%d_%H%M%S")
        for idx, image in enumerate(result.images, start=1):
            suffix = f"_img{idx}" if len(result.images) > 1 else ""
            path = out_dir / f"lens_turbo_u4_{stamp}_seed{seed}{suffix}.png"
            image.save(path)
            saved_paths.append(path)
            print("saved", path)
        return saved_paths


class ImageLabel(QLabel):
    def __init__(self) -> None:
        super().__init__("No image yet")
        self._pix: QPixmap | None = None
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border:1px solid #555; background:#202020; color:#ddd;")

    def set_image(self, path: str) -> None:
        self._pix = QPixmap(path)
        self._update_scaled()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled()

    def _update_scaled(self) -> None:
        if self._pix and not self._pix.isNull():
            self.setPixmap(self._pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.setPixmap(QPixmap())
            self.setText("No image yet")


def move_path_to_trash(path: Path) -> bool:
    path = Path(path)
    if not path.exists():
        return True
    if os.name == "nt":
        try:
            FO_DELETE = 3
            FOF_ALLOWUNDO = 0x0040
            FOF_NOCONFIRMATION = 0x0010
            FOF_SILENT = 0x0004

            class SHFILEOPSTRUCTW(ctypes.Structure):
                _fields_ = [
                    ("hwnd", ctypes.c_void_p),
                    ("wFunc", ctypes.c_uint),
                    ("pFrom", ctypes.c_wchar_p),
                    ("pTo", ctypes.c_wchar_p),
                    ("fFlags", ctypes.c_ushort),
                    ("fAnyOperationsAborted", ctypes.c_bool),
                    ("hNameMappings", ctypes.c_void_p),
                    ("lpszProgressTitle", ctypes.c_wchar_p),
                ]

            op = SHFILEOPSTRUCTW()
            op.wFunc = FO_DELETE
            op.pFrom = str(path) + "\0\0"
            op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
            result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
            return result == 0 and not op.fAnyOperationsAborted
        except Exception:
            pass
    try:
        from send2trash import send2trash
        send2trash(str(path))
        return True
    except Exception:
        return False


class LensTurboWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.root = root_dir()
        self.worker: LensGenerationWorker | None = None
        self.current_job: dict | None = None
        self.pending_jobs: list[dict] = []
        self._cached_pipe = None
        self._cached_pipe_key: tuple | None = None
        self.finished_jobs: list[dict] = []
        self.failed_jobs: list[dict] = []
        self.job_counter = 0
        self.settings_path = self.root / "presets" / "setsave" / "lens_turbo_u4_ui.json"
        self.pending_jobs_path = self.root / "presets" / "setsave" / "lens_turbo_u4_pending_jobs.json"
        self._loading_settings = False
        self.setWindowTitle("Get Going Fast | Lens Turbo U4")
        self.resize(1360, 900)
        self.build_ui()
        self.apply_defaults()
        self.load_settings()
        self.update_resolution_label()
        self.refresh_queue_views()
        if self.pending_jobs:
            QTimer.singleShot(350, self.resume_pending_after_startup)

    def build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        brand_row = QHBoxLayout()
        brand_text = QVBoxLayout()
        self.brand_title = QLabel("GET GOING FAST  /  LENS TURBO")
        self.brand_title.setObjectName("brandTitle")
        self.brand_subtitle = QLabel("Rapid local image generation | Resident GPU pipeline by default")
        self.brand_subtitle.setObjectName("brandSubtitle")
        self.brand_link = QLabel('With the help of DJ Grizzly  |  <a href="https://www.youtube.com/@dj__grizzly">YouTube channel</a>')
        self.brand_link.setObjectName("brandLink")
        self.brand_link.setOpenExternalLinks(True)
        brand_text.addWidget(self.brand_title)
        brand_text.addWidget(self.brand_subtitle)
        brand_row.addLayout(brand_text)
        brand_row.addStretch(1)
        brand_row.addWidget(self.brand_link)
        outer.addLayout(brand_row)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        gen_tab = QWidget()
        queue_tab = QWidget()
        settings_tab = QWidget()
        self.tabs.addTab(gen_tab, "Generate")
        self.tabs.addTab(queue_tab, "Queue")
        self.tabs.addTab(settings_tab, "Settings")

        gen_layout = QHBoxLayout(gen_tab)
        left_host = QWidget()
        left_layout = QVBoxLayout(left_host)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_host)
        gen_layout.addWidget(left_scroll, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        gen_layout.addWidget(right, 1)

        prompt_group = QGroupBox("Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Describe the image you want to generate...")
        self.negative_edit = QTextEdit()
        self.negative_edit.setPlaceholderText("Optional negative prompt...")
        prompt_layout.addWidget(QLabel("Prompt"))
        prompt_layout.addWidget(self.prompt_edit)
        prompt_layout.addWidget(QLabel("Negative prompt"))
        prompt_layout.addWidget(self.negative_edit)
        left_layout.addWidget(prompt_group)

        main_group = QGroupBox("Generation")
        form = QFormLayout(main_group)
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["1:1", "16:9", "9:16"])
        self.aspect_combo.currentIndexChanged.connect(self.on_aspect_changed)

        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self.on_resolution_preset_changed)

        self.custom_resolution_widget = QWidget()
        custom_layout = QVBoxLayout(self.custom_resolution_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_row = QWidget()
        custom_row_layout = QHBoxLayout(custom_row)
        custom_row_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(256, 2560)
        self.custom_width_spin.setSingleStep(32)
        self.custom_width_spin.setSuffix(" w")
        self.custom_width_spin.valueChanged.connect(self.on_custom_resolution_changed)
        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(256, 1440)
        self.custom_height_spin.setSingleStep(32)
        self.custom_height_spin.setSuffix(" h")
        self.custom_height_spin.valueChanged.connect(self.on_custom_resolution_changed)
        self.custom_resolution_hint = QLabel("Custom size, 32-step, max 2560 x 1440")
        self.custom_resolution_warning = QLabel("Images above base resolution may produce artifacts and add cloned objects")
        self.custom_resolution_warning.setWordWrap(True)
        self.custom_resolution_warning.setVisible(False)
        custom_row_layout.addWidget(self.custom_width_spin)
        custom_row_layout.addWidget(self.custom_height_spin)
        custom_row_layout.addWidget(self.custom_resolution_hint, 1)
        custom_layout.addWidget(custom_row)
        custom_layout.addWidget(self.custom_resolution_warning)

        self.size_label = QLabel("-")
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 200)
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(0.0, 30.0)
        self.cfg_spin.setDecimals(2)
        self.cfg_spin.setSingleStep(0.25)
        self.images_spin = QSpinBox()
        self.images_spin.setRange(1, 16)
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 100)

        seed_row = QWidget()
        seed_layout = QHBoxLayout(seed_row)
        seed_layout.setContentsMargins(0, 0, 0, 0)
        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText("seed value")
        self.seed_random_btn = QPushButton("Random Seed: OFF")
        self.seed_random_btn.setCheckable(True)
        self.seed_random_btn.toggled.connect(self.on_random_seed_toggled)
        seed_layout.addWidget(self.seed_edit, 1)
        seed_layout.addWidget(self.seed_random_btn)

        form.addRow("Aspect ratio", self.aspect_combo)
        form.addRow("Resolution", self.preset_combo)
        form.addRow("Custom size", self.custom_resolution_widget)
        form.addRow("Resolved output", self.size_label)
        form.addRow("Steps", self.steps_spin)
        form.addRow("CFG", self.cfg_spin)
        form.addRow("Images per prompt", self.images_spin)
        form.addRow("Batch jobs", self.batch_spin)
        form.addRow("Seed", seed_row)
        left_layout.addWidget(main_group)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.generate_btn = QPushButton("Add to Queue")
        self.stop_btn = QPushButton("Stop Current")
        self.stop_btn.setEnabled(False)
        self.open_output_btn = QPushButton("Open Output Folder")
        self.generate_btn.clicked.connect(self.start_generation)
        self.stop_btn.clicked.connect(self.stop_generation)
        self.open_output_btn.clicked.connect(self.open_output_folder)
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.open_output_btn)
        left_layout.addWidget(buttons)
        left_layout.addStretch(1)

        self.status_label = QLabel("Idle")
        right_layout.addWidget(self.status_label)
        self.image_preview = ImageLabel()
        right_layout.addWidget(self.image_preview, 2)

        info = QWidget()
        info_form = QFormLayout(info)
        self.last_file_label = QLineEdit()
        self.last_file_label.setReadOnly(True)
        self.used_seed_label = QLineEdit()
        self.used_seed_label.setReadOnly(True)
        self.refined_prompt_label = QLineEdit()
        self.refined_prompt_label.setReadOnly(True)
        info_form.addRow("Last image", self.last_file_label)
        info_form.addRow("Used seed", self.used_seed_label)
        info_form.addRow("Refined prompt", self.refined_prompt_label)
        right_layout.addWidget(info)

        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        right_layout.addWidget(self.log_edit, 1)

        queue_layout = QVBoxLayout(queue_tab)
        self.queue_summary_label = QLabel("Queue is idle")
        queue_layout.addWidget(self.queue_summary_label)
        queue_grid = QGridLayout()
        queue_layout.addLayout(queue_grid)

        self.running_group = QGroupBox("Running (0)")
        running_layout = QVBoxLayout(self.running_group)
        self.running_list = QListWidget()
        self.running_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.running_list.customContextMenuRequested.connect(self.show_running_context_menu)
        running_layout.addWidget(self.running_list)
        queue_grid.addWidget(self.running_group, 0, 0)

        self.pending_group = QGroupBox("Pending (0)")
        pending_layout = QVBoxLayout(self.pending_group)
        self.pending_list = QListWidget()
        self.pending_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pending_list.customContextMenuRequested.connect(self.show_pending_context_menu)
        pending_layout.addWidget(self.pending_list)
        queue_grid.addWidget(self.pending_group, 0, 1)

        self.finished_group = QGroupBox("Finished (0)")
        finished_layout = QVBoxLayout(self.finished_group)
        self.finished_list = QListWidget()
        self.finished_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.finished_list.customContextMenuRequested.connect(self.show_finished_context_menu)
        finished_layout.addWidget(self.finished_list)
        queue_grid.addWidget(self.finished_group, 1, 0)

        self.failed_group = QGroupBox("Failed (0)")
        failed_layout = QVBoxLayout(self.failed_group)
        self.failed_list = QListWidget()
        failed_layout.addWidget(self.failed_list)
        queue_grid.addWidget(self.failed_group, 1, 1)

        queue_note = QLabel("Pending jobs are saved to presets/setsave and restored after restart. Running/failed jobs are session-only. The last 10 finished jobs are saved and restored.")
        queue_note.setWordWrap(True)
        queue_layout.addWidget(queue_note)

        settings_layout = QVBoxLayout(settings_tab)
        settings_inner = QWidget()
        sform = QFormLayout(settings_inner)
        self.model_edit = QLineEdit(MODEL_ID)
        self.output_edit = QLineEdit(str(self.root / "output" / "lens_turbo_u4"))
        self.output_browse_btn = QPushButton("Browse")
        self.output_browse_btn.clicked.connect(self.browse_output_dir)
        out_row = QWidget()
        out_layout = QHBoxLayout(out_row)
        out_layout.setContentsMargins(0, 0, 0, 0)
        out_layout.addWidget(self.output_edit, 1)
        out_layout.addWidget(self.output_browse_btn)

        self.repo_path_edit = QLineEdit(str(self.root / "models" / "lens" / "repos" / "Lens"))
        self.dtype_combo = QComboBox()
        self.dtype_combo.addItems(["bfloat16"])
        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.max_seq_spin = QSpinBox()
        self.max_seq_spin.setRange(64, 4096)
        self.offload_chk = QCheckBox("Low-VRAM CPU offload (slower; releases modules after each image)")
        self.offline_chk = QCheckBox("Offline / portable cache only")
        self.disable_mxfp4_chk = QCheckBox("Disable MXFP4 (disabled in UI inline mode)")
        self.disable_mxfp4_chk.setEnabled(False)
        self.reasoner_chk = QCheckBox("Enable reasoner (not used yet)")
        self.reasoner_chk.setEnabled(False)
        self.api_url_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.api_model_edit = QLineEdit()
        self.python_label = QLabel(str(env_python(self.root)))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.info_btn = QPushButton("Info")
        self.info_btn.clicked.connect(self.show_info_popup)

        sform.addRow("Model repo/id", self.model_edit)
        sform.addRow("Output folder", out_row)
        sform.addRow("Lens repo path", self.repo_path_edit)
        sform.addRow("Python env", self.python_label)
        sform.addRow("Theme", self.theme_combo)
        sform.addRow("Dtype", self.dtype_combo)
        sform.addRow("HF token (optional)", self.hf_token_edit)
        sform.addRow("Max sequence length", self.max_seq_spin)
        sform.addRow("Advanced", self.offload_chk)
        sform.addRow("", self.offline_chk)
        sform.addRow("", self.disable_mxfp4_chk)
        sform.addRow("", self.reasoner_chk)
        sform.addRow("API URL", self.api_url_edit)
        sform.addRow("API Key", self.api_key_edit)
        sform.addRow("API Model", self.api_model_edit)
        settings_layout.addWidget(settings_inner)
        settings_button_row = QWidget()
        settings_button_layout = QHBoxLayout(settings_button_row)
        settings_button_layout.setContentsMargins(0, 0, 0, 0)
        settings_button_layout.addWidget(self.save_btn)
        settings_button_layout.addWidget(self.info_btn)
        settings_button_layout.addStretch(1)
        settings_layout.addWidget(settings_button_row)
        settings_layout.addStretch(1)
        self.apply_tooltips()

    def apply_tooltips(self) -> None:
        tips = {
            self.tabs: "Generate images, inspect the queue, and change app settings.",
            self.prompt_edit: "Main image prompt. Describe the subject, scene, lighting, style, and composition. Clear prompts work best.",
            self.negative_edit: "Optional negative prompt. Use only when needed to avoid unwanted details. Default: empty.",
            self.aspect_combo: "Image shape. Default: 16:9. Changing this updates the base-resolution presets and custom defaults.",
            self.preset_combo: "Resolution mode. Default: 1024 (base res). Use 1440 (base res) for the largest native Lens bucket. Custom is experimental.",
            self.custom_resolution_widget: "Custom resolution controls. Values snap to 32-step increments. Max: 2560 x 1440.",
            self.custom_width_spin: "Custom output width. Snaps to the nearest 32. Max: 2560. Custom sizes above the native base bucket may create artifacts or cloned objects.",
            self.custom_height_spin: "Custom output height. Snaps to the nearest 32. Max: 1440. Custom sizes above the native base bucket may create artifacts or cloned objects.",
            self.custom_resolution_hint: "Custom size is experimental. Recommended: stay near or below the selected aspect ratio's 1440 base output.",
            self.custom_resolution_warning: "Warning: above the highest Lens base-resolution bucket, images can show artifacts, doubled details, or cloned objects.",
            self.size_label: "Actual size sent to Lens. Base presets use Lens-supported buckets; Custom sends width and height directly.",
            self.steps_spin: "Inference steps. Default: 4. More steps may improve detail but are slower.",
            self.cfg_spin: "Guidance / CFG. Default: 1.0 for this Lens Turbo setup. Higher values may over-force the prompt or reduce quality.",
            self.images_spin: "Images per queued job. Default: 1. Creates multiple images from the same prompt/job.",
            self.batch_spin: "Number of jobs to add to the queue at once. Default: 1. With Random Seed ON, each job gets a fresh seed.",
            self.seed_edit: "Manual seed for repeatable results. Leave Random Seed ON to generate a new seed for every queued job.",
            self.seed_random_btn: "Toggle automatic seed changes. Default: OFF. When ON, every queued job gets a fresh random seed.",
            self.generate_btn: "Add the current prompt/settings to the queue. The app keeps working while jobs run one by one.",
            self.stop_btn: "Cancel the currently running job. Use this if a generation is stuck or you picked the wrong settings.",
            self.open_output_btn: "Open the folder where Lens images are saved.",
            self.status_label: "Current app/job status.",
            self.image_preview: "Preview of the latest generated image.",
            self.last_file_label: "Path to the most recently saved output image.",
            self.used_seed_label: "Seed used by the latest/current job. Copy this to reproduce a result with Random Seed OFF.",
            self.refined_prompt_label: "Reserved for future prompt-refinement output. Currently usually empty.",
            self.log_edit: "Live generation log and error details. Useful when testing offline/cache/kernel problems.",
            self.queue_summary_label: "Quick queue status summary: running, pending, finished, and failed counts.",
            self.running_group: "Currently running job. Right-click a job to cancel it.",
            self.running_list: "Running job list. Right-click: Cancel job.",
            self.pending_group: "Jobs waiting to run. Pending jobs are saved to presets/setsave/lens_turbo_u4_pending_jobs.json and restored after restart.",
            self.pending_list: "Pending job list. Right-click: Cancel job. Pending jobs resume after restart.",
            self.finished_group: "Finished jobs. The last 10 are saved after restart.",
            self.finished_list: "Finished job list. Right-click: Open, Open folder, or Delete from disk/trash.",
            self.failed_group: "Failed or cancelled jobs for this session.",
            self.failed_list: "Failed/cancelled jobs. These are session-only and are not restored after restart.",
            self.model_edit: "Hugging Face model id. Default: WaveCut/Lens-Turbo-SDNQ-uint4-static.",
            self.output_edit: "Output folder for generated images. Default: output/lens_turbo_u4 under the app root.",
            self.output_browse_btn: "Choose a different output folder.",
            self.repo_path_edit: "Local Lens repo path. Normally keep this at models/lens/repos/Lens.",
            self.python_label: "Python environment used to run Lens.",
            self.theme_combo: "UI theme. Default: Get Going Fast, using the Get Going Fast surface and green accent palette.",
            self.dtype_combo: "Model dtype. Default: bfloat16. Keep this unless the backend changes.",
            self.hf_token_edit: "Optional Hugging Face token. Usually not needed for public cached models.",
            self.max_seq_spin: "Maximum text sequence length. Default: 512. Higher values allow longer prompts but may use more memory.",
            self.offload_chk: "Low-VRAM fallback only. It offloads Lens modules after each image and transfers them again on the next run, so leave it OFF for rapid generation when your GPU has enough VRAM.",
            self.offline_chk: "Offline / portable cache mode. Default: OFF. Turn ON after the model and kernel cache are prepared.",
            self.disable_mxfp4_chk: "Disabled placeholder. MXFP4 is required for the fast quantized Lens path.",
            self.reasoner_chk: "Disabled placeholder for a future prompt-reasoner feature.",
            self.api_url_edit: "Optional future external API URL. Not required for normal local Lens generation.",
            self.api_key_edit: "Optional future API key. Not required for normal local Lens generation.",
            self.api_model_edit: "Optional future API model name. Not required for normal local Lens generation.",
            self.save_btn: "Save UI/settings JSON to presets/setsave/lens_turbo_u4_ui.json.",
            self.info_btn: "Open credits and links. Clicking links needs an internet connection and opens your web browser.",
        }
        for widget, tip in tips.items():
            try:
                widget.setToolTip(tip)
                widget.setStatusTip(tip)
            except Exception:
                pass

    def show_info_popup(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Info")
        dialog.resize(620, 420)
        layout = QVBoxLayout(dialog)

        browser = QTextBrowser(dialog)
        browser.setOpenExternalLinks(True)
        browser.setHtml("""
        <div style="font-size: 15px; line-height: 1.45;">
            <h2>Get Going Fast | Lens Turbo</h2>
            <p>Built for rapid local generation with help from <b>DJ Grizzly</b>.<br>
            <a href="https://github.com/Koongrizzly">https://github.com/Koongrizzly</a> /
            <a href="https://www.youtube.com/@dj__grizzly">https://www.youtube.com/@dj__grizzly</a></p>
            <p><b>The A.i. Hobby Guy</b><br>
            <a href="https://discord.gg/3freTyckU">https://discord.gg/3freTyckU</a> /
            <a href="https://www.youtube.com/@TheAIHobbyGuy">https://www.youtube.com/@TheAIHobbyGuy</a></p>
            <p><i>Clicking a link needs internet connection and will open a web browser</i></p>
        </div>
        """)
        layout.addWidget(browser, 1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close_btn)
        layout.addLayout(row)
        dialog.exec()

    def apply_defaults(self) -> None:
        self._loading_settings = True
        self.aspect_combo.setCurrentText(DEFAULT_ASPECT_RATIO)
        self.set_default_custom_dimensions_for_aspect(DEFAULT_ASPECT_RATIO)
        self.rebuild_resolution_presets(DEFAULT_RESOLUTION_PRESET)
        self.steps_spin.setValue(4)
        self.cfg_spin.setValue(1.0)
        self.images_spin.setValue(1)
        self.batch_spin.setValue(1)
        self.seed_edit.clear()
        self.seed_random_btn.setChecked(False)
        self.seed_random_btn.setText("Random Seed: OFF")
        self.dtype_combo.setCurrentText("bfloat16")
        self.offload_chk.setChecked(False)
        self.offline_chk.setChecked(False)
        self.disable_mxfp4_chk.setChecked(False)
        self.reasoner_chk.setChecked(False)
        self.max_seq_spin.setValue(512)
        self.output_edit.setText(str(self.root / "output" / "lens_turbo_u4"))
        if hasattr(self, "theme_combo"):
            self.theme_combo.setCurrentText(DEFAULT_THEME)
            self.apply_theme(DEFAULT_THEME)
        self._loading_settings = False

    def serialize_finished_jobs(self) -> list[dict]:
        items = []
        for job in self.finished_jobs[:MAX_SAVED_FINISHED]:
            items.append({
                "job_id": job.get("job_id"),
                "prompt": job.get("prompt", ""),
                "seed": job.get("seed"),
                "created_at": job.get("created_at", ""),
                "completed_at": job.get("completed_at", ""),
                "image_paths": list(job.get("image_paths", [])),
                "images_requested": int(job.get("params", {}).get("images", job.get("images_requested", 1)) or 1),
            })
        return items

    def serialize_pending_jobs(self) -> list[dict]:
        items: list[dict] = []
        for job in self.pending_jobs:
            params = dict(job.get("params") or {})
            items.append({
                "job_id": int(job.get("job_id") or 0),
                "status": "Pending",
                "prompt": str(job.get("prompt", "")),
                "seed": job.get("seed"),
                "created_at": str(job.get("created_at", "")),
                "image_paths": [],
                "params": params,
                "error": "",
            })
        return items

    def save_pending_jobs(self) -> None:
        try:
            self.pending_jobs_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "pending_jobs": self.serialize_pending_jobs(),
            }
            self.pending_jobs_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            self.append_log(f"Could not save pending queue JSON: {e}")

    def load_pending_jobs(self) -> None:
        self.pending_jobs = []
        if not self.pending_jobs_path.exists():
            return
        try:
            data = json.loads(self.pending_jobs_path.read_text(encoding="utf-8"))
            raw_jobs = data.get("pending_jobs") if isinstance(data, dict) else data
            for item in list(raw_jobs or []):
                params = dict(item.get("params") or {})
                prompt = str(item.get("prompt") or params.get("prompt") or "").strip()
                if not prompt:
                    continue
                job_id = int(item.get("job_id") or 0)
                seed = item.get("seed", params.get("seed"))
                if seed is None:
                    seed = random.randint(0, 2**31 - 1)
                params["prompt"] = prompt
                params["seed"] = int(seed)
                job = {
                    "job_id": job_id,
                    "status": "Pending",
                    "prompt": prompt,
                    "seed": int(seed),
                    "created_at": str(item.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S")),
                    "completed_at": "",
                    "image_paths": [],
                    "params": params,
                    "error": "",
                }
                self.pending_jobs.append(job)
            if self.pending_jobs:
                self.status_label.setText(f"Restored {len(self.pending_jobs)} pending job(s)")
        except Exception as e:
            QMessageBox.warning(self, "Queue", f"Could not load pending queue JSON:\n{e}")

    def settings_dict(self) -> dict:
        return {
            "prompt": self.prompt_edit.toPlainText(),
            "negative": self.negative_edit.toPlainText(),
            "resolution_preset": self.current_resolution_label(),
            "aspect_ratio": self.aspect_combo.currentText(),
            "base_resolution": self.current_base_resolution(),
            "use_custom_resolution": self.is_custom_resolution(),
            "custom_width": self.custom_width_spin.value(),
            "custom_height": self.custom_height_spin.value(),
            "steps": self.steps_spin.value(),
            "cfg": self.cfg_spin.value(),
            "images": self.images_spin.value(),
            "batch_jobs": self.batch_spin.value(),
            "seed": self.seed_edit.text(),
            "random_seed_enabled": self.seed_random_btn.isChecked(),
            "model_repo": self.model_edit.text(),
            "output_dir": self.output_edit.text(),
            "lens_repo_path": self.repo_path_edit.text(),
            "dtype": self.dtype_combo.currentText(),
            "offload": self.offload_chk.isChecked(),
            "offline": self.offline_chk.isChecked(),
            "disable_mxfp4": False,
            "reasoner": False,
            "max_seq_len": self.max_seq_spin.value(),
            "hf_token": self.hf_token_edit.text(),
            "api_url": self.api_url_edit.text(),
            "api_key": self.api_key_edit.text(),
            "api_model": self.api_model_edit.text(),
            "theme": self.theme_combo.currentText(),
            "finished_jobs": self.serialize_finished_jobs(),
        }

    def load_settings(self) -> None:
        self._loading_settings = True
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8")) if self.settings_path.exists() else {}
            self.prompt_edit.setPlainText(data.get("prompt", ""))
            self.negative_edit.setPlainText(data.get("negative", ""))
            aspect = str(data.get("aspect_ratio") or DEFAULT_ASPECT_RATIO)
            if aspect not in RESOLUTION_PRESETS:
                aspect = DEFAULT_ASPECT_RATIO
            self.aspect_combo.setCurrentText(aspect)
            self.set_default_custom_dimensions_for_aspect(aspect)
            if data.get("custom_width"):
                self.custom_width_spin.setValue(self.normalize_custom_width(int(data.get("custom_width"))))
            if data.get("custom_height"):
                self.custom_height_spin.setValue(self.normalize_custom_height(int(data.get("custom_height"))))
            preset_label = str(data.get("resolution_preset") or "")
            if bool(data.get("use_custom_resolution", False)):
                preset_label = CUSTOM_RESOLUTION_LABEL
            if not preset_label and data.get("base_resolution"):
                preset_label = self.closest_resolution_label(aspect, int(data.get("base_resolution")))
            if not preset_label and isinstance(data.get("preset_index"), int):
                old_index_map = {1: "1024 (base res)", 2: "1440 (base res)", 3: "1024 (base res)", 4: "1440 (base res)", 5: "1024 (base res)", 6: "1440 (base res)"}
                preset_label = old_index_map.get(int(data.get("preset_index")), DEFAULT_RESOLUTION_PRESET)
            self.rebuild_resolution_presets(preset_label or DEFAULT_RESOLUTION_PRESET)
            if data.get("steps"):
                self.steps_spin.setValue(int(data["steps"]))
            if data.get("cfg") is not None:
                self.cfg_spin.setValue(float(data["cfg"]))
            if data.get("images"):
                self.images_spin.setValue(int(data["images"]))
            if data.get("batch_jobs"):
                self.batch_spin.setValue(int(data["batch_jobs"]))
            if data.get("seed") is not None:
                self.seed_edit.setText(str(data["seed"]))
            self.seed_random_btn.setChecked(bool(data.get("random_seed_enabled", False)))
            self.on_random_seed_toggled(self.seed_random_btn.isChecked())
            self.model_edit.setText(str(data.get("model_repo") or MODEL_ID))
            self.output_edit.setText(str(data.get("output_dir") or (self.root / "output" / "lens_turbo_u4")))
            self.repo_path_edit.setText(str(data.get("lens_repo_path") or (self.root / "models" / "lens" / "repos" / "Lens")))
            self.hf_token_edit.setText(str(data.get("hf_token", "")))
            self.api_url_edit.setText(str(data.get("api_url", "")))
            self.api_key_edit.setText(str(data.get("api_key", "")))
            self.api_model_edit.setText(str(data.get("api_model", "")))
            self.offload_chk.setChecked(bool(data.get("offload", self.offload_chk.isChecked())))
            self.offline_chk.setChecked(bool(data.get("offline", self.offline_chk.isChecked())))
            theme = str(data.get("theme") or DEFAULT_THEME)
            if theme not in THEMES:
                theme = DEFAULT_THEME
            self.theme_combo.setCurrentText(theme)
            self.apply_theme(theme)

            self.finished_jobs = []
            for item in list(data.get("finished_jobs") or [])[:MAX_SAVED_FINISHED]:
                self.finished_jobs.append({
                    "job_id": int(item.get("job_id") or 0),
                    "status": "Finished",
                    "prompt": str(item.get("prompt", "")),
                    "seed": item.get("seed"),
                    "created_at": str(item.get("created_at", "")),
                    "completed_at": str(item.get("completed_at", "")),
                    "image_paths": list(item.get("image_paths", [])),
                    "images_requested": int(item.get("images_requested") or 1),
                    "params": {"images": int(item.get("images_requested") or 1)},
                    "error": "",
                })
            if self.finished_jobs:
                self.job_counter = max(int(job.get("job_id") or 0) for job in self.finished_jobs)
            self.load_pending_jobs()
            all_ids = [int(job.get("job_id") or 0) for job in (self.finished_jobs + self.pending_jobs + self.failed_jobs)]
            if all_ids:
                self.job_counter = max(self.job_counter, max(all_ids))
        except Exception as e:
            QMessageBox.warning(self, "Settings", f"Could not load settings:\n{e}")
        finally:
            self._loading_settings = False
            self.refresh_queue_views()

    def save_settings(self) -> None:
        if self._loading_settings:
            return
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(json.dumps(self.settings_dict(), indent=2), encoding="utf-8")
            self.status_label.setText(self.status_label.text() if self.worker else "Settings saved")
        except Exception as e:
            QMessageBox.warning(self, "Settings", f"Could not save settings:\n{e}")

    def closeEvent(self, event):
        self.save_settings()
        self.save_pending_jobs()
        super().closeEvent(event)

    def apply_theme(self, theme_name: str) -> None:
        theme = theme_name if theme_name in THEMES else DEFAULT_THEME
        QApplication.instance().setStyleSheet(THEMES[theme])
        if hasattr(self, "image_preview"):
            if theme == "Light":
                self.image_preview.setStyleSheet("border:1px solid #b0b0b0; background:#ffffff; color:#202020;")
            else:
                self.image_preview.setStyleSheet("border:1px solid #555; background:#202020; color:#ddd;")

    def on_theme_changed(self, theme_name: str) -> None:
        self.apply_theme(theme_name)
        if not self._loading_settings:
            self.save_settings()

    def browse_output_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Select output folder", self.output_edit.text() or str(self.root / "output"))
        if chosen:
            self.output_edit.setText(chosen)

    def open_output_folder(self) -> None:
        path = self.output_edit.text().strip() or str(self.root / "output" / "lens_turbo_u4")
        Path(path).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def current_resolution_entry(self) -> tuple[str, str, int, int, int]:
        data = self.preset_combo.currentData()
        if isinstance(data, tuple) and len(data) == 5:
            return data
        ratio = self.aspect_combo.currentText()
        return RESOLUTION_PRESETS.get(ratio, RESOLUTION_PRESETS[DEFAULT_ASPECT_RATIO])[0]

    def current_resolution_label(self) -> str:
        return str(self.current_resolution_entry()[0])

    def current_resolution_mode(self) -> str:
        return str(self.current_resolution_entry()[1])

    def is_custom_resolution(self) -> bool:
        return self.current_resolution_mode() == "custom"

    def current_base_resolution(self) -> int:
        base = int(self.current_resolution_entry()[2])
        return 1440 if base >= 1440 else 1024

    def normalize_to_32(self, value: int, maximum: int | None = None) -> int:
        snapped = max(256, int(round(value / 32.0) * 32))
        if maximum is not None:
            snapped = min(maximum, snapped)
        return snapped

    def normalize_custom_width(self, value: int) -> int:
        return self.normalize_to_32(value, 2560)

    def normalize_custom_height(self, value: int) -> int:
        return self.normalize_to_32(value, 1440)

    def set_default_custom_dimensions_for_aspect(self, aspect: str) -> None:
        defaults = {
            "1:1": (1024, 1024),
            "16:9": (1280, 704),
            "9:16": (704, 1280),
        }
        width, height = defaults.get(aspect, defaults[DEFAULT_ASPECT_RATIO])
        self.custom_width_spin.blockSignals(True)
        self.custom_height_spin.blockSignals(True)
        self.custom_width_spin.setValue(width)
        self.custom_height_spin.setValue(height)
        self.custom_width_spin.blockSignals(False)
        self.custom_height_spin.blockSignals(False)

    def closest_resolution_label(self, aspect: str, base_resolution: int) -> str:
        presets = [item for item in RESOLUTION_PRESETS.get(aspect, RESOLUTION_PRESETS[DEFAULT_ASPECT_RATIO]) if item[1] == "base"]
        return min(presets, key=lambda item: abs(int(item[2]) - int(base_resolution)))[0]

    def highest_base_resolution_output(self, aspect: str) -> tuple[int, int]:
        presets = [item for item in RESOLUTION_PRESETS.get(aspect, RESOLUTION_PRESETS[DEFAULT_ASPECT_RATIO]) if item[1] == "base"]
        if not presets:
            return (0, 0)
        highest = max(presets, key=lambda item: int(item[2]))
        return int(highest[3]), int(highest[4])

    def custom_exceeds_highest_base_resolution(self) -> bool:
        aspect = self.aspect_combo.currentText()
        max_width, max_height = self.highest_base_resolution_output(aspect)
        width = self.normalize_custom_width(self.custom_width_spin.value())
        height = self.normalize_custom_height(self.custom_height_spin.value())
        return width > max_width or height > max_height

    def rebuild_resolution_presets(self, preferred_label: str | None = None) -> None:
        ratio = self.aspect_combo.currentText()
        presets = RESOLUTION_PRESETS.get(ratio, RESOLUTION_PRESETS[DEFAULT_ASPECT_RATIO])
        preferred_label = preferred_label or (self.current_resolution_label() if self.preset_combo.count() else DEFAULT_RESOLUTION_PRESET)
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        selected_index = 0
        for idx, entry in enumerate(presets):
            label, _mode, _base, _w, _h = entry
            self.preset_combo.addItem(label, entry)
            if label == preferred_label:
                selected_index = idx
        self.preset_combo.setCurrentIndex(selected_index)
        self.preset_combo.blockSignals(False)
        self.update_resolution_label()

    def on_aspect_changed(self, *_args) -> None:
        previous_label = self.current_resolution_label() if self.preset_combo.count() else DEFAULT_RESOLUTION_PRESET
        self.set_default_custom_dimensions_for_aspect(self.aspect_combo.currentText())
        self.rebuild_resolution_presets(previous_label if previous_label in {"1024 (base res)", "1440 (base res)", CUSTOM_RESOLUTION_LABEL} else DEFAULT_RESOLUTION_PRESET)
        if not self._loading_settings:
            self.save_settings()

    def on_resolution_preset_changed(self, *_args) -> None:
        self.update_resolution_label()
        if not self._loading_settings:
            self.save_settings()

    def on_custom_resolution_changed(self, *_args) -> None:
        self.custom_width_spin.blockSignals(True)
        self.custom_height_spin.blockSignals(True)
        self.custom_width_spin.setValue(self.normalize_custom_width(self.custom_width_spin.value()))
        self.custom_height_spin.setValue(self.normalize_custom_height(self.custom_height_spin.value()))
        self.custom_width_spin.blockSignals(False)
        self.custom_height_spin.blockSignals(False)
        self.update_resolution_label()
        if not self._loading_settings:
            self.save_settings()

    def update_resolution_label(self, *_args) -> None:
        try:
            label, mode, base, width, height = self.current_resolution_entry()
            is_custom = mode == "custom"
            self.custom_resolution_widget.setVisible(is_custom)
            if is_custom:
                width = self.normalize_custom_width(self.custom_width_spin.value())
                height = self.normalize_custom_height(self.custom_height_spin.value())
                self.custom_resolution_warning.setVisible(self.custom_exceeds_highest_base_resolution())
                self.size_label.setText(f"{width} x {height}  |  Custom")
            else:
                self.custom_resolution_warning.setVisible(False)
                self.size_label.setText(f"{width} x {height}  |  Lens base {base}")
        except Exception:
            self.custom_resolution_widget.setVisible(False)
            if hasattr(self, "custom_resolution_warning"):
                self.custom_resolution_warning.setVisible(False)
            self.size_label.setText("-")
    def set_random_seed(self) -> None:
        self.seed_edit.setText(str(random.randint(0, 2**31 - 1)))

    def on_random_seed_toggled(self, checked: bool) -> None:
        self.seed_random_btn.setText("Random Seed: ON" if checked else "Random Seed: OFF")
        self.seed_edit.setEnabled(not checked)
        if checked:
            self.set_random_seed()
        if not self._loading_settings:
            self.save_settings()

    def append_log(self, text: str) -> None:
        self.log_edit.appendPlainText(text.rstrip())
        sb = self.log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def make_job_text(self, job: dict) -> str:
        prompt = " ".join(str(job.get("prompt", "")).split())
        if len(prompt) > 70:
            prompt = prompt[:67] + "..."
        seed = job.get("seed", "?")
        images = int(job.get("params", {}).get("images", job.get("images_requested", 1)) or 1)
        created = job.get("created_at") or ""
        completed = job.get("completed_at") or ""
        prefix = f"#{int(job.get('job_id', 0)):03d}"
        status = job.get("status", "")
        if status == "Finished":
            return f"{prefix} | seed {seed} | {images} img | done {completed or created} | {prompt}"
        if status == "Failed":
            error = str(job.get("error", ""))
            if len(error) > 50:
                error = error[:47] + "..."
            return f"{prefix} | seed {seed} | failed | {prompt} | {error}"
        if status == "Running":
            return f"{prefix} | seed {seed} | running | {prompt}"
        return f"{prefix} | seed {seed} | pending | {prompt}"

    def job_from_item(self, list_widget: QListWidget, pos) -> dict | None:
        item = list_widget.itemAt(pos)
        if item is None:
            item = list_widget.currentItem()
        if item is None:
            return None
        try:
            job_id = int(item.data(Qt.UserRole) or 0)
        except Exception:
            job_id = 0
        return self.find_job_by_id(job_id)

    def find_job_by_id(self, job_id: int) -> dict | None:
        if self.current_job and int(self.current_job.get("job_id") or 0) == int(job_id):
            return self.current_job
        for collection in (self.pending_jobs, self.finished_jobs, self.failed_jobs):
            for job in collection:
                if int(job.get("job_id") or 0) == int(job_id):
                    return job
        return None

    def show_running_context_menu(self, pos) -> None:
        job = self.job_from_item(self.running_list, pos)
        if not job:
            return
        menu = QMenu(self)
        cancel_action = menu.addAction("Cancel job")
        chosen = menu.exec(self.running_list.mapToGlobal(pos))
        if chosen == cancel_action:
            self.cancel_running_job()

    def show_pending_context_menu(self, pos) -> None:
        job = self.job_from_item(self.pending_list, pos)
        if not job:
            return
        menu = QMenu(self)
        cancel_action = menu.addAction("Cancel job")
        chosen = menu.exec(self.pending_list.mapToGlobal(pos))
        if chosen == cancel_action:
            self.cancel_pending_job(job)

    def show_finished_context_menu(self, pos) -> None:
        job = self.job_from_item(self.finished_list, pos)
        if not job:
            return
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        open_folder_action = menu.addAction("Open folder")
        menu.addSeparator()
        delete_action = menu.addAction("Delete from disk")
        chosen = menu.exec(self.finished_list.mapToGlobal(pos))
        if chosen == open_action:
            self.open_finished_job(job)
        elif chosen == open_folder_action:
            self.open_finished_job_folder(job)
        elif chosen == delete_action:
            self.delete_finished_job_from_disk(job)

    def first_existing_job_path(self, job: dict) -> Path | None:
        for raw in list(job.get("image_paths") or []):
            path = Path(str(raw))
            if path.exists():
                return path
        return None

    def open_finished_job(self, job: dict) -> None:
        path = self.first_existing_job_path(job)
        if not path:
            QMessageBox.information(self, "Open", "No existing output file was found for this job.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_finished_job_folder(self, job: dict) -> None:
        path = self.first_existing_job_path(job)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
            return
        raw_paths = list(job.get("image_paths") or [])
        if raw_paths:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(str(raw_paths[0])).parent)))
            return
        output_dir = self.output_edit.text().strip() or str(self.root / "output" / "lens_turbo_u4")
        QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))

    def delete_finished_job_from_disk(self, job: dict) -> None:
        paths = [Path(str(p)) for p in list(job.get("image_paths") or []) if Path(str(p)).exists()]
        if not paths:
            QMessageBox.information(self, "Delete from disk", "No existing output files were found for this job.")
            return
        reply = QMessageBox.question(
            self,
            "Delete from disk",
            f"Move {len(paths)} output file(s) to the Windows trash bin when available?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        failed: list[str] = []
        for path in paths:
            if not move_path_to_trash(path):
                failed.append(str(path))
        if failed:
            QMessageBox.warning(self, "Delete from disk", "Could not move these files to trash:\n" + "\n".join(failed[:5]))
            return
        self.finished_jobs = [j for j in self.finished_jobs if int(j.get("job_id") or 0) != int(job.get("job_id") or 0)]
        self.save_settings()
        self.refresh_queue_views()

    def cancel_pending_job(self, job: dict) -> None:
        job_id = int(job.get("job_id") or 0)
        self.pending_jobs = [j for j in self.pending_jobs if int(j.get("job_id") or 0) != job_id]
        job["status"] = "Failed"
        job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        job["error"] = "Cancelled by user"
        self.failed_jobs.insert(0, job)
        self.status_label.setText(f"Cancelled pending job #{job_id:03d}")
        self.save_pending_jobs()
        self.refresh_queue_views()

    def cancel_running_job(self) -> None:
        if not self.worker or not self.current_job:
            return
        job = self.current_job
        job_id = int(job.get("job_id") or 0)
        reply = QMessageBox.question(
            self,
            "Cancel running job",
            f"Cancel running job #{job_id:03d}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.worker.log.disconnect(self.on_worker_log)
        except Exception:
            pass
        try:
            self.worker.image_saved.disconnect(self.on_image_saved)
        except Exception:
            pass
        try:
            self.worker.used_seed.disconnect(self.used_seed_label.setText)
        except Exception:
            pass
        try:
            self.worker.failed.disconnect(self.on_generation_failed)
        except Exception:
            pass
        try:
            self.worker.done.disconnect(self.on_generation_done)
        except Exception:
            pass
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(3000)
        job["status"] = "Failed"
        job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        job["error"] = "Cancelled by user"
        self.failed_jobs.insert(0, job)
        self.worker = None
        self.current_job = None
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"Cancelled running job #{job_id:03d}")
        self.save_pending_jobs()
        self.refresh_queue_views()
        self.start_next_job()

    def refresh_queue_views(self) -> None:
        self.running_list.clear()
        self.pending_list.clear()
        self.finished_list.clear()
        self.failed_list.clear()

        if self.current_job:
            item = QListWidgetItem(self.make_job_text(self.current_job))
            item.setData(Qt.UserRole, int(self.current_job.get("job_id") or 0))
            self.running_list.addItem(item)
        for job in self.pending_jobs:
            item = QListWidgetItem(self.make_job_text(job))
            item.setData(Qt.UserRole, int(job.get("job_id") or 0))
            self.pending_list.addItem(item)
        for job in self.finished_jobs:
            item = QListWidgetItem(self.make_job_text(job))
            item.setData(Qt.UserRole, int(job.get("job_id") or 0))
            self.finished_list.addItem(item)
        for job in self.failed_jobs:
            item = QListWidgetItem(self.make_job_text(job))
            item.setData(Qt.UserRole, int(job.get("job_id") or 0))
            self.failed_list.addItem(item)

        self.running_group.setTitle(f"Running ({1 if self.current_job else 0})")
        self.pending_group.setTitle(f"Pending ({len(self.pending_jobs)})")
        self.finished_group.setTitle(f"Finished ({len(self.finished_jobs)})")
        self.failed_group.setTitle(f"Failed ({len(self.failed_jobs)})")

        if self.current_job:
            self.queue_summary_label.setText(
                f"Running job #{self.current_job['job_id']:03d} | pending {len(self.pending_jobs)} | finished {len(self.finished_jobs)} | failed {len(self.failed_jobs)}"
            )
        elif self.pending_jobs:
            self.queue_summary_label.setText(
                f"Queue waiting | pending {len(self.pending_jobs)} | finished {len(self.finished_jobs)} | failed {len(self.failed_jobs)}"
            )
        else:
            self.queue_summary_label.setText(
                f"Queue idle | finished {len(self.finished_jobs)} | failed {len(self.failed_jobs)}"
            )

    def gather_params(self, seed: int) -> dict:
        params = {
            "prompt": self.prompt_edit.toPlainText().strip(),
            "negative": self.negative_edit.toPlainText().strip(),
            "aspect_ratio": self.aspect_combo.currentText(),
            "steps": self.steps_spin.value(),
            "cfg": self.cfg_spin.value(),
            "images": self.images_spin.value(),
            "seed": seed,
            "output_dir": self.output_edit.text().strip() or str(self.root / "output" / "lens_turbo_u4"),
            "repo_id": self.model_edit.text().strip() or MODEL_ID,
            "offload": self.offload_chk.isChecked(),
            "offline": self.offline_chk.isChecked(),
            "max_seq_len": self.max_seq_spin.value(),
        }
        if self.is_custom_resolution():
            params["use_custom_resolution"] = True
            params["custom_width"] = self.normalize_custom_width(self.custom_width_spin.value())
            params["custom_height"] = self.normalize_custom_height(self.custom_height_spin.value())
            params["base_resolution"] = 0
        else:
            params["use_custom_resolution"] = False
            params["custom_width"] = 0
            params["custom_height"] = 0
            params["base_resolution"] = self.current_base_resolution()
        return params

    def resume_pending_after_startup(self) -> None:
        if self.worker or not self.pending_jobs:
            return
        self.status_label.setText(f"Resuming {len(self.pending_jobs)} restored pending job(s)")
        self.start_next_job()

    def start_generation(self) -> None:
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Prompt", "Please enter a prompt.")
            return

        seed_text = self.seed_edit.text().strip()
        random_seed_enabled = self.seed_random_btn.isChecked()
        base_seed = int(seed_text) if (seed_text and not random_seed_enabled) else None
        batch_jobs = self.batch_spin.value()
        queued = 0
        for idx in range(batch_jobs):
            if random_seed_enabled:
                seed = random.randint(0, 2**31 - 1)
            elif base_seed is not None:
                seed = base_seed + idx
            else:
                seed = random.randint(0, 2**31 - 1)
            params = self.gather_params(seed)
            self.job_counter += 1
            job = {
                "job_id": self.job_counter,
                "status": "Pending",
                "prompt": prompt,
                "seed": seed,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "completed_at": "",
                "image_paths": [],
                "params": params,
                "error": "",
            }
            self.pending_jobs.append(job)
            queued += 1

        self.status_label.setText(f"Queued {queued} job{'s' if queued != 1 else ''}")
        self.save_pending_jobs()
        self.save_settings()
        self.refresh_queue_views()
        if not self.worker:
            self.start_next_job()

    def start_next_job(self) -> None:
        if self.worker or not self.pending_jobs:
            self.refresh_queue_views()
            return

        self.current_job = self.pending_jobs.pop(0)
        self.save_pending_jobs()
        self.current_job["status"] = "Running"
        self.log_edit.clear()
        self.last_file_label.clear()
        self.used_seed_label.setText(str(self.current_job.get("seed", "")))
        self.refined_prompt_label.clear()
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"Running job #{self.current_job['job_id']:03d}")
        self.append_log(f"Starting queued job #{self.current_job['job_id']:03d}")
        _params = self.current_job["params"]
        _pipe_key = (_params.get("repo_id") or MODEL_ID, bool(_params.get("offload", False)), bool(_params.get("offline", False)))
        _pipe = self._cached_pipe if self._cached_pipe_key == _pipe_key else None
        self.worker = LensGenerationWorker(self.root, _params, pipe=_pipe)
        self.worker.log.connect(self.on_worker_log)
        self.worker.image_saved.connect(self.on_image_saved)
        self.worker.used_seed.connect(self.used_seed_label.setText)
        self.worker.failed.connect(self.on_generation_failed)
        self.worker.done.connect(self.on_generation_done)
        self.worker.pipe_ready.connect(self._on_pipe_ready)
        self.worker.start()
        self.refresh_queue_views()

    def _on_pipe_ready(self, pipe, pipe_key) -> None:
        self._cached_pipe = pipe
        self._cached_pipe_key = pipe_key

    def on_worker_log(self, text: str) -> None:
        if self.current_job:
            self.append_log(f"[Job {self.current_job['job_id']:03d}] {text}")
        else:
            self.append_log(text)

    def on_image_saved(self, path: str) -> None:
        self.last_file_label.setText(path)
        if self.current_job:
            self.current_job.setdefault("image_paths", []).append(path)
        if Path(path).exists():
            self.image_preview.set_image(path)

    def on_generation_done(self) -> None:
        self.stop_btn.setEnabled(False)
        if self.current_job:
            self.current_job["status"] = "Finished"
            self.current_job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.finished_jobs.insert(0, self.current_job)
            self.finished_jobs = self.finished_jobs[:MAX_SAVED_FINISHED]
            self.status_label.setText(f"Finished job #{self.current_job['job_id']:03d}")
        self.worker = None
        self.current_job = None
        self.save_settings()
        self.save_pending_jobs()
        self.refresh_queue_views()
        self.start_next_job()

    def on_generation_failed(self, msg: str) -> None:
        self.stop_btn.setEnabled(False)
        if self.current_job:
            self.current_job["status"] = "Failed"
            self.current_job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.current_job["error"] = msg
            self.failed_jobs.insert(0, self.current_job)
            self.status_label.setText(f"Failed job #{self.current_job['job_id']:03d}")
        QMessageBox.warning(self, "Generation", msg)
        self.worker = None
        self.current_job = None
        self.save_pending_jobs()
        self.refresh_queue_views()
        self.start_next_job()

    def stop_generation(self) -> None:
        self.cancel_running_job()


def main() -> int:
    app = QApplication(sys.argv)
    win = LensTurboWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
