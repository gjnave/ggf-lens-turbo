# Get Going Fast | Lens Turbo

Fast local image generation powered by `WaveCut/Lens-Turbo-SDNQ-uint4-static`, packaged as a Windows desktop UI.

Styled for [Get Going Fast](https://getgoingfast.pro/) with help from [DJ Grizzly on YouTube](https://www.youtube.com/@dj__grizzly).

## Fast Mode

The desktop app now defaults to resident GPU mode: the loaded Lens pipeline remains on the GPU and is reused for queued jobs. This avoids the expensive per-image module release and GPU transfer cycle caused by Diffusers CPU offload.

`Low-VRAM CPU offload` remains available in Settings when a GPU cannot hold the pipeline, but it is intentionally slower because model modules are returned to CPU between image calls.

## Run

1. Install Python 3.11, Git, and a CUDA-capable NVIDIA driver.
2. For a tiny bootstrap zip, ship only `disclaimer.md`, `about.nfo`, `install.bat`, and `run.bat`.
3. Run `install.bat` once. It can clone this repo automatically, then installs pinned tested dependencies, clones Microsoft Lens, and downloads the model/kernel cache.
4. Run `run.bat` to launch the UI.
5. Keep `Low-VRAM CPU offload` off for fastest repeated generations.

`setuptools` is pinned to tested version `70.2.0` because the CUDA PyTorch build requires `setuptools<82`; setup finishes with `pip check` so conflicts do not get ignored.

Models, environments, package caches, output images, logs, and local saved prompts/settings are intentionally excluded from the source backup.
