up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrations:
	docker compose exec api python manage.py makemigrations

migrate:
	docker compose exec api python manage.py migrate

shell:
	docker compose exec api python manage.py shell

createsuperuser:
	docker compose exec api python manage.py createsuperuser

app:
	docker compose exec api python manage.py startapp $(name)

test:
	docker compose run --rm --no-deps --build api python manage.py test --settings=app.settings_test

check:
	docker compose run --rm --no-deps --build api python manage.py check --settings=app.settings_test

schema:
	docker compose exec api python manage.py spectacular --file schema.yml

.PHONY: up down build logs migrations migrate shell createsuperuser app test check schema
