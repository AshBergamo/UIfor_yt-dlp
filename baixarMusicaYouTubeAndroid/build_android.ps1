$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot 'setup_android.ps1')

if (-not (Test-Path -LiteralPath ".\gradlew.bat")) {
    throw "gradlew.bat não encontrado. Abra esta pasta no Android Studio ou adicione o Gradle Wrapper."
}

& .\gradlew.bat assembleDebug
if ($LASTEXITCODE -ne 0) { throw 'Gradle assembleDebug falhou.' }

$apk = Join-Path $PSScriptRoot "app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path -LiteralPath $apk) {
    $entries = & tar -tf $apk
    $requiredEntries = @(
        "lib/arm64-v8a/libffmpeg.so",
        "lib/arm64-v8a/libpython.so",
        "lib/arm64-v8a/libqjs.so"
    )
    foreach ($entry in $requiredEntries) {
        if ($entries -notcontains $entry) {
            throw "APK gerado sem dependência obrigatória: $entry"
        }
    }

    $sizeMb = [Math]::Round((Get-Item -LiteralPath $apk).Length / 1MB, 1)
    Write-Host "APK gerado em: $apk"
    Write-Host "Tamanho: $sizeMb MB"
    Write-Host "Verificação OK: FFmpeg/yt-dlp Android encontrados no APK."
}
