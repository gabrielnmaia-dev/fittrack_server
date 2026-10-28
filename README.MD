# FitTrack 🏋️

API REST para acompanhamento de treinos e dietas com planos personalizados.

---

## Tecnologias

- Python / Django + Django REST Framework
- JWT para autenticação (`djangorestframework-simplejwt`)
- Swagger / ReDoc via `drf-spectacular`
- Filtros, busca e ordenação via `django-filter`
- PostgreSQL
- Docker + Docker Compose
- Makefile para automação de tarefas

---

## Requisitos

- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)

---

## Configuração

Copie o arquivo de variáveis de ambiente e ajuste os valores:

```bash
cp .env.example .env
```

```env
SECRET_KEY=sua-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

DB_NAME=fittrack
DB_USER=fittrack
DB_PASSWORD=fittrack
DB_HOST=db
DB_PORT=5432

TIME_ZONE=UTC
LOG_LEVEL=INFO
```

> `DB_HOST=db` é o nome do serviço do banco dentro do Docker Compose.
> Para rodar o Django fora do Docker, use `DB_HOST=localhost` e `DB_PORT=5433`.

---

## Rodando o projeto

### Com Make

```bash
make build           # Builda os containers
make up              # Sobe os containers
make migrate         # Roda as migrations
make createsuperuser # Cria superusuário
```

### Sem Make

```bash
docker compose up --build
docker compose exec api python manage.py migrate
docker compose exec api python manage.py createsuperuser
```

A API fica disponível em `http://localhost:8000`.

> Em produção, a imagem usa **gunicorn** por padrão (`Dockerfile`). Defina
> `DEBUG=False` no `.env`, configure `ALLOWED_HOSTS` e sirva os arquivos
> estáticos do Django Admin (`python manage.py collectstatic`) via Nginx/CDN.

> O container roda como um usuário sem privilégios. Em sistemas Linux, se os
> arquivos do projeto pertencerem ao seu usuário (UID 1000), o Compose já usa
> `${HOST_UID:-1000}:${HOST_GID:-1000}`. Caso seu UID seja diferente, exporte
> antes de subir: `export HOST_UID=$(id -u) HOST_GID=$(id -g)`.

---

## Comandos úteis (Makefile)

| Comando | Descrição |
|---|---|
| `make up` | Sobe os containers |
| `make down` | Derruba os containers |
| `make build` | Builda as imagens |
| `make migrate` | Executa as migrations |
| `make migrations` | Gera novas migrations |
| `make createsuperuser` | Cria superusuário |
| `make shell` | Abre o shell do Django |
| `make test` | Roda a suíte de testes |
| `make check` | Executa os checks do Django |
| `make schema` | Gera o schema OpenAPI em `schema.yml` |

---

## Autenticação

A API usa JWT. O fluxo é: **registrar → obter token → usar o token**.

### Registro

```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "username": "joao",
  "email": "joao@example.com",
  "password": "Uma-Senha-Forte!123",
  "profile": {
    "age": 28,
    "height": 178,
    "weight": 75,
    "goal": "gain_muscle"
  }
}
```

O campo `profile` é opcional no registro (pode ser preenchido depois via
`PATCH /api/v1/users/me/`). As senhas são armazenadas com hash e validadas
pelos validadores de senha do Django.

`POST /api/v1/users/` também cria usuários (mesmo payload).

### Obter token

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "joao",
  "password": "Uma-Senha-Forte!123"
}
```

Resposta:

```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

### Usar o token

```http
Authorization: Bearer <access_token>
```

### Renovar token

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

---

## Endpoints

A API é versionada sob o prefixo `/api/v1/`.

| Recurso | Endpoint |
|---|---|
| Registro | `POST /api/v1/auth/register/` |
| Login (token) | `POST /api/v1/auth/token/` |
| Renovar token | `POST /api/v1/auth/token/refresh/` |
| Usuário autenticado | `GET/PUT/PATCH /api/v1/users/me/` |
| Usuários (staff) | `GET /api/v1/users/` |
| Planos de treino | `/api/v1/workout-plans/` |
| Exercícios | `/api/v1/exercises/` |
| Planos de dieta | `/api/v1/diet-plans/` |
| Refeições | `/api/v1/meals/` |
| Health check | `GET /health/` |

