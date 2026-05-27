# Get Going Fast | Lens Turbo

<img src=./assets/hhihinskifjio.png>
<a href="https://getgoingfast.pro/tools/mslens/">Download an Easy installer here</a><br>
<br>

## Fast Mode

The desktop app now defaults to resident GPU mode: the loaded Lens pipeline remains on the GPU and is reused for queued jobs. This avoids the expensive per-image module release and GPU transfer cycle caused by Diffusers CPU offload.

`Low-VRAM CPU offload` remains available in Settings when a GPU cannot hold the pipeline, but it is intentionally slower because model modules are returned to CPU between image calls.
