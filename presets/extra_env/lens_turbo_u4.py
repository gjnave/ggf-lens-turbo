from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

MODEL_ID = "WaveCut/Lens-Turbo-SDNQ-uint4-static"
LENS_GIT_URL = "https://github.com/microsoft/Lens.git"
LENS_ZIP_URL = "https://github.com/microsoft/Lens/archive/refs/heads/main.zip"
ENV_NAME = ".lens_turbo_u4"
MODEL_CACHE_SUBDIR = Path("models") / "lens" / "hf_cache"


def model_cache_dir(root: Path) -> Path:
    return root / MODEL_CACHE_SUBDIR


def runtime_cache_dirs(root: Path) -> dict[str, Path]:
    base = root / "models" / "lens"
    return {
        "hf_home": base / "hf_home",
        "hf_hub_cache": base / "hf_cache",
        "transformers_cache": base / "transformers_cache",
        "hf_modules_cache": base / "hf_modules",
        "triton_cache": base / "triton_cache",
        "kernels_cache": base / "kernels_cache",
        "torch_home": base / "torch_home",
        "xdg_cache_home": base / "xdg_cache",
    }


def runtime_env(root: Path, offline: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    dirs = runtime_cache_dirs(root)
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    env["HF_HOME"] = str(dirs["hf_home"])
    env["HF_HUB_CACHE"] = str(dirs["hf_hub_cache"])
    env["HUGGINGFACE_HUB_CACHE"] = str(dirs["hf_hub_cache"])
    env["TRANSFORMERS_CACHE"] = str(dirs["transformers_cache"])
    env["HF_MODULES_CACHE"] = str(dirs["hf_modules_cache"])
    env["TRITON_CACHE_DIR"] = str(dirs["triton_cache"])
    env["KERNELS_CACHE"] = str(dirs["kernels_cache"])
    env["TORCH_HOME"] = str(dirs["torch_home"])
    env["XDG_CACHE_HOME"] = str(dirs["xdg_cache_home"])
    if offline:
        env["HF_HUB_OFFLINE"] = "1"
        env["TRANSFORMERS_OFFLINE"] = "1"
    else:
        env.pop("HF_HUB_OFFLINE", None)
        env.pop("TRANSFORMERS_OFFLINE", None)
    return env


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def log(msg: str) -> None:
    print(msg, flush=True)


def run(cmd, cwd: Path | None = None, env: dict | None = None, check: bool = True) -> int:
    printable = " ".join(str(x) for x in cmd)
    log(f"\n>> {printable}")
    p = subprocess.run([str(x) for x in cmd], cwd=str(cwd) if cwd else None, env=env)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {p.returncode}: {printable}")
    return p.returncode


def which(name: str) -> str | None:
    return shutil.which(name)


def find_conda() -> str | None:
    candidates = []
    conda_exe = os.environ.get("CONDA_EXE")
    if conda_exe:
        candidates.append(conda_exe)
    found = which("conda")
    if found:
        candidates.append(found)
    user = Path.home()
    candidates.extend([user / "miniconda3" / "Scripts" / "conda.exe", user / "anaconda3" / "Scripts" / "conda.exe", Path("C:/ProgramData/miniconda3/Scripts/conda.exe"), Path("C:/ProgramData/anaconda3/Scripts/conda.exe"), Path("C:/Miniconda3/Scripts/conda.exe"), Path("C:/Anaconda3/Scripts/conda.exe")])
    for c in candidates:
        p = Path(c)
        if p.exists(): return str(p)
    return None


def env_python(env_dir: Path) -> Path:
    p1 = env_dir / "python.exe"
    p2 = env_dir / "Scripts" / "python.exe"
    return p1 if p1.exists() else p2


def create_env(root: Path, force: bool = False) -> Path:
    env_dir = root / "environments" / ENV_NAME
    py = env_python(env_dir)
    if force and env_dir.exists():
        log(f"Removing existing env: {env_dir}")
        shutil.rmtree(env_dir)
    if py.exists():
        log(f"Using existing env: {env_dir}")
        return py
    conda = find_conda()
    if not conda:
        raise RuntimeError("Conda was not found. Install Miniconda/Anaconda or run from a shell where conda is available.")
    env_dir.parent.mkdir(parents=True, exist_ok=True)
    run([conda, "create", "-y", "-p", env_dir, "python=3.11", "pip"])
    py = env_python(env_dir)
    if not py.exists(): raise RuntimeError(f"Python was not created at expected env path: {py}")
    return py


def pip_install(py: Path, args: list[str], check: bool = True) -> int:
    return run([py, "-m", "pip", "install", *args], check=check)


def py_check(py: Path, code: str) -> bool:
    return run([py, "-c", code], check=False) == 0


def get_py_output(py: Path, code: str) -> str:
    p = subprocess.run([str(py), "-c", code], text=True, capture_output=True)
    return ((p.stdout or "") + (p.stderr or "")).strip()


def torch_cuda128_ok(py: Path) -> bool:
    code = '''
try:
    import torch
    ver = str(torch.__version__)
    cuda = str(torch.version.cuda)
    major_minor = tuple(int(x) for x in ver.split('+')[0].split('.')[:2])
    ok = major_minor >= (2, 8) and cuda == '12.8' and torch.cuda.is_available()
    print(f'torch={ver} cuda={cuda} cuda_available={torch.cuda.is_available()} ok={ok}')
    raise SystemExit(0 if ok else 1)
except Exception as e:
    print(repr(e))
    raise SystemExit(1)
'''
    return py_check(py, code)


def imports_ok(py: Path, modules: list[str]) -> bool:
    lines = ["import importlib"]
    lines += [f"importlib.import_module({m!r})" for m in modules]
    lines.append("print('imports ok')")
    return py_check(py, "\n".join(lines))


def install_python_packages(py: Path, allow_sdnq_fail: bool = False, skip_triton: bool = False) -> None:
    run([py, "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    if torch_cuda128_ok(py):
        log("\nPyTorch CUDA 12.8 is already installed; skipping PyTorch reinstall.")
    else:
        log("\nInstalling PyTorch CUDA 12.8 build from the official cu128 index...")
        pip_install(py, ["--upgrade", "torch>=2.8.0", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu128"])
    deps = ["diffusers", "transformers", "accelerate", "safetensors", "huggingface_hub", "sentencepiece", "google.protobuf", "PIL", "numpy", "scipy", "einops", "peft", "tqdm"]
    if imports_ok(py, deps):
        log("\nLens/Diffusers dependencies already import; skipping dependency reinstall.")
    else:
        log("\nInstalling Lens/Diffusers dependencies...")
        pip_install(py, ["--upgrade", "diffusers>=0.35.1", "transformers>=4.57.1", "accelerate", "safetensors", "huggingface_hub[hf_xet]", "sentencepiece", "protobuf", "pillow", "numpy", "scipy", "einops", "peft", "tqdm"])
    if imports_ok(py, ["PySide6"]):
        out = get_py_output(py, "import PySide6; print(getattr(PySide6, '__version__', 'unknown'))")
        log(f"\nPySide6 already imports; skipping PySide6 reinstall. Version: {out}")
    else:
        log("\nInstalling PySide6 for the standalone Lens UI...")
        pip_install(py, ["--upgrade", "PySide6"])
    if skip_triton:
        log("\nSkipping Triton install because --skip-triton was used.")
    elif imports_ok(py, ["triton"]):
        out = get_py_output(py, "import triton; print(getattr(triton, '__version__', 'unknown'))")
        log(f"\nTriton already imports; skipping Triton reinstall. Version: {out}")
    else:
        log("\nInstalling Triton for Windows. This is needed for MXFP4/SDNQ fast paths...")
        pip_install(py, ["--upgrade", "triton-windows<3.7"])
    if imports_ok(py, ["kernels"]):
        out = get_py_output(py, "import kernels; print(getattr(kernels, '__version__', 'ok'))")
        log(f"\nkernels already imports; skipping kernels reinstall. Version: {out}")
    else:
        log("\nInstalling kernels package for Transformers MXFP4 quantization support...")
        pip_install(py, ["--upgrade", "kernels"])
    if imports_ok(py, ["bitsandbytes"]):
        out = get_py_output(py, "import bitsandbytes as bnb; print(getattr(bnb, '__version__', 'unknown'))")
        log(f"\nbitsandbytes already imports; skipping bitsandbytes reinstall. Version: {out}")
    else:
        log("\nInstalling bitsandbytes for quantized component compatibility...")
        pip_install(py, ["--upgrade", "bitsandbytes"])
    if imports_ok(py, ["sdnq"]):
        log("\nSDNQ already imports; skipping SDNQ reinstall.")
    else:
        log("\nInstalling SDNQ package for UINT4 model support...")
        rc = pip_install(py, ["--upgrade", "sdnq"], check=False)
        if rc != 0:
            msg = "sdnq failed to install. This model will probably not load without SDNQ support."
            if allow_sdnq_fail: log("WARNING: " + msg)
            else: raise RuntimeError(msg)


def download_lens_repo(root: Path, force_repo: bool = False) -> Path:
    repo_dir = root / "models" / "lens" / "repos" / "Lens"
    if force_repo and repo_dir.exists():
        log(f"Removing existing Lens repo: {repo_dir}")
        shutil.rmtree(repo_dir)
    if (repo_dir / "lens").exists():
        log(f"Using existing Lens repo: {repo_dir}")
        return repo_dir
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    git = which("git")
    if git:
        run([git, "clone", "--depth", "1", LENS_GIT_URL, repo_dir])
        return repo_dir
    log("Git was not found; downloading Lens repo ZIP instead...")
    tmp = root / "temp" / "lens_repo_main.zip"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(LENS_ZIP_URL, tmp)
    extract_root = root / "temp" / "lens_repo_extract"
    if extract_root.exists(): shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(tmp, "r") as zf: zf.extractall(extract_root)
    src = extract_root / "Lens-main"
    if not src.exists(): raise RuntimeError("Downloaded Lens ZIP did not contain expected Lens-main folder.")
    if repo_dir.exists(): shutil.rmtree(repo_dir)
    shutil.move(str(src), str(repo_dir))
    shutil.rmtree(extract_root, ignore_errors=True)
    return repo_dir


def verify(py: Path, root: Path, repo_dir: Path) -> None:
    code = rf'''
import os, sys, json
sys.path.insert(0, r"{repo_dir}")
import torch
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
print("torch_cuda", torch.version.cuda)
if torch.cuda.is_available(): print("gpu", torch.cuda.get_device_name(0))
try:
    import triton
    print("triton import", "ok", getattr(triton, "__version__", "unknown"))
except Exception as e: print("triton import failed", repr(e))
try:
    import bitsandbytes as bnb
    print("bitsandbytes import", "ok", getattr(bnb, "__version__", "unknown"))
except Exception as e: print("bitsandbytes import failed", repr(e))
try:
    import kernels
    print("kernels import", "ok", getattr(kernels, "__version__", "ok"))
except Exception as e:
    print("kernels import failed", repr(e))
    raise
try:
    import sdnq
    print("sdnq import", "ok")
except Exception as e:
    print("sdnq import failed", repr(e))
    raise
try:
    import PySide6
    print("PySide6 import", "ok", getattr(PySide6, "__version__", "unknown"))
except Exception as e:
    print("PySide6 import failed", repr(e))
    raise
from lens import LensPipeline
print("LensPipeline import", "ok")
'''
    run([py, "-c", code], env=runtime_env(root, offline=False))


def maybe_snapshot_model(py: Path, root: Path) -> None:
    target = model_cache_dir(root)
    target.mkdir(parents=True, exist_ok=True)
    env = runtime_env(root, offline=False)
    kernel_cache = runtime_cache_dirs(root)["kernels_cache"]
    code = rf'''
from huggingface_hub import snapshot_download
from pathlib import Path
cache_dir = Path(r"{target}")
kernel_cache = Path(r"{kernel_cache}")
print("Preparing portable offline cache for:", "{MODEL_ID}")
print("cache_dir=", cache_dir)
path = snapshot_download(repo_id="{MODEL_ID}", cache_dir=str(cache_dir))
print("snapshot_download path=", path)
try:
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained("{MODEL_ID}", cache_dir=str(cache_dir), trust_remote_code=True)
    print("AutoConfig primed:", type(cfg).__name__)
except Exception as e:
    print("AutoConfig prime skipped:", repr(e))
try:
    from kernels import get_kernel
    print("Preparing trusted local kernel cache: kernels-community/gpt-oss-triton-kernels")
    get_kernel("kernels-community/gpt-oss-triton-kernels", trust_remote_code=True)
    hits = list(kernel_cache.rglob("metadata.json"))
    print("Kernel cache metadata files:", len(hits))
    if not hits:
        raise RuntimeError(f"Kernel cache did not contain metadata.json under {kernel_cache}")
    print("Kernel cache prepared.")
except Exception as e:
    print("Kernel cache prime failed:", repr(e))
    raise
print("Portable cache prepared.")
'''
    run([py, "-c", code], env=env)


def print_model_cache_hint(root: Path) -> None:
    target = model_cache_dir(root)
    target.mkdir(parents=True, exist_ok=True)
    expected = target / "models--WaveCut--Lens-Turbo-SDNQ-uint4-static"
    log("\nPortable Hugging Face model cache:")
    log(f"  {target}")
    if expected.exists():
        log(f"Found local Lens Turbo U4 cache folder: {expected}")
    else:
        log("Model cache folder was not found yet.")
        log("If you already downloaded it in the default Hugging Face cache, move/copy:")
        log(r"  %USERPROFILE%\.cache\huggingface\hub\models--WaveCut--Lens-Turbo-SDNQ-uint4-static")
        log("to:")
        log(f"  {expected}")
        log("Then the test runner will reuse it instead of downloading again.")

def write_env_info(root: Path, py: Path, repo_dir: Path) -> None:
    logs = root / "logs"; logs.mkdir(parents=True, exist_ok=True)
    info = logs / "lens_turbo_u4_install_info.txt"
    extra = get_py_output(py, '''
import sys
print('python=' + sys.version.split()[0])
try:
    import torch
    print('torch=' + str(torch.__version__))
    print('torch_cuda=' + str(torch.version.cuda))
except Exception as e: print('torch_error=' + repr(e))
for name in ['triton', 'bitsandbytes', 'kernels', 'sdnq', 'PySide6', 'diffusers', 'transformers', 'accelerate']:
    try:
        mod = __import__(name)
        print(name + '=' + str(getattr(mod, '__version__', 'ok')))
    except Exception as e:
        print(name + '_error=' + repr(e))
''')
    caches = runtime_cache_dirs(root)
    info.write_text("Lens Turbo SDNQ UINT4 installer\n" + f"installed_at={time.strftime('%Y-%m-%d %H:%M:%S')}\nroot={root}\nenv_python={py}\nlens_repo={repo_dir}\nmodel_id={MODEL_ID}\nmodel_cache={model_cache_dir(root)}\nportable_hf_home={caches['hf_home']}\nportable_transformers_cache={caches['transformers_cache']}\nportable_hf_modules_cache={caches['hf_modules_cache']}\nportable_triton_cache={caches['triton_cache']}\nportable_kernels_cache={caches['kernels_cache']}\nportable_torch_home={caches['torch_home']}\n\nPackage info:\n{extra}\n", encoding="utf-8")
    log(f"Wrote install info: {info}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install standalone Lens Turbo SDNQ UINT4 test environment.")
    parser.add_argument("--force-env", action="store_true", help="Delete and recreate the conda env.")
    parser.add_argument("--force-repo", action="store_true", help="Delete and redownload the Microsoft Lens repo.")
    parser.add_argument("--download-model", action="store_true", help="Compatibility flag. The installer now prepares the portable offline model/runtime cache automatically.")
    parser.add_argument("--allow-sdnq-fail", action="store_true", help="Continue if pip install sdnq fails.")
    parser.add_argument("--skip-triton", action="store_true", help="Do not install/check Triton Windows.")
    args = parser.parse_args()
    root = root_dir(); log(f"Root: {root}")
    (root / "models" / "lens").mkdir(parents=True, exist_ok=True)
    model_cache_dir(root).mkdir(parents=True, exist_ok=True)
    for path in runtime_cache_dirs(root).values():
        path.mkdir(parents=True, exist_ok=True)
    (root / "output" / "lens_turbo_u4").mkdir(parents=True, exist_ok=True)
    (root / "temp").mkdir(parents=True, exist_ok=True)
    py = create_env(root, force=args.force_env)
    install_python_packages(py, allow_sdnq_fail=args.allow_sdnq_fail, skip_triton=args.skip_triton)
    repo_dir = download_lens_repo(root, force_repo=args.force_repo)
    verify(py, root, repo_dir)
    maybe_snapshot_model(py, root)
    print_model_cache_hint(root)
    write_env_info(root, py, repo_dir)
    log("\nDONE"); log("Portable offline cache was prepared during install. Lens should now keep working offline, including after restart."); log("Run run_lens_test.bat --offload to try a small image generation test.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("\nERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
