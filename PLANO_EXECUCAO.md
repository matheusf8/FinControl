# FinControl — Plano de Execução

Projeto pessoal: sistema de controle financeiro que roda **local, como programa de desktop** (um `.exe`, sem instalar nada, sem publicar nada na internet).
Stack: **React (Vite) → FastAPI → SQLite**, empacotado num executável único com PyInstaller + pywebview.
Repositório: `github.com/matheusf8/sistema-financeiro` — pode ficar **privado**, é só backup do código-fonte, não precisa publicar nada.

## Status atual (2026-08-07)

**Sprints 1–8 concluídas — projeto fechado e em uso real.** MVP funcional completo — auth, contas/categorias/transações, dashboard com gráficos, cartões com parcelamento, metas, modo escuro, rate limiting, responsividade mobile, e empacotado num `.exe` de verdade (janela nativa, sem terminal, ícone próprio). 64 testes de backend + 13 de frontend (todos verdes). Commits locais no `main` (falta só `git push`, que é manual — ver seção "Fluxo de trabalho").

**Testado de ponta a ponta:** `FinControl.exe` rodando de uma pasta fora do ambiente de dev (simulando outro PC) — abre a janela, cria `fincontrol.db` e `.env` sozinho, backend responde, frontend carrega e navega certinho.

