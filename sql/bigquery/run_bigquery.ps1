# WP34b - Run the four BigQuery raw-table SQL ports, then reconcile against DuckDB.
# Prereqs: gcloud auth login done; the project is set; sql/bigquery/load_to_bigquery.ps1
# has already loaded raw_* tables into platzi_fpa. Rerunnable: each bq_ table is replaced.
# Run: powershell -ExecutionPolicy Bypass -File sql\bigquery\run_bigquery.ps1
param(
  [string]$Project = "project-b7f9b2e4-dcdc-4e36-b89",
  [string]$Dataset = "platzi_fpa"
)
$ErrorActionPreference = "Stop"
$gbin = "$env:LOCALAPPDATA\gcloud\google-cloud-sdk\bin"
$env:PATH = "$gbin;$env:PATH"   # bq calls gcloud for credentials; the portable install is not on PATH
$bq = "$gbin\bq.cmd"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$queries = @("q1_mrr_apr24.sql", "q2_retention_q1_24.sql", "q3_active_subs_apr24.sql", "q4_ndr_t12m.sql")
$tmpDir = [System.IO.Path]::GetTempPath()
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

foreach ($q in $queries) {
  $path = Join-Path $PSScriptRoot $q
  Write-Output "=== Running $q ==="
  # PowerShell piping a string to a native console app can prepend a UTF-8 BOM
  # on stdin, which bq's SQL parser rejects as an illegal character. Work
  # around it by rewriting the query to a temp file with explicit BOM-less
  # UTF-8, then redirecting bq's stdin from that file (cmd.exe `<` redirection
  # reads raw bytes, no BOM re-insertion).
  $sql = [System.IO.File]::ReadAllText($path).TrimStart([char]0xFEFF)
  $tmpFile = Join-Path $tmpDir "wp34b_$q"
  [System.IO.File]::WriteAllText($tmpFile, $sql, $utf8NoBom)
  cmd /c "`"$bq`" --project_id=$Project query --use_legacy_sql=false < `"$tmpFile`""
  $exit = $LASTEXITCODE
  Remove-Item $tmpFile -ErrorAction SilentlyContinue
  if ($exit -ne 0) {
    Write-Error "Query $q failed (exit $exit)"
    exit 1
  }
}

Write-Output "`n=== Reconciling against DuckDB marts ==="
$env:PYTHONIOENCODING = "utf-8"
& "$root\.venv\Scripts\python.exe" (Join-Path $PSScriptRoot "reconcile.py")
exit $LASTEXITCODE
