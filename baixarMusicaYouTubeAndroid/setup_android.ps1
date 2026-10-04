$ErrorActionPreference = 'Stop'
if (-not $env:JAVA_HOME) {
    $jdk17 = Join-Path $env:ProgramFiles 'Java\jdk-17'
    if (Test-Path -LiteralPath $jdk17) { $env:JAVA_HOME = $jdk17 }
}
if (-not $env:JAVA_HOME) { throw 'Defina JAVA_HOME para um JDK 17.' }
$javaExe = Join-Path $env:JAVA_HOME 'bin\java.exe'
$javaVersion = & $javaExe --version | Out-String
if ($LASTEXITCODE -ne 0 -or $javaVersion -notmatch '(?m)^(openjdk|java) 17\.') { throw 'Este build usa JDK 17. Ajuste JAVA_HOME.' }
if (-not $env:ANDROID_HOME) {
    $defaultSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    if (Test-Path -LiteralPath $defaultSdk) { $env:ANDROID_HOME = $defaultSdk }
}
if (-not $env:ANDROID_HOME) { throw 'Defina ANDROID_HOME para o Android SDK.' }
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
if (-not $env:GRADLE_USER_HOME) {
    $env:GRADLE_USER_HOME = Join-Path (Split-Path -Parent $PSScriptRoot) 'work\gradle'
}
