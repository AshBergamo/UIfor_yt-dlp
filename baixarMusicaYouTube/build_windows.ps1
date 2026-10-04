$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Crie o ambiente virtual na raiz: py -3.11 -m venv .venv'
}
Push-Location $PSScriptRoot
try {
    & $pythonExe -m pip install -r (Join-Path $repoRoot 'requirements-build.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências.' }
    & $pythonExe -m PyInstaller --noconfirm baixar_musica_qt.spec
    if ($LASTEXITCODE -ne 0) { throw 'Falha no PyInstaller.' }
} finally {
    Pop-Location
}
