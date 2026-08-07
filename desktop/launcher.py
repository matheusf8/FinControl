"""Ponto de entrada do FinControl empacotado como .exe.

Sobe o backend FastAPI (Uvicorn) numa thread em segundo plano e abre uma
janela nativa do Windows (pywebview) apontando pra ele — sem terminal, sem
precisar abrir navegador separado. É isso que o PyInstaller empacota.
"""
import logging
import socket
import sys
import threading
from pathlib import Path

import uvicorn
import webview

# Rodando direto (`python desktop/launcher.py`, sem empacotar ainda), o
# pacote `app` do backend não está no sys.path por padrão — adiciona a pasta
# backend/. Empacotado pelo PyInstaller isso não é necessário (o spec já
# inclui o pacote `app` na análise).
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.database import init_db  # noqa: E402
from app.main import app  # noqa: E402

WINDOW_TITLE = "FinControl"
WINDOW_SIZE = (1280, 800)
MIN_SIZE = (960, 640)

_log_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
logging.basicConfig(
    filename=_log_dir / "launcher.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("launcher")
# Sem janela de terminal (Sprint 8), esse launcher.log é o único jeito de
# diagnosticar um problema — por isso o try/except em cada etapa abaixo.


def _free_port() -> int:
    """Porta livre na máquina — evita colidir se sobrar algo travado na 8000
    (ex: uma instância anterior que não fechou direito)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run_server(port: int) -> None:
    try:
        log.info("Servidor: iniciando na porta %s", port)
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
        log.info("Servidor: uvicorn.run retornou (encerrado)")
    except Exception:
        log.exception("Servidor: crashou")


def main() -> None:
    log.info("=== FinControl iniciando ===")
    try:
        init_db()
        log.info("init_db: ok")
    except Exception:
        log.exception("init_db: falhou")
        raise

    port = _free_port()
    log.info("Porta escolhida: %s", port)
    threading.Thread(target=_run_server, args=(port,), daemon=True).start()

    log.info("Criando janela pywebview...")
    webview.create_window(
        WINDOW_TITLE,
        f"http://127.0.0.1:{port}",
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        min_size=MIN_SIZE,
    )
    log.info("Chamando webview.start()...")
    try:
        webview.start(debug=False)
    except Exception:
        log.exception("webview.start: crashou")
        raise
    log.info("webview.start retornou (janela fechada)")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Sem terminal (console=False), esse é o único registro que sobra se
        # algo der errado antes mesmo da janela abrir.
        log.exception("Falha fatal ao iniciar o FinControl")
