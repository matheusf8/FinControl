# FinControl — Plano de Execução

Projeto pessoal: sistema de controle financeiro que roda **local, como programa de desktop** (um `.exe`, sem instalar nada, sem publicar nada na internet).
Stack: **React (Vite) → FastAPI → SQLite**, empacotado num executável único com PyInstaller + pywebview.
Repositório: `github.com/matheusf8/sistema-financeiro` — pode ficar **privado**, é só backup do código-fonte, não precisa publicar nada.

---

## Stack técnica

**Frontend**
- React + Vite + TypeScript
- TailwindCSS (estilo)
- React Router (rotas)
- React Query (dados do servidor) + Zustand (estado local/auth)
- React Hook Form + Zod (formulários e validação)
- Recharts (gráficos do dashboard)
- Build final: arquivos estáticos (`npm run build`), servidos pelo próprio backend — não roda mais como servidor de dev separado no produto final

**Backend**
- Python 3.12 + FastAPI
- SQLAlchemy 2.0 + Alembic (models e migrations)
- Pydantic v2 (schemas)
- JWT (access + refresh token) com passlib/bcrypt para hash de senha
- Arquitetura em camadas: `routers → services → repositories → models/schemas`

**Banco de dados**
- **SQLite** — um arquivo `.db` local, sem servidor separado (trocamos PostgreSQL por isso: mais simples de empacotar num `.exe`, e o app é de uso pessoal/single-user, então não perde nada relevante)

**Empacotamento final (em vez de Docker)**
- **pywebview** — abre o app numa janela nativa do Windows (sem precisar de navegador aberto)
- **PyInstaller** — empacota o backend Python (FastAPI + Uvicorn + SQLite) num `.exe` único, sem precisar de Python instalado na máquina
- Resultado: uma pasta com `FinControl.exe` + arquivos de suporte + `fincontrol.db`, portátil — copia pra qualquer PC Windows e roda

**Testes**
- Backend: pytest + httpx
- Frontend: Vitest + React Testing Library

**CI**
- GitHub Actions: roda lint + testes a cada push (só validação, não publica nada, não builda o `.exe` automaticamente por enquanto)

---

## Estrutura de pastas proposta

```
sistema-financeiro/
├── backend/
│   ├── app/
│   │   ├── core/          # config, segurança, JWT
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── repositories/  # acesso ao banco
│   │   ├── services/      # regras de negócio
│   │   ├── routers/       # endpoints REST
│   │   ├── static/        # build do frontend entra aqui na hora de empacotar
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── fincontrol.db      # banco SQLite (fora do git)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/       # cliente da API
│   │   └── store/
│   └── package.json
├── desktop/                 # empacotamento final
│   ├── launcher.py          # abre a janela pywebview + sobe o backend
│   └── build.spec           # config do PyInstaller
├── docs/                    # documento mestre, ADRs, etc.
├── .github/workflows/ci.yml
├── .env.example
└── README.md
```

---

## Estratégia: MVP primeiro

O documento mestre original cobre 13 capítulos e recursos avançados (Open Finance, IA). Para não travar o projeto, a ordem é: **MVP funcional completo primeiro, extras depois**. Cartões/parcelamento entram antes de metas porque têm mais valor de portfólio (mostram lógica de negócio mais complexa).

---

## Sprints

### Sprint 1 — Setup do projeto
- Criar repositório no GitHub (`matheusf8/sistema-financeiro`, pode ser privado), branch `main` protegida + `dev`
- Estrutura de pastas (backend/frontend), venv Python + `requirements.txt`, scaffold do Vite + dependências do frontend
- `.env.example`, `.gitignore`, README inicial
- GitHub Actions básico (roda lint em cada push)
- **Aceite:** backend sobe com `uvicorn app.main:app --reload` e frontend com `npm run dev`, ambos sem erro

### Sprint 2 — Backend: fundação + autenticação
- Modelo `User`, configuração do SQLAlchemy + Alembic (primeira migration) apontando pro SQLite
- Endpoints de registro, login, refresh token (JWT), hash de senha
- Middleware de autorização (rotas protegidas)
- Testes de auth com pytest
- **Aceite:** registro/login funcionando via Swagger (`/docs`), senha nunca em texto puro

### Sprint 3 — Frontend: fundação + autenticação
- Setup Vite + Tailwind + React Router
- Páginas de login/cadastro, cliente HTTP com interceptor de token
- Rotas protegidas, persistência de sessão
- **Aceite:** usuário consegue criar conta e logar pela interface, sem acesso a rotas protegidas deslogado

### Sprint 4 — Núcleo financeiro: contas, categorias e transações
- Modelos `Account`, `Category`, `Transaction` (receitas/despesas)
- CRUD completo (API + telas): criar conta, categorias, lançar receita/despesa
- Listagem com filtros (data, categoria, tipo)
- **Aceite:** usuário cadastra uma conta, categoriza e lança transações, vê a lista atualizada

### Sprint 5 — Dashboard e relatórios
- Endpoints de agregação (saldo, gastos por categoria, evolução mensal)
- Dashboard com gráficos (Recharts): pizza por categoria, linha de evolução, saldo por conta
- Filtros de período
- **Aceite:** dashboard reflete corretamente os dados lançados, com gráficos funcionais

### Sprint 6 — Cartões e parcelamento
- Modelos `Card`, `Installment`
- Lançamento de compra parcelada gerando parcelas futuras automaticamente
- Fatura do cartão por mês
- **Aceite:** uma compra em 3x gera 3 lançamentos corretos nos meses seguintes

### Sprint 7 — Metas + qualidade (não funcionais)
- Modelo `Goal`, CRUD de metas com progresso visual
- Cobertura de testes (backend e frontend) nos fluxos críticos
- Validações de entrada, tratamento de erros, responsividade da janela
- Revisão de segurança básica (variáveis sensíveis fora do código)
- **Aceite:** suite de testes passando no CI

### Sprint 8 — Empacotamento em .exe
- Build do frontend (`npm run build`) copiado pra dentro de `backend/app/static/`
- `desktop/launcher.py`: sobe o FastAPI (Uvicorn) em background + abre janela pywebview apontando pra ele
- `desktop/build.spec` + PyInstaller: gera `FinControl.exe` numa pasta portátil (`dist/FinControl/`)
- Testar rodando o `.exe` de uma pasta fora do ambiente de desenvolvimento (simulando "outro PC")
- README completo (como rodar em dev, como gerar o `.exe`, como usar)
- Seed de dados de demonstração opcional
- **Aceite:** clicar em `FinControl.exe` abre o app numa janela, sem terminal, sem instalar nada, com os dados salvos em `fincontrol.db` na mesma pasta

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
`[ ] Login [ ] Cadastro [ ] JWT [ ] CRUD Receitas [ ] CRUD Despesas [ ] Dashboard [ ] Gráficos [ ] Cartões [ ] Parcelamento [ ] Metas [ ] Empacotamento .exe [ ] Testes [ ] README`
