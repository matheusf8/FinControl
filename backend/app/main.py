"""Ponto de entrada da API FastAPI."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import accounts, auth, cards, categories, dashboard, transactions

app = FastAPI(title=settings.app_name)

# CORS liberado só pro frontend em dev (Vite); no .exe final, front e back
# são servidos pela mesma origem, então isso nem entra em jogo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])

# Serve o build do frontend (gerado no Sprint 8) se existir, na raiz "/".
# Em dev, o frontend roda separado via `npm run dev` (Vite), então essa pasta
# fica vazia e essa linha não faz nada.
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.exists() and any(_static_dir.iterdir()):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
