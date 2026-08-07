# FinControl

Sistema de controle financeiro pessoal — programa de desktop, uso local, sem publicação na internet.

**Stack:** React (Vite) + FastAPI + SQLite, empacotado como executável único (`.exe`) com PyInstaller + pywebview.

> 🚧 Em construção. Veja o [plano de execução](./PLANO_EXECUCAO.md) completo.

## Como rodar (desenvolvimento)

Backend:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Como gerar o `.exe` (produção)

Ver Sprint 8 do [plano de execução](./PLANO_EXECUCAO.md) — build do frontend + PyInstaller geram uma pasta portátil com `FinControl.exe`, sem precisar instalar nada na máquina de destino.

## Estrutura

- `backend/` — API em FastAPI + banco SQLite local
- `frontend/` — interface em React
- `desktop/` — empacotamento final (pywebview + PyInstaller)
- `docs/` — documentação do projeto
