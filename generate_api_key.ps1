# Generator API Key dla Route Pricing API
# Wygeneruje bezpieczny, losowy klucz API

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Route Pricing API - Generator API Key" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Generuj bezpieczny losowy klucz
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$apiKey = [Convert]::ToBase64String($bytes)

# Wyświetl wyniki
Write-Host "✓ Wygenerowano nowy API key:" -ForegroundColor Green
Write-Host ""
Write-Host "API_KEY=$apiKey" -ForegroundColor Yellow
Write-Host ""

# Instrukcje
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Co dalej?" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. LOKALNIE (.env):" -ForegroundColor White
Write-Host "   Skopiuj powyższą linię do pliku .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. NA RENDER:" -ForegroundColor White
Write-Host "   Dashboard → Your Service → Environment" -ForegroundColor Gray
Write-Host "   Add Environment Variable:" -ForegroundColor Gray
Write-Host "   Key: API_KEY" -ForegroundColor Gray
Write-Host "   Value: $apiKey" -ForegroundColor Gray
Write-Host ""
Write-Host "3. ZAPISZ BEZPIECZNIE:" -ForegroundColor White
Write-Host "   Zachowaj ten klucz w menedżerze haseł!" -ForegroundColor Gray
Write-Host "   Nie udostępniaj go publicznie." -ForegroundColor Gray
Write-Host ""

# Opcja zapisu do pliku
$save = Read-Host "Zapisać klucz do pliku .env? (t/n)"
if ($save -eq "t" -or $save -eq "T" -or $save -eq "y" -or $save -eq "Y") {
    $envPath = Join-Path $PSScriptRoot ".env"
    
    # Sprawdź czy .env już istnieje
    if (Test-Path $envPath) {
        $overwrite = Read-Host "Plik .env już istnieje. Nadpisać? (t/n)"
        if ($overwrite -ne "t" -and $overwrite -ne "T" -and $overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Host "Anulowano." -ForegroundColor Yellow
            exit
        }
    }
    
    # Zapisz do .env
    @"
# PostgreSQL Database Configuration
POSTGRES_HOST=your-database-host.render.com
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_DB=your_database_name
POSTGRES_PASSWORD=your_password

# API Security
API_KEY=$apiKey
REQUIRE_API_KEY=true
"@ | Out-File -FilePath $envPath -Encoding UTF8
    
    Write-Host ""
    Write-Host "✓ Zapisano do .env" -ForegroundColor Green
    Write-Host "Edytuj plik i uzupełnij dane do PostgreSQL" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Gotowe! 🎉" -ForegroundColor Green
