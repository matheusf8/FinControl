"""Rate limiting simples em memória pro endpoint de login — evita força bruta
de senha. Em memória (não Redis) de propósito: é um app local single-process,
não faria sentido trazer infra externa só pra isso."""
import time
from collections import defaultdict

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60  # tentativas fora dessa janela não contam mais
LOCKOUT_SECONDS = 5 * 60  # tempo bloqueado depois de estourar o limite

_attempts: dict[str, list[float]] = defaultdict(list)
_locked_until: dict[str, float] = {}


def is_locked(key: str) -> float | None:
    """Retorna quantos segundos faltam pro desbloqueio, ou None se liberado."""
    locked_until = _locked_until.get(key)
    if locked_until is None:
        return None
    remaining = locked_until - time.monotonic()
    if remaining <= 0:
        _locked_until.pop(key, None)
        _attempts.pop(key, None)
        return None
    return remaining


def register_failure(key: str) -> None:
    now = time.monotonic()
    attempts = [t for t in _attempts[key] if now - t <= WINDOW_SECONDS]
    attempts.append(now)
    _attempts[key] = attempts
    if len(attempts) >= MAX_ATTEMPTS:
        _locked_until[key] = now + LOCKOUT_SECONDS


def register_success(key: str) -> None:
    _attempts.pop(key, None)
    _locked_until.pop(key, None)
