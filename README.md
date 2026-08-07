# FinControl

Sistema de controle financeiro pessoal — programa de desktop, uso local, sem publicação na internet.

**Stack:** React (Vite) + FastAPI + SQLite, empacotado como executável único (`.exe`) com PyInstaller + pywebview.

> ✅ MVP completo (Sprints 1–7): autenticação, contas, categorias, transações, dashboard com gráficos, cartões com parcelamento, metas e modo escuro. Empacotamento final em `.exe` em andamento (Sprint 8). Veja o [plano de execução](./PLANO_EXECUCAO.md) completo.

## Funcionalidades

- **Autenticação** — cadastro, login, JWT com refresh automático, rate limiting contra força bruta
- **Contas** — corrente, poupança, carteira, investimento
- **Categorias e transações** — receitas/despesas categorizadas, com filtros por conta/categoria/tipo/período
- **Dashboard** — saldo total e por conta, gastos por categoria (pizza), evolução mensal (linha)
- **Cartões de crédito** — compras parceladas com cálculo automático de fatura (respeitando dia de fechamento), fatura por mês
- **Metas financeiras** — com barra de progresso e registro de contribuições
- **Modo escuro** — com toggle manual, persistido
- **Responsivo** — funciona também no celular

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

## Como rodar os testes

Backend (63 testes):
```bash
cd backend
.venv\Scripts\python.exe -m pytest
```

Frontend (6 testes):
```bash
cd frontend
npm run test
```

## Como gerar o `.exe` (produção)

Ver Sprint 8 do [plano de execução](./PLANO_EXECUCAO.md) — build do frontend + PyInstaller geram uma pasta portátil com `FinControl.exe`, sem precisar instalar nada na máquina de destino.

## Estrutura

- `backend/` — API em FastAPI + banco SQLite local
- `frontend/` — interface em React
- `desktop/` — empacotamento final (pywebview + PyInstaller)
- `docs/` — documentação do projeto
