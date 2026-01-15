# ============================================================
# 📦 Project Makefile — Production & Development Ready
# ============================================================

# ============================================================
# 🐍 Python Virtual Environment
# ============================================================
venv:
	python3 -m venv .venv
	. .venv/bin/activate

list:
	pip list

uninstall-all:
	pip freeze | xargs pip uninstall -y

install-all:
	pip install -r requirements.txt

appinstall:
	pip install $(package)

# ============================================================
# 🐳 DOCKER — PRODUCTION
# ============================================================
build:
	@echo "📦 Building Docker image (Production)..."
	docker-compose build

build-progress:
	docker compose build --progress=plain

fresh-build:
	docker compose build --no-cache

up:
	@echo "🚀 Starting production services..."
	docker compose up -d --remove-orphans

down:
	@echo "🛑 Stopping production services..."
	docker compose down --volumes --remove-orphans

restart:
	make down
	make up

logs:
	docker compose logs -f

migrate:
	@echo "📜 Running database migrations..."
	docker compose exec -T api python manage.py migrate

shell:
	docker exec -it borderlink_api /bin/sh

# ============================================================
# 🧪 DOCKER — DEVELOPMENT
# ============================================================
dev-build:
	docker compose -f docker-compose.dev.yml build

dev-progress:
	docker compose -f docker-compose.dev.yml build --progress=plain

dev-fresh-build:
	docker compose -f docker-compose.dev.yml build --no-cache

dev:
	docker compose -f docker-compose.dev.yml up -d --remove-orphans

dev-down:
	docker compose -f docker-compose.dev.yml down --volumes --remove-orphans

dev-restart:
	make dev-down
	make dev

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-shell:
	docker exec -it pfm_api_dev /bin/sh

# ============================================================
# 🧹 MAINTENANCE & UTILITIES
# ============================================================
purge-redis:
	docker exec -it pfm_api redis-cli flushall

purge-celery:
	docker exec -it celery_worker celery -A main_system purge -f

key:
	openssl rand -base64 $(length)

agno-upgrade:
	pip install -U agno --no-cache-dir

ngrok:
	ngrok http --url=pretty-noble-jaybird.ngrok-free.app 8000

# ============================================================
# 🪜 GIT HELPERS
# ============================================================
commit:
	@echo "Enter commit message: "; \
	read msg; \
	echo "Enter branch name (default: main): "; \
	read branch; \
	branch=$${branch:-main}; \
	for file in $$(git status --porcelain | awk '{print $$2}'); do \
		git add "$$file"; \
		git commit -m "$$msg" -- "$$file"; \
	done; \
	git push origin "$$branch"

# ============================================================
# 🐍 Django Helpers
# ============================================================
startapp:
	@if [ -z "$(name)" ]; then \
  		echo "Error: You must provide the app name. Usage: make startapp name=myapp"; \
	else \
		cd src && python manage.py startapp $(name); \
	fi

migrations:
	cd src && python manage.py makemigrations

# ============================================================
# 🐳 Docker Hub Deployment
# ============================================================
dhub_build:
	@echo "🐳 Building Docker image for Docker Hub..."
	docker build -t threxcode/pfm:latest .

dhub-push:
	@echo "⬆️  Pushing Docker image to Docker Hub..."
	docker push threxcode/pfm:latest
	@echo "✅ Docker image pushed successfully."

# ============================================================
# 🧽 Cleanup
# ============================================================
prune-docker:
	@echo "🧹 Pruning unused Docker resources..."
	docker system prune -a --volumes -f
	@echo "✅ Docker resources pruned successfully."

encode-env:
	base64 -i .env.production | tr -d '\n' > encoded_env.txt

# ============================================================
# 📜 Deployment Helper (for manual trigger)
# ============================================================
deploy:
	@echo "🚀 Running manual deployment steps..."
	docker compose build --no-cache
	docker compose up -d --remove-orphans
	docker compose exec -T api python manage.py migrate
	docker image prune -f && docker builder prune -f
	@echo "✅ Deployment completed successfully."

