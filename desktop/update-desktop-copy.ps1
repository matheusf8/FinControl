# Atualiza a copia de uso do FinControl (fora da pasta do projeto) com um
# build novo do PyInstaller, SEM MEXER no banco de dados / configuracao do
# usuario. So troca o programa em si (FinControl.exe + _internal).
#
# Uso: rode depois de gerar um build novo em desktop/dist/FinControl
#   powershell -File desktop\update-desktop-copy.ps1

$ErrorActionPreference = "Stop"

$src = Join-Path $PSScriptRoot "dist\FinControl"
$dst = "C:\Users\mathe\OneDrive\Desktop\area_trabalho\FinControl"

if (-not (Test-Path $src)) {
    throw "Build nao encontrado em $src - rode o PyInstaller primeiro (build.spec)."
}

# Fecha a instancia rodando, se houver (senao o .exe fica travado pra sobrescrever)
Get-Process -Name FinControl -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Backup do banco antes de mexer em qualquer coisa, mesmo so trocando exe/_internal
# abaixo - defesa extra, nunca custa ter uma copia a mais.
$dbPath = Join-Path $dst "fincontrol.db"
if (Test-Path $dbPath) {
    $backupDir = Join-Path $PSScriptRoot "..\backups"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item $dbPath (Join-Path $backupDir "fincontrol_$stamp.db")
    Write-Host "Backup do banco salvo em backups\fincontrol_$stamp.db"
}

New-Item -ItemType Directory -Force -Path $dst | Out-Null

# So troca o PROGRAMA (exe + _internal) - NUNCA mexe em fincontrol.db, .env,
# launcher.log ou "Acesse pelo celular.txt", que ficam soltos do lado.
Copy-Item (Join-Path $src "FinControl.exe") $dst -Force
Remove-Item (Join-Path $dst "_internal") -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $src "_internal") $dst -Recurse -Force

Write-Host "FinControl atualizado em: $dst (dados do usuario preservados)"
