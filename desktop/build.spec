# -*- mode: python ; coding: utf-8 -*-
"""Spec do PyInstaller pro FinControl.

Gera uma pasta portátil (dist/FinControl/) com FinControl.exe — modo
--onedir de propósito (não --onefile): abre mais rápido, porque --onefile
precisa descompactar tudo num diretório temporário a cada execução.

Rodar de dentro de desktop/:
    ..\backend\.venv\Scripts\pyinstaller.exe build.spec
"""
from pathlib import Path

ROOT = Path(SPECPATH)  # pasta desktop/
BACKEND = ROOT.parent / "backend"

a = Analysis(
    [str(ROOT / "launcher.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=[
        (str(BACKEND / "app" / "static"), "app/static"),
    ],
    hiddenimports=[
        # uvicorn escolhe essas implementações dinamicamente (por string, em
        # runtime) — a análise estática do PyInstaller não enxerga esses
        # imports sozinha.
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.protocols.utils",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FinControl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Sem janela de terminal atrás (Aceite da Sprint 8) — diagnóstico de erro
    # fica em launcher.log ao lado do .exe (ver launcher.py) em vez de stdout.
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FinControl",
)
