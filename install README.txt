Get Going Fast | Lens Turbo
===========================

Install:
1. Install Python 3.11, Git, and an NVIDIA driver capable of running CUDA PyTorch.
2. Run install.bat.
3. Run run.bat.

That is all the installer does:
- creates venv/
- installs pinned, tested dependencies
- installs CUDA PyTorch from the official cu128 wheel index
- clones Microsoft Lens into models/lens/repos/Lens/
- downloads the WaveCut Lens Turbo UINT4 model into models/lens/hf_cache/
- prepares the quantized kernel cache

Why setuptools is pinned:
PyTorch CUDA 2.11 declares setuptools<82. The installer pins the tested compatible
version, setuptools 70.2.0, and runs pip check so conflicts fail clearly.

Fast generation:
Keep "Low-VRAM CPU offload" unchecked in the UI when your GPU has enough VRAM.
Offload is available for limited-memory GPUs, but releases model modules between
images and makes repeated generation slower.

Test:
  run_lens_test.bat --offline --prompt "a neon robot" --steps 4 --cfg 1
