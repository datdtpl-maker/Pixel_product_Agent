Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\datdt\Documents\Codex\2026-05-27\project-n-y-nousresearch-hermes-agent"
Set-Location $ProjectDir

python -m pip install -r requirements.txt
python .\photo_pipeline.py run-once --product "Ten San Pham Test"
