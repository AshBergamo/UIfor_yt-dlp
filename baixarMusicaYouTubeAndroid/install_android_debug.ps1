$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

.\build_android.ps1

$adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path -LiteralPath $adb)) {
    throw "adb não encontrado em $adb"
}

$devices = & $adb devices
$connected = $devices | Select-String -Pattern "`tdevice$"
if (-not $connected) {
    throw "Nenhum aparelho Android conectado/autorizado via adb."
}

$apk = Join-Path $PSScriptRoot "app\build\outputs\apk\debug\app-debug.apk"
& $adb install -r $apk
Write-Host "APK instalado no aparelho conectado."
