$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$env:PYTHONPATH = "$repoRoot\packages\audio_id;$repoRoot"
python -m unittest discover -s tests

