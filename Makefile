.PHONY: format lint check migrations tests

format:
	isort .
	black .

lint:
	ruff check .

check: format lint

tests:
	python manage.py test products -v 2

migrations:
	python manage.py makemigrations
	python manage.py migrate


