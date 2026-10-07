# Verificación de la semana 7 en Windows (PowerShell 7 + Docker Desktop).
# Uso:  pwsh -File scripts/verify-docker.ps1          (deja los servicios corriendo)
#       pwsh -File scripts/verify-docker.ps1 -Down    (los detiene al terminar)
param([switch]$Down)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$ModelUrl = "https://github.com/darwinjaco/bank-churn-ml/releases/download/model-v1.0/model.joblib"
$Customer = @{
    CreditScore = 600; Age = 52; Tenure = 3; Balance = 120000; NumOfProducts = 1
    HasCrCard = 1; IsActiveMember = 0; Geography = "Germany"
}

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }

Step "1. Docker Desktop"
docker version --format "cliente {{.Client.Version}} / servidor {{.Server.Version}}"
if ($LASTEXITCODE -ne 0) { throw "Docker no responde: abre Docker Desktop y espera a que diga 'Engine running'." }

Step "2. Release del modelo"
try {
    # Pide solo el primer byte: evita descargar 16 MB y funciona con la redirección de GitHub.
    $probe = Invoke-WebRequest -Uri $ModelUrl -Headers @{ Range = "bytes=0-0" } -MaximumRedirection 10
    Write-Host "Release accesible (HTTP $($probe.StatusCode))"
} catch {
    throw "No existe $ModelUrl. Publica el Release 'model-v1.0' con models/model.joblib (ver README)."
}

Step "3. Build"
docker compose build
if ($LASTEXITCODE -ne 0) { throw "Falló docker compose build (revisa el error de arriba)." }

Step "4. Arranque"
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "Falló docker compose up." }
$deadline = (Get-Date).AddSeconds(240)
do {
    Start-Sleep -Seconds 3
    try { $health = Invoke-RestMethod http://localhost:8000/health -TimeoutSec 3 } catch { $health = $null }
} until ($health -or (Get-Date) -gt $deadline)
if (-not $health) { docker compose logs --tail 40; throw "La API no respondió en 4 minutos." }
Write-Host "health: $($health.status)  sha256: $($health.artifact_sha256.Substring(0,12))..."

Step "5. Pruebas de la API"
$body = $Customer | ConvertTo-Json
$p = Invoke-RestMethod -Method Post http://localhost:8000/predict -ContentType "application/json" -Body $body
"predict: probabilidad {0:N4}  contactar {1}  razones {2}" -f $p.churn_probability, $p.contact, (($p.top_reasons | ForEach-Object feature) -join ", ")
$withGender = $Customer.Clone(); $withGender.Gender = "Male"
$r = Invoke-WebRequest -Method Post http://localhost:8000/predict -ContentType "application/json" `
    -Body ($withGender | ConvertTo-Json) -SkipHttpErrorCheck
"predict con Gender -> HTTP $($r.StatusCode) (esperado 422)"
$e = Invoke-RestMethod -Method Post http://localhost:8000/explain -ContentType "application/json" -Body $body
"explain: fuente $($e.source)"

Step "6. Dashboard"
$deadline = (Get-Date).AddSeconds(120)
do {
    Start-Sleep -Seconds 3
    try { $dash = Invoke-WebRequest http://localhost:8501/_stcore/health -TimeoutSec 3 } catch { $dash = $null }
} until ($dash -or (Get-Date) -gt $deadline)
if (-not $dash) { docker compose logs dashboard --tail 40; throw "El dashboard no respondió." }
"dashboard: $($dash.Content)  ->  abre http://localhost:8501"

Step "7. Estado"
docker compose ps
docker image ls bank-churn-ml:local --format "imagen: {{.Repository}}:{{.Tag}}  {{.Size}}"

if ($Down) { Step "8. Detener"; docker compose down }
Write-Host "`nVERIFICACIÓN COMPLETA" -ForegroundColor Green
