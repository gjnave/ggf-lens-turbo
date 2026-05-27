# Get Going Fast | Lens Turbo

<img src=./assets/hhihinskifjio.png>
<a href="https://getgoingfast.pro/tools/mslens/">Download an Easy installer here</a><br>
<br>

## Fast Mode

The desktop app now defaults to resident GPU mode: the loaded Lens pipeline remains on the GPU and is reused for queued jobs. This avoids the expensive per-image module release and GPU transfer cycle caused by Diffusers CPU offload.

`Low-VRAM CPU offload` remains available in Settings when a GPU cannot hold the pipeline, but it is intentionally slower because model modules are returned to CPU between image calls.

## Install
<h2>Manual Install</h2>

<ol>
  <li>
    Download and extract the project files to a folder on your computer.
  </li>

  <li>
    Open Command Prompt in that folder.
  </li>

  <li>
    Clone the app files:
    <br>
    <code>git clone https://github.com/gjnave/ggf-lens-turbo.git</code>
  </li>

  <li>
    Enter the app folder:
    <br>
    <code>cd ggf-lens-turbo</code>
  </li>

  <li>
    Create a Python 3.11 virtual environment:
    <br>
    <code>py -3.11 -m venv venv</code>
  </li>

  <li>
    Activate the virtual environment:
    <br>
    <code>venv\Scripts\activate</code>
  </li>

  <li>
    Install the required dependencies:
    <br>
    <code>python -m pip install --upgrade pip wheel</code>
    <br>
    <code>python -m pip install setuptools==70.2.0</code>
    <br>
    <code>python -m pip install "torch&gt;=2.8.0,&lt;2.12" torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128</code>
    <br>
    <code>python -m pip install -r requirements.txt</code>
  </li>

<li>
  Download the required model files into:
  <br>
  <code>models\lens\hf_cache\models--WaveCut--Lens-Turbo-SDNQ-uint4-static</code>
</li>

<li>
  Download the required kernel files into:
  <br>
  <code>models\lens\kernels_cache\kernels--kernels-community--gpt-oss-triton-kernels</code>
</li>

  <li>
    Clone the Microsoft Lens repository:
    <br>
    <code>git clone https://github.com/microsoft/Lens.git models\lens\repos\Lens</code>
  </li>

  <li>
    Run the app:
    <br>
    <code>python app.py</code>
  </li>
</ol>
