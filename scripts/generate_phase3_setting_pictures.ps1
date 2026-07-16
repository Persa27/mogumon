param(
  [switch]$ForceRegenerate
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$braveCandidates = @(
  "${env:ProgramFiles}\BraveSoftware\Brave-Browser\Application\brave.exe",
  "${env:ProgramFiles(x86)}\BraveSoftware\Brave-Browser\Application\brave.exe",
  "${env:LocalAppData}\BraveSoftware\Brave-Browser\Application\brave.exe"
)

$bravePath = $braveCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $bravePath) {
  throw "Brave was not found."
}

$debugPort = 9222
$profileDir = Join-Path $root ".brave-gemini-profile"
$promptDir = Join-Path $root ".gemini-output\prompts\phase3_settings"
$outputDir = Join-Path $root "static\monsters\setting_picture"

$jobs = @(
  @{ Prompt = "draup_mature.txt"; Output = "draup_mature.png" },
  @{ Prompt = "draup_final.txt"; Output = "draup_final.png" },
  @{ Prompt = "garoron_mature.txt"; Output = "garoron_mature.png" },
  @{ Prompt = "garoron_final.txt"; Output = "garoron_final.png" },
  @{ Prompt = "fishul_mature.txt"; Output = "fishul_mature.png" },
  @{ Prompt = "fishul_final.txt"; Output = "fishul_final.png" },
  @{ Prompt = "kororon_mature.txt"; Output = "kororon_mature.png" },
  @{ Prompt = "kororon_final.txt"; Output = "kororon_final.png" },
  @{ Prompt = "lumina_mature.txt"; Output = "lumina_mature.png" },
  @{ Prompt = "lumina_final.txt"; Output = "lumina_final.png" }
)

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

function Stop-BraveDebugSession {
  $debugProcesses = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -ieq "brave.exe" -and
    $_.CommandLine -match "--remote-debugging-port=$debugPort" -and
    $_.CommandLine -like "*$profileDir*"
  }

  foreach ($process in $debugProcesses) {
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
  }

  Start-Sleep -Seconds 2
}

function Start-BraveDebugSession {
  $existingBrave = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -ieq "brave.exe" -and
    $_.CommandLine -match "--remote-debugging-port=$debugPort" -and
    $_.CommandLine -like "*$profileDir*"
  } | Select-Object -First 1

  if (-not $existingBrave) {
    $args = @(
      "--remote-debugging-port=$debugPort",
      "--user-data-dir=$profileDir",
      "--new-window",
      "https://gemini.google.com/app"
    )
    Start-Process -FilePath $bravePath -ArgumentList $args -WindowStyle Normal | Out-Null
    Start-Sleep -Seconds 5
  }

  $ready = $false
  for ($i = 0; $i -lt 20; $i += 1) {
    try {
      Invoke-WebRequest -Uri "http://127.0.0.1:$debugPort/json/version" -UseBasicParsing -TimeoutSec 2 | Out-Null
      $ready = $true
      break
    } catch {
      Start-Sleep -Seconds 1
    }
  }

  if (-not $ready) {
    throw "Brave remote debugging port $debugPort did not become ready."
  }
}

foreach ($job in $jobs) {
  $promptPath = Join-Path $promptDir $job.Prompt
  $outputPath = Join-Path $outputDir $job.Output
  $completed = $false

  if ((-not $ForceRegenerate.IsPresent) -and (Test-Path $outputPath)) {
    Write-Host "Skipping existing $($job.Output)"
    continue
  }

  for ($attempt = 1; $attempt -le 3; $attempt += 1) {
    Write-Host "Generating $($job.Output)... attempt $attempt/3"

    Start-BraveDebugSession

    node (Join-Path $PSScriptRoot "gemini_attach.js") `
      --prompt-file $promptPath `
      --output-file $outputPath `
      --timeout-ms 300000

    if ($LASTEXITCODE -eq 0) {
      $completed = $true
      break
    }

    Write-Host "Reloading Brave Gemini session for retry..."
    Stop-BraveDebugSession
  }

  if (-not $completed) {
    throw "Generation failed for $($job.Output) after 3 attempts."
  }
}

Write-Host "Saved files to $outputDir"
