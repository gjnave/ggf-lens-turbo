Get Going Fast | Lens Turbo
===========================

Install:
1. Put `disclaimer.md`, `about.nfo`, `install.bat`, `run.bat`, `aria2c.exe`, and `model-download.py` in one folder.
2. Install Miniconda/Anaconda, Git, and an NVIDIA driver capable of running CUDA PyTorch.
3. Run `install.bat`. This will create a Conda environment with Python 3.11.
4. Run `run.bat`.

That is all the installer does:
- clones the public `ggf-lens-turbo` repo if the full app is not already present
- creates a Conda environment in environments/conda/
- installs pinned, tested dependencies
- installs CUDA PyTorch from the official cu124 wheel index
- clones Microsoft Lens into models/lens/repos/Lens/
- downloads the WaveCut Lens Turbo UINT4 model into models/lens/hf_cache/ (using aria2c if available)
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
