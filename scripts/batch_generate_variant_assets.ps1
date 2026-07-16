$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$promptDir = Join-Path $root ".gemini-output\prompts"
$rawDir = Join-Path $root ".gemini-output\raw_variants"
$transparentDir = Join-Path $root ".gemini-output\transparent_variants"

python (Join-Path $PSScriptRoot "generate_gemini_variant_prompts.py")

$manifest = Get-Content (Join-Path $promptDir "manifest.json") -Raw | ConvertFrom-Json

foreach ($asset in $manifest.PSObject.Properties.Name) {
  $promptFile = $manifest.$asset
  $outputFile = Join-Path $rawDir "$asset.png"
  $transparentFile = Join-Path $transparentDir "$asset.png"
  Write-Host "Generating $asset"
  node (Join-Path $PSScriptRoot "gemini_attach.js") --prompt-file $promptFile --output-file $outputFile --timeout-ms 240000
  node (Join-Path $PSScriptRoot "browser_remove_background.js") --input $outputFile --output $transparentFile --timeout-ms 240000
  python (Join-Path $PSScriptRoot "crop_generated_sheet.py") --source $transparentFile --target (Join-Path $root "static\monsters\$asset")
}
