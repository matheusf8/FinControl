# Deploy do FinControl na internet (Vercel + Render + Neon)

Status: **🎉 concluído e no ar** (2026-08-10). Arquitetura: **frontend no Vercel**, **backend no
Render**, **banco Postgres no Neon** (gratuito e sem expirar — diferente do Postgres grátis do
próprio Render, que expira em 30 dias).

Custo: **R$ 0/mês**. Único trade-off do plano grátis: o backend no Render "dorme" depois de ~15
min sem acesso, e a próxima visita demora uns 30-50s pra acordar. Se isso incomodar, dá pra trocar
o backend pro plano Starter do Render (~$7/mês) depois — não muda nada no código.

---

## URLs em produção

- **Frontend (o que você acessa):** https://fin-control-three.vercel.app
- **Backend (API):** https://fincontrol-backend-cebg.onrender.com
- **Health check:** https://fincontrol-backend-cebg.onrender.com/api/health

## Cadastro por convite

Cadastro é aberto pra internet, mas protegido por **código de convite**: quem não souber o código
configurado em `INVITE_CODE` (env var no Render) não consegue criar conta — recebe 403. Only
compartilhe o código com quem você quer convidar; não fica visível em lugar nenhum público.

## Serviços e onde mexer em cada um

| Camada | Serviço | Painel |
|---|---|---|
| Frontend | Vercel | https://vercel.com/dashboard → projeto `FinControl` |
| Backend | Render | https://dashboard.render.com → serviço `fincontrol-backend` |
| Banco | Neon | https://console.neon.tech → projeto `FinControl` |
| Código | GitHub | https://github.com/matheusf8/FinControl |

## Variáveis de ambiente configuradas no Render

(valores reais só no painel do Render, nunca commitados)

- `SECRET_KEY` — chave do JWT
- `DATABASE_URL` — connection string do Postgres (Neon)
- `CORS_ORIGINS` — `https://fin-control-three.vercel.app`
- `INVITE_CODE` — código exigido no cadastro
- `PYTHON_VERSION` — `3.12.7` (fixo via `backend/render.yaml`, não precisa mexer)

## Variável de ambiente configurada no Vercel

- `VITE_API_URL` — `https://fincontrol-backend-cebg.onrender.com`

---

## Operação do dia a dia

- **Deploy automático:** todo `git push` pra `main` já faz o Vercel e o Render redeployarem
  sozinhos. Não precisa fazer nada manual pra publicar uma mudança.
- **Ver logs/erros do backend:** Render → serviço `fincontrol-backend` → aba "Logs"
- **Ver logs/erros do frontend (build):** Vercel → projeto → aba "Deployments" → clique no deploy
- **Trocar o código de convite:** Render → Environment → edita `INVITE_CODE` → salva (reinicia
  sozinho)
- **Tirar o "sono" do backend (~$7/mês):** Render → serviço → Settings → Instance Type → Starter
- **Ver/gerenciar usuários e dados direto no banco:** Neon → projeto → SQL Editor, ou
  `psql "$DATABASE_URL"` local

## Se precisar recriar do zero (outro Neon/Render/Vercel, ex: mudar de conta)

1. **Neon** — criar projeto, copiar a connection string (Dashboard → Connect)
2. **Render** — "New" → "Blueprint", conectar o repo, **Blueprint Path = `backend/render.yaml`**
   (o arquivo não está na raiz do repo), preencher as env vars listadas acima
3. **Vercel** — "Add New" → "Project", importar o repo, **Root Directory = `frontend`**, preencher
   `VITE_API_URL` com a URL do backend do passo 2
4. Voltar no Render e ajustar `CORS_ORIGINS` pra URL final do Vercel
5. Testar: cadastrar usuário (com o código de convite), logar, criar conta/transação, recarregar
   a página e confirmar que os dados persistem (prova que é Postgres de verdade)

## Histórico: problemas resolvidos durante o deploy

- **Build do Render falhava (`pyinstaller`/Python 3.14):** o `requirements.txt` tinha
  `pyinstaller`/`pywebview` (só usados pra empacotar o `.exe` local), e o Render usa Python mais
  recente por padrão — sem wheel do `pyinstaller` pra essa versão, e `pydantic-core` também
  quebrava por precisar compilar via Rust sem toolchain disponível. Corrigido movendo essas duas
  libs pra `backend/requirements-desktop.txt` (fora do build do servidor) e fixando
  `PYTHON_VERSION=3.12.7` no `render.yaml` (não usar `runtime.txt`, formato do Heroku — Render não
  lê isso).
- **`prints/` fora do `.gitignore`:** pasta usada pra troca de screenshots com o assistente podia
  vazar credenciais em print sem querer — adicionada ao `.gitignore`.

---

O `.exe` local (`desktop/`) continua existindo no repositório como modo alternativo 100%
offline/local, mas deixou de ser o jeito recomendado de usar o FinControl — ver README.
