# Deploy do FinControl na internet (Vercel + Render + Neon)

Guia passo a passo pra colocar o FinControl no ar, sempre acessível, sem depender do PC ligado.
Arquitetura: **frontend no Vercel**, **backend no Render**, **banco Postgres no Neon** (gratuito
e sem expirar — diferente do Postgres grátis do próprio Render, que expira em 30 dias).

Custo: **R$ 0/mês** pra começar. Único trade-off do plano grátis: o backend no Render "dorme"
depois de ~15 min sem acesso, e a próxima visita demora uns 30-50s pra acordar. Se isso incomodar,
dá pra trocar o backend pro plano Starter do Render (~$7/mês) depois — não muda nada no código.

As contas e cliques nos dashboards abaixo são coisas que só você pode fazer (login/senha em
serviço de terceiro). Eu preparei todo o código e configs pra esse passo a passo ser rápido.

---

## Status atual (atualizado 2026-08-10)

- [x] Repositório GitHub criado e código enviado: `https://github.com/matheusf8/FinControl.git`,
      branch `main` sincronizada
- [x] Neon: projeto `FinControl` criado, connection string do Postgres obtida (guardada só na
      conversa/no Render — não commitada em arquivo nenhum por segurança)
- [ ] Render: serviço ainda não criado
- [ ] Vercel: projeto ainda não criado

## 0. Subir o código pro GitHub

✅ Feito — código já está em `https://github.com/matheusf8/FinControl.git`, branch `main`.

## 1. Banco de dados — Neon (Postgres gratuito)

1. Crie conta em https://neon.tech (dá pra entrar com GitHub)
2. "New Project" → nome `fincontrol` → região mais perto do Brasil disponível
3. Na tela do projeto, copie a **Connection string** (algo como
   `postgresql://usuario:senha@ep-xxx-pooler.neon.tech/neondb?sslmode=require`)
4. Guarde essa string — vai usar como `DATABASE_URL` no Render (passo 3)

## 2. `SECRET_KEY` — já gerei uma pra você

Chave forte gerada localmente, não commitada em nenhum arquivo:

```
8d2e6ccd2325d449ab4c7eb31a399c489bf257c06434c8b63404c603c765dd0a
```

Guarde ela também — vai usar como `SECRET_KEY` no Render (próximo passo). Se preferir gerar a sua
própria, o comando é `python -c "import secrets; print(secrets.token_hex(32))"`.

## 3. Backend — Render

1. Crie conta em https://render.com (dá pra entrar com GitHub)
2. "New" → "Blueprint" → conecte o repositório `FinControl` — o Render já vai ler o
   [`backend/render.yaml`](../backend/render.yaml) que preparei e sugerir o serviço `fincontrol-backend`
3. Ele vai pedir pra preencher 3 env vars (ficaram como `sync: false` no blueprint de propósito,
   pra não pedir isso público no arquivo):
   - `SECRET_KEY` → cole a chave do passo 2
   - `DATABASE_URL` → cole a connection string do Neon (passo 1)
   - `CORS_ORIGINS` → deixe em branco por enquanto, volta aqui depois do passo 4 (Vercel) pra
     preencher com a URL final do frontend
4. Deploy. Quando terminar, anote a URL gerada (algo como `https://fincontrol-backend.onrender.com`)
5. Teste: abra `https://SEU-BACKEND.onrender.com/api/health` no navegador — deve responder
   `{"status": "ok", "app": "FinControl"}`

## 4. Frontend — Vercel

1. Crie conta em https://vercel.com (dá pra entrar com GitHub)
2. "Add New" → "Project" → importe o repositório `FinControl`
3. Em "Root Directory", selecione `frontend`
4. Em "Environment Variables", adicione:
   - `VITE_API_URL` = a URL do backend do passo 3 (ex: `https://fincontrol-backend.onrender.com`,
     **sem** `/api` no final — o código já completa isso)
5. Deploy. Anote a URL final (algo como `https://sistema-financeiro.vercel.app`)

## 5. Fechar o CORS

Volte no Render (serviço `fincontrol-backend` → Environment) e edite `CORS_ORIGINS` pra URL do
Vercel do passo 4 (ex: `https://sistema-financeiro.vercel.app`). Salve — o Render reinicia o
serviço sozinho.

## 6. Testar de ponta a ponta

1. Abra a URL do Vercel
2. Cadastre um usuário, faça login
3. Crie uma conta e uma transação
4. Recarregue a página — os dados devem continuar lá (prova que é Postgres de verdade, não mais
   um arquivo que sumiria a cada deploy)

---

## Depois disso

- Todo `git push` pra `main` faz o Vercel e o Render redeployarem sozinhos (deploy automático)
- Pra migrar o backend pro plano pago (tirar o "sono" do free tier): Render → serviço → Settings → Instance Type
- O `.exe` local (`desktop/`) continua existindo no repositório, mas deixou de ser o jeito
  recomendado de usar o FinControl a partir desta migração
