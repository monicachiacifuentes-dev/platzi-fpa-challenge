# WP34 - Load the raw data and every pipeline table into BigQuery (dataset platzi_fpa).
# Prereqs: gcloud auth login done; the project is set. Rerunnable: each table is replaced.
# Run: powershell -ExecutionPolicy Bypass -File sql\bigquery\load_to_bigquery.ps1
param(
  [string]$Project = "project-b7f9b2e4-dcdc-4e36-b89",
  [string]$Dataset = "platzi_fpa",
  [string]$Location = "US"
)
$ErrorActionPreference = "Continue"
$gbin = "$env:LOCALAPPDATA\gcloud\google-cloud-sdk\bin"
$env:PATH = "$gbin;$env:PATH"   # bq calls gcloud for credentials; the portable install is not on PATH
$bq = "$gbin\bq.cmd"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Create the dataset if it doesn't exist
$exists = & $bq --project_id=$Project ls --datasets 2>$null | Select-String -SimpleMatch $Dataset
if (-not $exists) { & $bq --project_id=$Project --location=$Location mk --dataset "${Project}:${Dataset}" | Out-Null }

$files = @()
Get-ChildItem "$root\Docs\Originals\*.csv" | ForEach-Object { $files += ,@(("raw_" + $_.BaseName), $_.FullName) }
Get-ChildItem "$root\outputs\marts\*.csv" | ForEach-Object { $files += ,@($_.BaseName, $_.FullName) }

$ok = 0; $fail = @()
foreach ($f in $files) {
  $table = $f[0]; $path = $f[1]
  $out = & $bq --project_id=$Project --location=$Location load --replace --autodetect `
         --source_format=CSV --skip_leading_rows=1 "${Dataset}.${table}" "$path" 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) { $ok++; Write-Output "OK   $table" } else { $fail += $table; Write-Output "FAIL $table`n$out" }
}
Write-Output "`nLoaded $ok of $($files.Count) tables into ${Project}:${Dataset}"
if ($fail.Count -gt 0) { Write-Output ("Failed: " + ($fail -join ", ")) }
