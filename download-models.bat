call "model-download.py" || goto :error
exit /b 0

:error
echo [ERROR] Model download failed.
exit /b 1