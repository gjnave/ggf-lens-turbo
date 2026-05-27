@echo off
set HF_HUB_DISABLE_XET=1
set HF_HUB_DOWNLOAD_TIMEOUT=60
set HF_HUB_ETAG_TIMEOUT=60

call "model-download.py" || goto :error
exit /b 0

:error
echo [ERROR] Model download failed.
exit /b 1