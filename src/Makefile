app:
	@if [ -z "$(name)" ]; then \
  		echo "Error: You must provide the app. Usage: make app name_of_app"; \
	else \
		python manage.py startapp $(name); \
	fi

migrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate


run:
	python manage.py $(command)

commands = banks budget_types categories countries debt_types goal_types investment_types notification_types

batch_seeder:
	@for command in $(commands); do \
		echo "Running: $$command"; \
		python manage.py $$command; \
	done

seed:
	python manage.py seeder

shell:
	python manage.py shell

show_urls:
	python manage.py show_urls

test:
	@echo "Enter the module you want to run (leave empty to run all tests):"; \
	read module; \
	if [ -z "$$module" ]; then \
		pytest -vv; \
	else \
		pytest -vv "$$module"; \
	fi


