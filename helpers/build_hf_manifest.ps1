param(
    [Parameter(Mandatory = $true)][string]$Repo,
    [Parameter(Mandatory = $true)][string]$Dest,
    [Parameter(Mandatory = $true)][string]$MetaJson,
    [Parameter(Mandatory = $true)][string]$UrlsTxt
)

$ErrorActionPreference = "Stop"

$meta = Get-Content -LiteralPath $MetaJson -Raw | ConvertFrom-Json
$revision = [string]$meta.sha
if (-not $revision) {
    throw "Could not resolve repository revision SHA."
}

$snapshotRoot = Join-Path $Dest ("snapshots\" + $revision)
New-Item -ItemType Directory -Force -Path $Dest, (Join-Path $Dest "refs"), $snapshotRoot | Out-Null

$files = @($meta.siblings | Where-Object { $_.rfilename } | Select-Object -ExpandProperty rfilename)
if (-not $files.Count) {
    throw "No downloadable files were returned for $Repo."
}

if ($Repo -eq "kernels-community/gpt-oss-triton-kernels") {
    $files = @(
        $files | Where-Object {
            $_ -eq ".gitattributes" -or
            $_ -eq "README.md" -or
            $_ -like "build/torch-cuda/*"
        }
    )
    if (-not $files.Count) {
        throw "No CUDA kernel files were returned for $Repo."
    }
}

$entries = foreach ($file in $files) {
    $target = Join-Path $snapshotRoot ($file.Replace("/", "\"))
    $dir = Split-Path -Parent $target
    $name = Split-Path -Leaf $target
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    "https://huggingface.co/$Repo/resolve/$revision/${file}?download=true"
    "  dir=$dir"
    "  out=$name"
}

Set-Content -LiteralPath $UrlsTxt -Value $entries -Encoding ascii
Set-Content -LiteralPath (Join-Path $Dest "refs\main") -Value $revision -Encoding ascii
