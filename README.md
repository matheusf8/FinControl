# FinControl

Sistema de controle financeiro pessoal — programa de desktop, uso local, sem publicação na internet.

**Stack:** React (Vite) + FastAPI + SQLite, empacotado como executável único (`.exe`) com PyInstaller + pywebview.

> ✅ **MVP completo (Sprints 1–8):** autenticação, contas, categorias, transações, dashboard com gráficos, cartões com parcelamento, metas, modo escuro e empacotamento em `.exe`. Veja o [plano de execução](./PLANO_EXECUCAO.md) completo.

## Funcionalidades

- **Autenticação** — cadastro, login, JWT com refresh automático, rate limiting contra força bruta
- **Contas** — corrente, poupança, carteira, investimento
- **Categorias e transações** — receitas/despesas categorizadas, com filtros por conta/categoria/tipo/período
- **Dashboard** — saldo total e por conta, gastos por categoria (pizza), evolução mensal (linha)
- **Cartões de crédito** — compras parceladas com cálculo automático de fatura (respeitando dia de fechamento), fatura por mês
- **Metas financeiras** — com barra de progresso e registro de contribuições
- **Modo escuro** — com toggle manual, persistido
- **Responsivo** — funciona também no celular
- **Programa de desktop** — roda como `.exe`, sem terminal, sem instalar nada

## Como usar (só abrir o programa)

Se você já tem a pasta `FinControl/` gerada (ver "Como gerar o `.exe`" abaixo), é só:

1. Clicar duas vezes em `FinControl.exe`
2. Pronto — abre numa janela, sem terminal. Na primeira vez, ele cria sozinho o banco de dados (`fincontrol.db`) e a chave de segurança (`.env`) do lado do `.exe`
3. Pra usar em outro PC (ou guardar no pen drive), é só copiar a pasta `FinControl/` inteira — os dados vão junto

## Como usar pelo celular (mesma rede Wi-Fi)

Com o FinControl aberto no PC, ele também aceita acesso de outros aparelhos na mesma rede Wi-Fi:

1. Abra a pasta do programa e leia o arquivo **`Acesse pelo celular.txt`** (criado/atualizado toda vez que o programa abre) — ele tem o endereço certo pra digitar
2. No celular (na mesma Wi-Fi do PC), abra o navegador e acesse esse endereço (algo como `http://192.168.x.x:8756`)
3. Faça login normalmente — a sessão do celular é separada da sessão da janela do PC
4. Na primeira vez, o Windows pode perguntar se libera o FinControl na rede — clique em **"Permitir acesso"**

Só funciona com o PC ligado e o programa aberto, e só dentro da mesma rede Wi-Fi (não funciona longe de casa/com dados móveis — isso exigiria hospedar o backend na internet, o que muda a proposta 100% local/privada do projeto).

## Como rodar (desenvolvimento)

Backend:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Como rodar os testes

Backend (64 testes):
```bash
cd backend
.venv\Scripts\python.exe -m pytest
```

Frontend (6 testes):
```bash
cd frontend
npm run test
```

## Como gerar o `.exe`

```powershell
# 1. Build do frontend
cd frontend
npm run build

# 2. Copia o build pra dentro do backend (o FastAPI serve ele)
Remove-Item -Recurse -Force ..\backend\app\static\* -ErrorAction SilentlyContinue
Copy-Item -Recurse dist\* ..\backend\app\static\

# 3. Gera o executável (pasta portátil desktop/dist/FinControl/)
cd ..\desktop
..\backend\.venv\Scripts\pyinstaller.exe build.spec --noconfirm
```

O resultado fica em `desktop/dist/FinControl/` — a pasta inteira é o programa (`FinControl.exe` + arquivos de suporte).

**Pra atualizar uma cópia já em uso** (que já tem `fincontrol.db` com dados de verdade), **não copie a pasta inteira por cima** — isso apaga o banco. Use o script que só troca o programa, preservando os dados, e ainda faz backup automático:

```powershell
# Edite a variável $dst dentro do script pra apontar pra sua cópia em uso
.\update-desktop-copy.ps1
```

Se algo der errado ao abrir o `.exe` (não deveria, mas caso aconteça), o diagnóstico fica em `launcher.log`, criado do lado do `.exe`.

## Estrutura

- `backend/` — API em FastAPI + banco SQLite local
- `frontend/` — interface em React
- `desktop/` — empacotamento final (`launcher.py`, `build.spec`, `icon.ico`)
- `docs/` — documentação do projeto
