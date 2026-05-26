Lens Turbo SDNQ UINT4 standalone installer
=========================================

Files:
- install.bat
- run_lens_test.bat
- presets/extra_env/lens_turbo_u4.py
- helpers/lens_turbo_u4_test.py

Install:
1. Extract this folder somewhere portable, for example C:\lens_turbo_u4.
2. Run install.bat.
3. After install, run run_lens_test.bat.

Default locations created by the installer:
- environments/.lens_turbo_u4/
- models/lens/repos/Lens/
- output/lens_turbo_u4/
- logs/

The installer uses a conda environment if conda is available.
It targets Python 3.11 and PyTorch CUDA 12.8 wheels through the official cu128 PyTorch index.
It installs/updates the Microsoft Lens repo because Lens needs its local custom Python package for LensPipeline.

Useful options:
- install.bat --download-model
  Also asks Hugging Face to snapshot the WaveCut/Lens-Turbo-SDNQ-uint4-static model during install.

- run_lens_test.bat --prompt "a neon robot in a rainy alley" --steps 4 --cfg 1
  Runs a small test image in fast resident-GPU mode.

- run_lens_test.bat --prompt "a neon robot in a rainy alley" --steps 4 --cfg 1 --offload
  Runs with the slower low-VRAM fallback. CPU offload releases modules after image calls.

Notes:
- First model run can take a while because Hugging Face downloads model files.
- If sdnq or Lens changes upstream, this installer may need package/version adjustment.


- Installer adds/checks Triton Windows with triton-windows<3.7.
- Installer adds/checks bitsandbytes.
- Installer skips the large PyTorch CUDA reinstall when torch CUDA 12.8 is already working.
- Test runner imports Triton, bitsandbytes, and SDNQ before LensPipeline.from_pretrained so quant hooks have the best chance to register.
- Leave CPU offload disabled for fastest repeated generations when GPU memory is sufficient.
- Installer now adds/checks the `kernels` package required by Transformers MXFP4 CUDA quantization.
- The test runner now hard-fails before loading if Triton, kernels, bitsandbytes, or SDNQ are missing.
- If the console still prints `defaulting the model to bf16`, stop the run because the quant path is not active and memory can explode.
- Rerunning install.bat should skip existing Torch/Lens/Diffusers/SDNQ/Triton/bitsandbytes and only add missing packages.


Portable model cache note
-------------------------
Lens model weights are now forced to use this local app-folder Hugging Face cache:

  models/lens/hf_cache/

If you already downloaded WaveCut/Lens-Turbo-SDNQ-uint4-static, move/copy into this folder:
  models/lens/hf_cache/models--WaveCut--Lens-Turbo-SDNQ-uint4-static

After that, run_lens_test.bat should reuse the local files instead of downloading again.
For a strict no-download test, run:

  run_lens_test.bat --offload --offline

If --offline fails, the local cache folder is incomplete or in the wrong place.
