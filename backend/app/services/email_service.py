"""Envio de e-mail transacional via Resend (https://resend.com/docs/api-reference/emails/send-email).

Sem infra própria de e-mail de propósito — é a mesma lógica de não trazer
Redis pro rate limit (ver app/core/rate_limit.py): app pessoal, não vale a
complexidade de rodar SMTP/fila. Resend tem plano grátis e API HTTP simples
(um POST), então só chamamos direto com httpx.
"""
import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


class EmailSendError(Exception):
    """Falha ao chamar a API do Resend (rede, chave inválida, etc.)."""


def send_email(*, to: str, subject: str, html: str) -> None:
    # Sem chave configurada (dev local sem .env, testes, ou instalação do
    # .exe que ninguém configurou ainda): loga e segue em frente, sem
    # quebrar o fluxo de quem chamou (forgot-password sempre responde 204
    # de qualquer forma, pra não revelar se o e-mail existe).
    if not settings.resend_api_key:
        log.warning("RESEND_API_KEY não configurada — e-mail '%s' pra %s não foi enviado", subject, to)
        return

    try:
        response = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.mail_from, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        log.exception("Falha ao enviar e-mail via Resend (assunto: %s)", subject)
        raise EmailSendError()
