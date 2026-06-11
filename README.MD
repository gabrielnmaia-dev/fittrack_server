# FitTrack 🏋️

API REST para acompanhamento de treinos e dietas com planos personalizados.

---

## Tecnologias

- Python / Django + Django REST Framework
- JWT para autenticação
- Swagger / drf-spectacular para documentação
- Docker + Docker Compose
- Makefile para automação de tarefas


---

## Requisitos

- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)

---

## Configuração

Clone o repositório e copie o arquivo de variáveis de ambiente:

```bash
git clone https://github.com/seu-usuario/fittrack.git
cd fittrack
cp .env.example .env
```

Edite o `.env` com suas configurações:

```env
SECRET_KEY=sua-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@db:5432/fittrack
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Rodando o projeto

### Com Make

```bash
make build       # Builda os containers
make up          # Sobe os containers
make migrate     # Roda as migrations
make createsuperuser  # Cria superusuário
```

### Sem Make

```bash
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## Comandos úteis (Makefile)

| Comando | Descrição |
|---|---|
| `make up` | Sobe os containers |
| `make down` | Derruba os containers |
| `make build` | Builda as imagens |
| `make migrate` | Executa as migrations |
| `make makemigrations` | Gera novas migrations |
| `make createsuperuser` | Cria superusuário |
| `make shell` | Abre o shell do Django |


---

## Autenticação

A API usa JWT. Para autenticar, faça login e use o token retornado no header das requisições.

**Obter token:**
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "seu-usuario",
  "password": "sua-senha"
}
```

**Usar o token:**
```http
Authorization: Bearer <access_token>
```

**Renovar token:**
```http
POST /api/v1/auth/token/refresh/
```

---

## Modelos

### User (Usuário)
Usuário do sistema com dados de perfil como peso, altura e objetivo.

### WorkoutPlan (Plano de Treino)
Plano de treino personalizado vinculado a um usuário, com nome, descrição e nível de dificuldade.

### Exercise (Exercício)
Exercícios cadastrados com séries, repetições e grupo muscular.

### DietPlan (Plano de Dieta)
Plano alimentar personalizado com calorias diárias e distribuição de macros.

### Meal (Refeição)
Refeições vinculadas a um plano de dieta com horário e composição.

> Todos os modelos utilizam **soft delete** — registros não são removidos do banco, apenas marcados como inativos.

---

## Endpoints

A API é versionada sob o prefixo `/api/v1/`.

| Recurso | Endpoint |
|---|---|
| Autenticação | `/api/v1/auth/token/` |
| Usuários | `/api/v1/users/` |
| Planos de Treino | `/api/v1/workout-plans/` |
| Exercícios | `/api/v1/exercises/` |
| Planos de Dieta | `/api/v1/diet-plans/` |
| Refeições | `/api/v1/meals/` |

### Filtros e busca

Todas as listagens suportam busca via `query_params`:

```
GET /api/v1/workout-plans/?search=hipertrofia
GET /api/v1/exercises/?muscle_group=peito
GET /api/v1/diet-plans/?user=1
```

### Paginação

Respostas paginadas por padrão:

```json
{
  "count": 50,
  "next": "http://localhost:8000/api/v1/exercises/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Documentação

Com o projeto rodando, acesse:

- **Swagger UI:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Redoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

---

## Testes com Postman

Importe a collection disponível em `/docs/fittrack.postman_collection.json` para testar todos os endpoints com exemplos de requisição já configurados.

Fluxo básico de teste:
1. Criar usuário via `POST /api/v1/users/`
2. Autenticar via `POST /api/v1/auth/token/`
3. Usar o `access` token nas demais requisições

---

## Estrutura do projeto

```
fittrack/
├── apps/
│   ├── users/
│   ├── workouts/
│   └── diets/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── docker/
├── .env.example
├── docker-compose.yml
├── Makefile
└── manage.py
```

---

