Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\datdt\Documents\Codex\2026-05-27\project-n-y-nousresearch-hermes-agent"
$EnvPath = Join-Path $ProjectDir ".env"

$openai = Read-Host "Paste OPENAI_API_KEY"
$gemini = Read-Host "Paste GEMINI_API_KEY"

@"
OPENAI_API_KEY=$openai
GEMINI_API_KEY=$gemini
"@ | Set-Content -Path $EnvPath -Encoding UTF8

Write-Host "Saved API keys to $EnvPath"