> **Mudanças de rota:** os caminhos agora seguem a documentação.
> `/api/v1/userprofiles/` foi substituído por `/api/v1/users/me/`;
> `/api/v1/workouts/` por `/api/v1/workout-plans/`;
> `/api/v1/dietplans/` por `/api/v1/diet-plans/`; e
> `/api/v1/token/` por `/api/v1/auth/token/`.

---

## Modelo de acesso

- Todos os endpoints (exceto registro, login e health check) exigem JWT.
- **Usuário comum** só enxerga e altera os próprios dados:
  - perfis de usuário;
  - planos de treino;
  - planos de dieta e suas refeições;
  - exercícios criados por ele (o catálogo global também é visível).
- **Staff** pode listar e administrar os dados de todos os usuários.
- O `user` de planos de treino/dieta e de exercícios é definido pelo servidor a
  partir do token — enviar `user` no payload não tem efeito.
- Refições só podem ser criadas em planos de dieta do próprio usuário.
- Exercícios do **catálogo global** (`"user": null`, criados no Django Admin)
  são visíveis para todos, mas só o staff pode alterá-los.
- Usuários só podem ser desativados (`DELETE /api/v1/users/{id}/`, staff);
  o registro é mantido no banco.
- Acessos a recursos de outros usuários retornam `404`, evitando vazar a
  existência dos registros.

### Soft delete

Todos os modelos de domínio (`UserProfile`, `Workout`, `Exercise`, `DietPlan`,
`Meal`) usam **soft delete**: `DELETE` marca `is_active=False` e o registro
continua no banco. As listagens da API escondem registros inativos, e o Django
Admin permite filtrar e restaurar registros desativados.

---

## Filtros, busca e ordenação

Todas as listagens suportam `search`, `ordering` e filtros por campo:

```
GET /api/v1/workout-plans/?search=hipertrofia&level=advanced
GET /api/v1/exercises/?muscle_group=peito&ordering=name
GET /api/v1/diet-plans/?user=1&search=low carb
GET /api/v1/meals/?diet_plan=1
GET /api/v1/users/?search=joao&is_active=true   # staff
```

Campos de ordenação aceitos:

| Recurso | Ordenação |
|---|---|
| Exercícios | `name`, `muscle_group`, `created_at` |
| Planos de treino | `name`, `duration`, `level`, `created_at` |
| Planos de dieta | `name`, `calories`, `created_at` |
| Refeições | `name`, `calories`, `created_at` |
| Usuários | `username`, `date_joined` |

### Paginação

Respostas paginadas (10 itens por padrão, máximo de 100 via `page_size`):

```json
{
  "count": 50,
  "next": "http://localhost:8000/api/v1/exercises/?page=2",
  "previous": null,
  "results": []
}
```

---

## Documentação

Com o projeto rodando, acesse:

- **Swagger UI:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Redoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **OpenAPI schema:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

Na Swagger UI, use o botão **Authorize** e informe o token JWT.

---

## Testes

A suíte cobre autenticação, permissões/isolamento entre usuários, CRUD,
validações, filtros, paginação, documentação e soft delete.

```bash
make test
```

Ou diretamente:

```bash
docker compose run --rm --no-deps api \
  python manage.py test --settings=app.settings_test
```

Os testes usam SQLite em memória (`app/settings_test.py`), então não precisam
do PostgreSQL nem do Redis rodando.

Para rodar localmente com um ambiente Python instalado:

```bash
pip install -r requirements.txt
python manage.py test --settings=app.settings_test
```

---

## Estrutura do projeto

```
fittrack/
├── app/
│   ├── api/v1/
│   │   ├── pagination.py
│   │   ├── permissions.py
│   │   ├── router.py
│   │   ├── serializers.py
│   │   ├── viewsets.py
│   │   └── tests/
│   ├── settings.py
│   ├── settings_test.py
│   └── urls.py
├── core/
├── users/
├── workouts/
├── diet/
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
└── manage.py
```
