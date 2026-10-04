$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot 'setup_android.ps1')

if (-not (Test-Path -LiteralPath ".\gradlew.bat")) {
    throw "gradlew.bat nao encontrado. Abra esta pasta no Android Studio ou adicione o Gradle Wrapper."
}

$keytool = Get-Command keytool -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
if (-not $keytool) {
    $androidStudioKeytool = Join-Path $env:ProgramFiles "Android\Android Studio\jbr\bin\keytool.exe"
    if (Test-Path -LiteralPath $androidStudioKeytool) {
        $keytool = $androidStudioKeytool
    }
}
if (-not $keytool) {
    throw "keytool nao encontrado. Instale o Android Studio/JDK ou coloque keytool no PATH."
}

$sdk = $env:ANDROID_HOME
if (-not $sdk -or -not (Test-Path -LiteralPath $sdk)) {
    throw "Android SDK nao encontrado. Configure ANDROID_HOME ou instale o SDK pelo Android Studio."
}

$buildToolsDir = Join-Path $sdk "build-tools"
$buildTools = Get-ChildItem -LiteralPath $buildToolsDir -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $buildTools) {
    throw "Build Tools do Android SDK nao encontrados em $buildToolsDir."
}

$apksigner = Join-Path $buildTools.FullName "apksigner.bat"
if (-not (Test-Path -LiteralPath $apksigner)) {
    throw "apksigner.bat nao encontrado em $($buildTools.FullName)."
}

$signingDir = Join-Path $PSScriptRoot "release-signing"
$keystore = Join-Path $signingDir "baixar-musica-youtube-release.jks"
$propertiesFile = Join-Path $signingDir "keystore.properties"
$alias = "baixar-musica-youtube"

New-Item -ItemType Directory -Force -Path $signingDir | Out-Null

if (-not (Test-Path -LiteralPath $propertiesFile)) {
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $bytes = New-Object byte[] 24
        $rng.GetBytes($bytes)
        $password = [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
    } finally {
        $rng.Dispose()
    }

    & $keytool -genkeypair `
        -v `
        -keystore $keystore `
        -storetype PKCS12 `
        -alias $alias `
        -keyalg RSA `
        -keysize 2048 `
        -validity 10000 `
        -storepass $password `
        -keypass $password `
        -dname "CN=Baixar Musica YouTube, OU=AI PyTorch, O=AI PyTorch, L=Local, S=Local, C=BR" `
        -noprompt
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar keystore. Nenhuma configuração de assinatura foi gravada.' }

    @(
        "storeFile=release-signing/baixar-musica-youtube-release.jks"
        "storePassword=$password"
        "keyAlias=$alias"
        "keyPassword=$password"
    ) | Set-Content -LiteralPath $propertiesFile -Encoding ASCII

    Write-Host "Keystore release criada em: $keystore"
    Write-Host "IMPORTANTE: guarde a pasta release-signing. Sem ela, futuras atualizacoes nao instalam por cima desta release."
}

& .\gradlew.bat assembleRelease
if ($LASTEXITCODE -ne 0) { throw 'Gradle assembleRelease falhou.' }

$releaseApk = Join-Path $PSScriptRoot "app\build\outputs\apk\release\app-release.apk"
if (-not (Test-Path -LiteralPath $releaseApk)) {
    throw "APK release nao foi encontrado em $releaseApk."
}

$outputDir = Join-Path $PSScriptRoot "Output"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$finalApk = Join-Path $outputDir "BaixarMusicaYouTube_Android_v3.3_release.apk"
Copy-Item -LiteralPath $releaseApk -Destination $finalApk -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$apk = [System.IO.Compression.ZipFile]::OpenRead($finalApk)
try {
    $entries = $apk.Entries | ForEach-Object { $_.FullName }
    $requiredEntries = @(
        "lib/arm64-v8a/libffmpeg.so",
        "lib/arm64-v8a/libpython.so",
        "lib/arm64-v8a/libqjs.so"
    )
    foreach ($entry in $requiredEntries) {
        if ($entries -notcontains $entry) {
            throw "APK gerado sem dependencia obrigatoria: $entry"
        }
    }
} finally {
    $apk.Dispose()
}

& $apksigner verify --verbose --print-certs $finalApk
if ($LASTEXITCODE -ne 0) { throw 'Verificação de assinatura falhou.' }

$sizeMb = [Math]::Round((Get-Item -LiteralPath $finalApk).Length / 1MB, 1)
Write-Host "APK release assinado gerado em: $finalApk"
Write-Host "Tamanho: $sizeMb MB"
Write-Host "Verificacao OK: APK assinado e FFmpeg/yt-dlp Android encontrados."
