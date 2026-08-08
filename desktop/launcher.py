"""Ponto de entrada do FinControl empacotado como .exe.

Sobe o backend FastAPI (Uvicorn) numa thread em segundo plano e abre uma
janela nativa do Windows (pywebview) apontando pra ele — sem terminal, sem
precisar abrir navegador separado. É isso que o PyInstaller empacota.

Também aceita conexões de outros aparelhos na mesma rede Wi-Fi (celular,
por exemplo) — ver `_write_lan_access_file`.
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
PREFERRED_PORT = 8756  # porta fixa de propósito — fácil de repetir no celular

_log_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
logging.basicConfig(
    filename=_log_dir / "launcher.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("launcher")
# Sem janela de terminal (Sprint 8), esse launcher.log é o único jeito de
# diagnosticar um problema — por isso o try/except em cada etapa abaixo.


def _preferred_port() -> int:
    """Tenta a porta fixa (fácil de repetir no celular). Se estiver ocupada
    (outra instância, ou algo travado), cai pra uma porta livre qualquer —
    nesse caso o celular precisa conferir `Acesse pelo celular.txt` de novo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", PREFERRED_PORT))
            return PREFERRED_PORT
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", 0))
        return sock.getsockname()[1]


def _lan_ip() -> str:
    """IP deste PC na rede local (Wi-Fi/cabo) — o endereço que o celular usa
    pra achar o programa. Não manda nada de verdade pro 8.8.8.8: o `connect`
    de um socket UDP só decide, localmente, qual interface de rede seria
    usada — nenhum pacote sai da máquina."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def _write_lan_access_file(ip: str, port: int) -> None:
    """Arquivo de texto do lado do .exe com o endereço pra abrir no celular —
    reescrito toda vez que o programa abre, porque o IP local pode mudar de
    uma conexão de Wi-Fi pra outra."""
    content = (
        "FinControl - acesso pelo celular\n"
        "=================================\n\n"
        "1. O celular precisa estar na MESMA rede Wi-Fi que este computador.\n"
        "2. Com o FinControl aberto aqui no PC, abra o navegador do celular e acesse:\n\n"
        f"   http://{ip}:{port}\n\n"
        "3. Faca login normalmente (a sessao do celular fica separada da do PC).\n\n"
        "Esse endereco pode mudar se o computador reconectar na rede - se parar\n"
        "de funcionar, abra o FinControl de novo aqui no PC e confira este\n"
        "arquivo outra vez (ele se atualiza sozinho a cada abertura).\n"
    )
    try:
        (_log_dir / "Acesse pelo celular.txt").write_text(content, encoding="utf-8")
    except Exception:
        log.exception("Não consegui escrever o arquivo de acesso pelo celular")


def _run_server(port: int) -> None:
    try:
        log.info("Servidor: iniciando na porta %s (aceita conexões da rede local)", port)
        # 0.0.0.0 (não 127.0.0.1): aceita conexão de outros aparelhos na
        # mesma rede Wi-Fi, não só desta máquina.
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
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

    port = _preferred_port()
    lan_ip = _lan_ip()
    log.info("Porta escolhida: %s | IP na rede local: %s", port, lan_ip)
    _write_lan_access_file(lan_ip, port)
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
