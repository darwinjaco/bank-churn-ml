# Verificación Docker en Windows (PowerShell 7 + Docker Desktop). Specs 005 §8 y 006 §2.
# Uso:  pwsh -File scripts/verify-docker.ps1          (deja los servicios corriendo)
#       pwsh -File scripts/verify-docker.ps1 -Down    (los detiene al terminar)
#       pwsh -File scripts/verify-docker.ps1 -LocalModel  (usa models/model.joblib, sin Release;
#                                                          omite la imagen del Space)
# Cada comprobación falla con un error si el resultado no es el esperado.
param([switch]$Down, [switch]$LocalModel)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$ModelUrl = "https://github.com/darwinjaco/bank-churn-ml/releases/download/model-v1.0/model.joblib"
$ExpectedSha = "579b7fe349dc035c3171582cbfba1bfaed4599a795da4b149d7664ed21dc095a"
$Compose = @("compose")
if ($LocalModel) { $Compose += @("-f", "docker-compose.yml", "-f", "docker-compose.local.yml") }
$Customer = @{
    CreditScore = 600; Age = 52; Tenure = 3; Balance = 120000; NumOfProducts = 1
    HasCrCard = 1; IsActiveMember = 0; Geography = "Germany"
}

$ExpectedProbability = 0.947   # Cliente de referencia (spec 006 §2.5)

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Check($condition, $message) {
    if (-not $condition) { throw "FALLO: $message" }
    Write-Host "  ok: $message" -ForegroundColor Green
}
function WaitHttp($url, $seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    do {
        Start-Sleep -Seconds 3
        try { return Invoke-WebRequest $url -TimeoutSec 3 } catch { }
    } until ((Get-Date) -gt $deadline)
    return $null
}

Step "1. Docker Desktop"
docker version --format "cliente {{.Client.Version}} / servidor {{.Server.Version}}"
if ($LASTEXITCODE -ne 0) { throw "Docker no responde: abre Docker Desktop y espera a que diga 'Engine running'." }

if ($LocalModel) {
    Step "2. Modelo local"
    if (-not (Test-Path models/model.joblib)) { throw "Falta models/model.joblib." }
    $sha = (Get-FileHash models/model.joblib -Algorithm SHA256).Hash.ToLower()
    if ($sha -ne $ExpectedSha) { throw "SHA-256 local $sha != esperado $ExpectedSha" }
    Write-Host "models/model.joblib verificado ($($sha.Substring(0,12))...)"
} else {
    Step "2. Release del modelo"
    try {
        # Pide solo el primer byte: evita descargar 16 MB y funciona con la redirección de GitHub.
        $probe = Invoke-WebRequest -Uri $ModelUrl -Headers @{ Range = "bytes=0-0" } -MaximumRedirection 10
        Write-Host "Release accesible (HTTP $($probe.StatusCode))"
    } catch {
        throw "No existe $ModelUrl. Publica el Release 'model-v1.0' o usa -LocalModel."
    }
}

Step "3. Build"
docker @Compose build
if ($LASTEXITCODE -ne 0) { throw "Falló docker compose build (revisa el error de arriba)." }

Step "4. Arranque"
docker @Compose up -d
if ($LASTEXITCODE -ne 0) { throw "Falló docker compose up." }
$deadline = (Get-Date).AddSeconds(240)
do {
    Start-Sleep -Seconds 3
    try { $health = Invoke-RestMethod http://localhost:8000/health -TimeoutSec 3 } catch { $health = $null }
} until ($health -or (Get-Date) -gt $deadline)
if (-not $health) { docker @Compose logs --tail 40; throw "La API no respondió en 4 minutos." }
Write-Host "health: $($health.status)  sha256: $($health.artifact_sha256.Substring(0,12))..."

Step "5. Pruebas de la API"
$body = $Customer | ConvertTo-Json
Check ($health.artifact_sha256 -eq $ExpectedSha) "SHA-256 servido = publicado"
$p = Invoke-RestMethod -Method Post http://localhost:8000/predict -ContentType "application/json" -Body $body
"predict: probabilidad {0:N4}  contactar {1}  razones {2}" -f $p.churn_probability, $p.contact, (($p.top_reasons | ForEach-Object feature) -join ", ")
Check ([math]::Abs($p.churn_probability - $ExpectedProbability) -lt 0.001) "probabilidad del cliente de referencia = $ExpectedProbability"
Check ($p.contact -eq $true) "decisión del cliente de referencia = contactar"
$withGender = $Customer.Clone(); $withGender.Gender = "Male"
$r = Invoke-WebRequest -Method Post http://localhost:8000/predict -ContentType "application/json" `
    -Body ($withGender | ConvertTo-Json) -SkipHttpErrorCheck
Check ($r.StatusCode -eq 422) "Gender en la entrada -> HTTP 422"
$e = Invoke-RestMethod -Method Post http://localhost:8000/explain -ContentType "application/json" -Body $body
Check ($e.source -in @("llm", "template")) "explain responde (fuente: $($e.source))"
$m = Invoke-WebRequest http://localhost:8000/monitoring -SkipHttpErrorCheck
Check ($m.StatusCode -eq 200) "GET /monitoring disponible"

Step "6. Dashboard"
$dash = WaitHttp http://localhost:8501/_stcore/health 120
if (-not $dash) { docker @Compose logs dashboard --tail 40; throw "El dashboard no respondió." }
"dashboard: $($dash.Content)  ->  abre http://localhost:8501"

Step "7. Estado"
docker @Compose ps
docker image ls bank-churn-ml:local --format "imagen: {{.Repository}}:{{.Tag}}  {{.Size}}"

if ($LocalModel) {
    Write-Host "`n(Imagen del Space omitida con -LocalModel: su Dockerfile solo usa el Release.)"
} else {
    Step "8. Imagen del Space (Dockerfile derivado, ROLE=all, puerto 7860)"
    $spaceDir = Join-Path ([IO.Path]::GetTempPath()) ("bank-churn-space-" + [guid]::NewGuid().ToString("N"))
    uv run python scripts/build_space.py --out $spaceDir
    if ($LASTEXITCODE -ne 0) { throw "Falló scripts/build_space.py." }
    docker build -t bank-churn-ml:space $spaceDir
    if ($LASTEXITCODE -ne 0) { throw "Falló el build de la imagen del Space." }
    docker rm -f bank-churn-space 2>$null | Out-Null
    docker run -d --name bank-churn-space -p 7860:7860 bank-churn-ml:space | Out-Null
    try {
        $space = WaitHttp http://localhost:7860/_stcore/health 180
        if (-not $space) { docker logs bank-churn-space --tail 40 }
        Check ($null -ne $space) "dashboard del Space responde en el puerto 7860"
        $internal = docker exec bank-churn-space python -c "import urllib.request as u; print(u.urlopen('http://127.0.0.1:8000/health').status)"
        Check ($internal -eq "200") "API interna en 127.0.0.1:8000 dentro del contenedor"
        docker image ls bank-churn-ml:space --format "imagen del Space: {{.Size}}"
    } finally {
        docker rm -f bank-churn-space | Out-Null
        Remove-Item -Recurse -Force $spaceDir -ErrorAction SilentlyContinue
    }
}

if ($Down) { Step "9. Detener"; docker @Compose down }
Write-Host "`nVERIFICACIÓN COMPLETA" -ForegroundColor Green