**Cópia em uso real do usuário:** `C:\Users\mathe\OneDrive\Desktop\area_trabalho\FinControl\` (ele prefere manter tudo dentro de `area_trabalho`, não direto na raiz da Área de Trabalho). Ver "Pós-lançamento" abaixo pra como atualizar essa cópia sem perder dados.

---

## Stack técnica

**Frontend**
- React + Vite + TypeScript
- TailwindCSS v4 (estilo, dark mode por classe com toggle manual)
- React Router (rotas)
- React Query (dados do servidor) + Zustand (estado local/auth/tema, persistidos no localStorage)
- React Hook Form + Zod (formulários e validação)
- Recharts (gráficos do dashboard)
- Build final: arquivos estáticos (`npm run build`), servidos pelo próprio backend — não roda mais como servidor de dev separado no produto final

**Backend**
- Python 3.12 + FastAPI
- SQLAlchemy 2.0 + Alembic (models e migrations, batch mode habilitado pro SQLite suportar ALTER/CHECK constraint)
- Pydantic v2 (schemas)
- JWT (access + refresh token) com **bcrypt direto** para hash de senha (não passlib — passlib 1.7.4 é incompatível com bcrypt novo, bug conhecido sem correção)
- Arquitetura em camadas: `routers → services → repositories → models/schemas`
- Rate limiting básico em memória no login (5 tentativas erradas = bloqueio de 5 min, por e-mail)

**Banco de dados**
- **SQLite** — um arquivo `.db` local, sem servidor separado (trocamos PostgreSQL por isso: mais simples de empacotar num `.exe`, e o app é de uso pessoal/single-user, então não perde nada relevante)

**Empacotamento final (em vez de Docker)**
- **pywebview** — abre o app numa janela nativa do Windows (sem precisar de navegador aberto)
- **PyInstaller** — empacota o backend Python (FastAPI + Uvicorn + SQLite) num `.exe` único, sem precisar de Python instalado na máquina
- Resultado: uma pasta com `FinControl.exe` + arquivos de suporte + `fincontrol.db`, portátil — copia pra qualquer PC Windows e roda

**Testes**
- Backend: pytest + httpx — 64 testes (auth, contas, categorias, transações, dashboard, cartões/parcelamento, metas)
- Frontend: Vitest + React Testing Library — 13 testes (fluxo de auth/rotas protegidas + utilitário de valores monetários)
- Validação manual no navegador em toda sprint, além dos testes automatizados (pegou bugs reais que os testes não cobriam)

**CI**
- GitHub Actions: roda lint + testes a cada push (só validação, não publica nada, não builda o `.exe` automaticamente por enquanto)

---

## Estrutura de pastas atual

```
sistema-financeiro/
├── backend/
│   ├── app/
│   │   ├── core/          # config, security (JWT/bcrypt), rate_limit, database, dependencies
│   │   ├── models/        # SQLAlchemy: User, Account, Category, Transaction, Card, Goal
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── repositories/  # acesso ao banco
│   │   ├── services/      # regras de negócio
│   │   ├── routers/       # auth, accounts, categories, transactions, dashboard, cards, goals
│   │   ├── static/        # build do frontend entra aqui na hora de empacotar (Sprint 8)
│   │   └── main.py
│   ├── alembic/versions/  # 5 migrations aplicadas
│   ├── tests/              # 63 testes
│   ├── requirements.txt
│   └── fincontrol.db      # banco SQLite (fora do git)
├── frontend/
│   ├── src/
│   │   ├── components/    # AppLayout, ProtectedRoute, ThemeToggle
│   │   ├── pages/          # Login, Register, Dashboard, Accounts, Categories, Transactions, Cards, Goals
│   │   ├── services/       # api.ts (axios+interceptor) + um service por domínio
│   │   ├── store/          # authStore, themeStore (zustand)
│   │   └── types/
│   └── package.json
├── desktop/                 # empacotamento final
│   ├── launcher.py          # abre a janela pywebview + sobe o backend
│   ├── build.spec           # config do PyInstaller
│   ├── icon.ico              # ícone do FinControl
│   └── dist/FinControl/      # gerado pelo PyInstaller (fora do git)
├── docs/                    # documento mestre, ADRs, etc.
├── .github/workflows/ci.yml
├── .env.example
└── README.md
```

---

## Estratégia: MVP primeiro

O documento mestre original cobre 13 capítulos e recursos avançados (Open Finance, IA). Para não travar o projeto, a ordem foi: **MVP funcional completo primeiro, extras depois**. Cartões/parcelamento entraram antes de metas porque têm mais valor de portfólio (mostram lógica de negócio mais complexa).

---

## Sprints

### ✅ Sprint 1 — Setup do projeto
Backend FastAPI + frontend Vite/React, stack SQLite, CI básico. Commit `b115d69`.

### ✅ Sprint 2 — Backend: fundação + autenticação
Model `User`, JWT (access+refresh) com bcrypt, endpoints de registro/login/refresh/me. 12 testes. Commit `b594200`.

### ✅ Sprint 3 — Frontend: fundação + autenticação
Login/cadastro (RHF+Zod), rotas protegidas, interceptor de token com refresh automático. Validado no navegador. Commit `890b7e6`.

### ✅ Sprint 4 — Núcleo financeiro: contas, categorias e transações
Models `Account`, `Category`, `Transaction`. CRUD completo + telas + filtros. 28 testes. Commit `d314c15`.

### ✅ Sprint 5 — Dashboard e relatórios
Agregações (saldo, gastos por categoria, evolução mensal) + gráficos Recharts. 35 testes. Commit `52984f0`.

### ✅ Sprint 6 — Cartões e parcelamento
Model `Card` + `Transaction` estendida (parcelas, sem model `Installment` separado — decisão de design pra reaproveitar toda a infra de listagem/dashboard já existente). Lógica de fechamento/vencimento, divisão com ajuste de arredondamento. 50 testes. Commit `6e3bc82`.

### ✅ Sprint 7 — Metas + qualidade
Model `Goal` com progresso visual, rate limiting no login, aviso de SECRET_KEY padrão, responsividade mobile testada em 375px. 63 testes. Commit `887118b`.

### ✅ Sprint 8 — Empacotamento em .exe
- Build do frontend copiado pra `backend/app/static/`; fallback de SPA no FastAPI (rotas do React Router funcionam com reload direto, sem 404)
- `config.py` ajustado pra achar `fincontrol.db`/`.env` do lado do `.exe` (não dentro da pasta interna do PyInstaller) — gera `SECRET_KEY` sozinho na primeira execução
- `database.py`: `init_db()` cria o schema sozinho num banco novo (sem precisar rodar Alembic manualmente — o `.exe` não tem terminal)
- `desktop/launcher.py`: sobe o FastAPI (Uvicorn) numa thread + abre janela pywebview; log de diagnóstico em `launcher.log`
- `desktop/build.spec` + PyInstaller (modo `--onedir`, sem terminal, ícone próprio): gera `FinControl.exe`
- Testado rodando de uma pasta fora do ambiente de dev (simulando "outro PC"): abre, cria banco+`.env` sozinho, backend responde, frontend carrega
- **Aceite:** clicar em `FinControl.exe` abre o app numa janela, sem terminal, sem instalar nada, com os dados salvos em `fincontrol.db` na mesma pasta ✅

---

## Pós-lançamento (uso real, depois da Sprint 8)

O usuário já está usando o `.exe` de verdade e reportando problemas de uso real — sinal de que o projeto cumpriu o objetivo. Fixes aplicados até agora:

- **`8e8eb2e`** — campos de valor (contas, transações, cartões, metas) só aceitavam formato internacional (`1356.92`), rejeitando o formato brasileiro (`1.356,92`) como se estivesse vazio. Criado `frontend/src/lib/money.ts` (`parseMoneyInput`/`toApiAmount`), aplicado em todas as telas com campo de dinheiro. 7 testes novos.
- **`429f16c`** — acesso pelo celular na mesma rede Wi-Fi: `launcher.py` liga o Uvicorn em `0.0.0.0` (porta fixa 8756) em vez de `127.0.0.1`, escreve `Acesse pelo celular.txt` do lado do `.exe` a cada abertura com o IP local atual. Usuário escolheu essa opção (grátis, rede local) em vez de hospedar na internet (pago, mudaria a proposta 100% local do projeto).
- **`5655e3e`** — **bug sério no meu próprio processo, não no app**: toda atualização eu apagava a pasta inteira da cópia em uso (`Remove-Item -Recurse -Force`) e recopiava do zero, o que apagava `fincontrol.db` e `.env` junto com o programa. Criado `desktop/update-desktop-copy.ps1`: troca só `FinControl.exe` + `_internal`, nunca toca no banco/config, e ainda faz backup timestamped em `backups/` antes de qualquer coisa. **Usar sempre esse script a partir de agora, nunca mais copiar a pasta inteira por cima de uma cópia em uso.**

**Nota:** o susto do "banco sumiu" foi falso alarme — o usuário tinha movido a pasta de `Desktop\FinControl` pra `Desktop\area_trabalho\FinControl` (prefere manter tudo junto), não foi apagado por antivírus nem nada. Mas o risco real (meu processo apagar dados numa atualização futura) era genuíno e ficou corrigido de qualquer forma.

---

## Fluxo de trabalho: quem faz o quê

- **Eu (assistente) edito os arquivos e rodo git direto nesta pasta** (código, docs, configs, `add`/`commit`) — isso funciona normalmente (confirmado em 2026-08-07).
- **`git push`** ainda depende de você (autenticação com o GitHub não está disponível pro assistente).
- Nota histórica: um `.git/index.lock` órfão (de um commit interrompido) chegou a travar `add`/`commit` uma vez — não é uma limitação real do OneDrive, só um lock que precisou ser removido manualmente. Se acontecer de novo, é só apagar `.git/index.lock` (confirmando antes que não há processo `git` rodando).

---

## Portabilidade entre computadores

Como o banco agora é **SQLite** (um arquivo `.db` dentro da própria pasta do projeto, não um volume escondido do Docker), a portabilidade fica bem mais simples do que era com Postgres:

- Essa pasta (`sistema-financeiro`) já está dentro do **OneDrive** (`Desktop\area_trabalho\pasta\...`), que sincroniza sozinho com a nuvem e com qualquer outro PC logado na mesma conta Microsoft.
- Depois de empacotado (Sprint 8), a pasta final (`FinControl.exe` + `fincontrol.db`) pode ficar dentro dessa mesma estrutura sincronizada — então ao trocar de computador, é só logar com a mesma conta Microsoft, esperar o OneDrive baixar os arquivos, e o programa (com todos os dados) já está lá.
- Também dá pra copiar a pasta inteira pra um **pen drive** a qualquer momento como backup extra ou pra usar num PC sem essa conta Microsoft — funciona igual, é só uma pasta portátil.
- **Cuidado:** não abrir o mesmo `FinControl.exe` em dois PCs ao mesmo tempo — o SQLite trava se dois processos tentarem escrever no arquivo ao mesmo tempo. Combina bem com o uso real (um PC de cada vez).

Isso substitui o processo antigo de backup/restore manual com `pg_dump`/`psql` — não é mais necessário.

---

## Depois do MVP (backlog futuro)
- Open Finance (integração bancária)
- Notificações (vencimento de fatura, metas)
- IA para análise de gastos

Esses ficam fora dos 8 sprints — só entram se sobrar tempo/energia depois do projeto "fechado".

---

## Checklist final (do documento mestre)
`[x] Login [x] Cadastro [x] JWT [x] CRUD Receitas [x] CRUD Despesas [x] Dashboard [x] Gráficos [x] Cartões [x] Parcelamento [x] Metas [x] Empacotamento .exe [x] Testes [x] README`

---

## 🎉 Projeto fechado

Todas as 8 sprints do MVP concluídas. O FinControl roda como programa de desktop de verdade — `.exe` com janela própria, ícone próprio, sem terminal, sem instalar nada, 100% local. Backlog futuro (Open Finance, notificações, IA) fica pra depois, se um dia fizer sentido continuar.
