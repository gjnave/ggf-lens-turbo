from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

MODEL_ID = "WaveCut/Lens-Turbo-SDNQ-uint4-static"


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick Lens Turbo SDNQ UINT4 generation test.")
    parser.add_argument("--prompt", default="A tiny silver robot holding a sign that says Lens Turbo U4, cinematic lighting, sharp details")
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--cfg", type=float, default=1.0)
    parser.add_argument("--base-resolution", type=int, default=1024)
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--offload", action="store_true", help="Low-VRAM fallback: releases pipeline modules to CPU after each image and is slower than resident GPU mode.")
    parser.add_argument("--repo-id", default=MODEL_ID)
    parser.add_argument("--offline", action="store_true", help="Use only the portable local cache and fail instead of downloading.")
    args = parser.parse_args()
    root = root_dir()
    lens_repo = root / "models" / "lens" / "repos" / "Lens"
    model_cache = configure_runtime_env(root, offline=args.offline)
    model_cache.mkdir(parents=True, exist_ok=True)
    if not (lens_repo / "lens").exists():
        raise RuntimeError(f"Lens repo not found: {lens_repo}. Run install.bat first.")
    sys.path.insert(0, str(lens_repo))
    import torch
    print("torch", torch.__version__)
    print("torch cuda", torch.version.cuda)
    print("cuda available", torch.cuda.is_available())
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is not available. This test requires NVIDIA CUDA PyTorch.")
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
        import sdnq
        print("sdnq import ok")
    except Exception as e:
        print("ERROR: sdnq import failed:", repr(e))
        missing.append("sdnq")
    if missing:
        raise RuntimeError("Missing quantization support package(s): " + ", ".join(missing) + ". Run install.bat again before testing.")
    patch_transformers_kernel_trust(root)
    from lens import LensPipeline
    from lens import LensGptOssEncoder
    out_dir = root / "output" / "lens_turbo_u4"; out_dir.mkdir(parents=True, exist_ok=True)
    print("Loading", args.repo_id)
    print("portable cache", model_cache)
    print("If Transformers prints 'defaulting the model to bf16', stop the run: MXFP4/quant kernels are still not active.")
    t0 = time.time()
    text_encoder_kwargs = {"subfolder": "text_encoder", "dtype": torch.bfloat16, "cache_dir": str(model_cache), "local_files_only": args.offline, "trust_remote_code": True}
    try:
        from transformers import Mxfp4Config
        try:
            text_encoder_kwargs["quantization_config"] = Mxfp4Config(dequantize=False, trust_remote_code=True)
        except TypeError:
            text_encoder_kwargs["quantization_config"] = Mxfp4Config(dequantize=False)
    except Exception as e:
        print("Mxfp4Config unavailable", repr(e))
    text_encoder = LensGptOssEncoder.from_pretrained(args.repo_id, **text_encoder_kwargs)
    pipe = LensPipeline.from_pretrained(args.repo_id, text_encoder=text_encoder, torch_dtype=torch.bfloat16, cache_dir=str(model_cache), local_files_only=args.offline, trust_remote_code=True)
    if args.offload:
        print("Low-VRAM CPU offload enabled: repeated generations will be slower.")
        pipe.enable_model_cpu_offload()
    else:
        print("Fast mode: keeping the Lens pipeline resident on the GPU.")
        pipe.to("cuda")
    print(f"loaded in {time.time() - t0:.2f}s")
    gen = torch.Generator("cuda").manual_seed(args.seed)
    print("Generating...")
    t1 = time.time()
    result = pipe(prompt=args.prompt, base_resolution=args.base_resolution, aspect_ratio=args.aspect_ratio, num_inference_steps=args.steps, guidance_scale=args.cfg, generator=gen)
    image = result.images[0]
    path = out_dir / f"lens_turbo_u4_{time.strftime('%Y%m%d_%H%M%S')}_seed{args.seed}.png"
    image.save(path)
    print(f"generated in {time.time() - t1:.2f}s")
    print("saved", path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
