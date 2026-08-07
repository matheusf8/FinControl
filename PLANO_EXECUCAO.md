# FinControl — Plano de Execução

Projeto de portfólio: sistema web de controle financeiro pessoal.
Stack: **React (Vite) → FastAPI → PostgreSQL**, com Docker e deploy em produção.
Repositório: `github.com/matheusf8/sistema-financeiro` (a criar).

---

## Stack técnica

**Frontend**
- React + Vite + TypeScript
- TailwindCSS (estilo)
- React Router (rotas)
- React Query (dados do servidor) + Zustand (estado local/auth)
- React Hook Form + Zod (formulários e validação)
- Recharts (gráficos do dashboard)

**Backend**
- Python 3.12 + FastAPI
- SQLAlchemy 2.0 + Alembic (models e migrations)
- Pydantic v2 (schemas)
- JWT (access + refresh token) com passlib/bcrypt para hash de senha
- Arquitetura em camadas: `routers → services → repositories → models/schemas`

**Infra**
- PostgreSQL
- Docker + Docker Compose (uso 100% local — sem publicação na internet)
- GitHub Actions (CI: lint + testes a cada push, só validação — não publica nada)

**Testes**
- Backend: pytest + httpx
- Frontend: Vitest + React Testing Library

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
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/       # cliente da API
│   │   └── store/
│   └── Dockerfile
├── docs/                    # documento mestre, ADRs, etc.
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Estratégia: MVP primeiro

O documento mestre original cobre 13 capítulos e recursos avançados (Open Finance, IA). Para não travar o projeto, a ordem é: **MVP funcional completo primeiro, extras depois**. Cartões/parcelamento entram antes de metas porque têm mais valor de portfólio (mostram lógica de negócio mais complexa).

---

## Sprints

### Sprint 1 — Setup do projeto
- Criar repositório no GitHub (`matheusf8/sistema-financeiro`), branch `main` protegida + `dev`
- Estrutura de pastas (backend/frontend), Docker Compose com Postgres + backend + frontend
- `.env.example`, `.gitignore`, README inicial
- GitHub Actions básico (roda lint em cada push)
- **Aceite:** `docker compose up` sobe os 3 serviços sem erro

### Sprint 2 — Backend: fundação + autenticação
- Modelos `User`, configuração do SQLAlchemy + Alembic (primeira migration)
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
- Validações de entrada, tratamento de erros, responsividade mobile
- Revisão de segurança (rate limiting básico, CORS, variáveis sensíveis fora do código)
- **Aceite:** suite de testes passando no CI, app usável no celular

### Sprint 8 — Empacotamento local e documentação
- Docker Compose "de produção" para uso local (build otimizado, variáveis de ambiente separadas de dev)
- Sem publicação na internet: o projeto roda 100% na sua máquina com `docker compose up`
- README completo (setup local passo a passo, prints, stack, como rodar testes) — importante pro repo ficar bom no GitHub mesmo sem link ao vivo
- Seed de dados de demonstração, para abrir o app já com dados de exemplo
- **Aceite:** qualquer pessoa que clonar o repo consegue rodar `docker compose up` e usar o app localmente em poucos passos, sem precisar de nenhuma conta externa

---

## Fluxo de trabalho: quem faz o quê

- **Eu (assistente) edito os arquivos** direto nesta pasta (código, docs, configs) — isso funciona normalmente.
- **Comandos de Git (`init`, `add`, `commit`, `push`) rodam no terminal do VSCode, por você** — o ambiente sandbox onde eu executo comandos não consegue manipular os arquivos internos do `.git` nesta pasta (é sincronizada via OneDrive, e essa combinação trava operações do Git). Sempre que tiver algo pronto pra commitar, eu aviso e passo os comandos exatos pra colar no terminal.

## Portabilidade entre computadores

**Por que é preciso um passo extra:** o Postgres guarda os dados num volume interno do Docker, escondido no sistema — não é um arquivo dentro da pasta `sistema-financeiro`. O OneDrive só sincroniza o que está literalmente dentro da pasta, então ele nunca vê (nem sincroniza) esses dados. O código, sim, viaja sozinho: está no GitHub, então `git clone` + `docker compose up` funciona em qualquer PC — só que com um banco **novo e vazio**.

**Solução:** manter Postgres (bom pro portfólio) + scripts de backup/restore que exportam os dados para um arquivo `.sql` normal, salvo dentro da pasta do projeto (`backups/`, fora do Git via `.gitignore`, mas dentro do OneDrive — esse arquivo sim sincroniza sozinho entre PCs):
- `backup.sh` / `backup.bat` — roda `pg_dump` e salva um `.sql` em `backups/`
- `restore.sh` / `restore.bat` — roda `pg_restore`/`psql` a partir do último backup

**Fluxo passo a passo ao trocar de computador:**
1. No PC A, termina de usar o app e roda `backup` → gera `backups/backup_2026-08-06.sql`.
2. Espera o OneDrive sincronizar (ícone verde).
3. No PC B, roda `git pull` (código) + `docker compose up` (sobe um banco novo vazio).
4. Roda `restore` no PC B → lê o `.sql` mais recente e recria os dados.

**Importante:** isso não é sincronização em tempo real (não é tipo Google Docs). É manual — só funciona se você lembrar de rodar backup antes de trocar de PC e restore depois. Se usar o app em dois PCs sem fazer esse processo no meio, um lançamento pode se perder. Na prática, funciona bem usando um computador de cada vez e seguindo essa rotina. Isso entra no Sprint 8 (empacotamento local).

## Depois do MVP (backlog futuro)
- Open Finance (integração bancária)
- Notificações (vencimento de fatura, metas)
- IA para análise de gastos

Esses ficam fora dos 8 sprints — só entram se sobrar tempo/energia depois do projeto "fechado".

---

## Checklist final (do documento mestre)
`[ ] Login [ ] Cadastro [ ] JWT [ ] CRUD Receitas [ ] CRUD Despesas [ ] Dashboard [ ] Gráficos [ ] Cartões [ ] Parcelamento [ ] Metas [ ] Docker [ ] Deploy [ ] Testes [ ] README`
