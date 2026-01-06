.PHONY: help install dev test build deploy clean

# V3 Makefile - LegoDesigner System

help:
	@echo "🏠 LegoDesigner V3 - Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Start development server"
	@echo "  make test          - Run tests"
	@echo "  make build         - Build for production"
	@echo "  make deploy        - Deploy to production"
	@echo "  make clean         - Clean up"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo ""

# ========================================
# Installation
# ========================================

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	go mod download
	@echo "✓ Dependencies installed"

install-dev:
	@echo "📦 Installing dev dependencies..."
	pip install -r requirements-dev.txt
	@echo "✓ Dev dependencies installed"

# ========================================
# Development
# ========================================

dev:
	@echo "🚀 Starting development server..."
	python v3/app.py

dev-watch:
	@echo "👀 Starting development server with auto-reload..."
	python -m flask --app v3/app run --reload

# ========================================
# Testing
# ========================================

test:
	@echo "🧪 Running tests..."
	pytest v3/tests/ -v

test-coverage:
	@echo "📊 Running tests with coverage..."
	pytest v3/tests/ --cov=v3 --cov-report=html

test-go:
	@echo "🧪 Running Go tests..."
	cd v3/go && go test ./...

# ========================================
# Building
# ========================================

build:
	@echo "🔨 Building for production..."
	mkdir -p build
	cp -r v3/templates build/
	cp -r v3/static build/
	@echo "✓ Build complete"

build-go:
	@echo "🔨 Building Go binaries..."
	cd v3/go && go build -o ../bin/lego-processor ./cmd/processor
	cd v3/go && go build -o ../bin/lego-order ./cmd/order
	@echo "✓ Go binaries built"

# ========================================
# Code Quality
# ========================================

lint:
	@echo "🔍 Running linters..."
	flake8 v3/ --max-line-length=120
	pylint v3/ --disable=all --enable=E,F
	cd v3/go && golangci-lint run ./...
	@echo "✓ Linting complete"

format:
	@echo "✨ Formatting code..."
	black v3/
	isort v3/
	cd v3/go && gofmt -w .
	@echo "✓ Formatting complete"

# ========================================
# Docker
# ========================================

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t lego-designer:v3 -f v3/Dockerfile .
	@echo "✓ Docker image built"

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 5000:5000 -v $(PWD)/data:/app/data lego-designer:v3
	@echo "✓ Docker container running"

docker-push:
	@echo "📤 Pushing Docker image..."
	docker tag lego-designer:v3 your-registry/lego-designer:v3
	docker push your-registry/lego-designer:v3
	@echo "✓ Docker image pushed"

# ========================================
# Deployment
# ========================================

deploy:
	@echo "🚀 Deploying to production..."
	@echo "1. Building..."
	make build
	make build-go
	@echo "2. Running tests..."
	make test
	@echo "3. Building Docker image..."
	make docker-build
	@echo "✓ Deployment ready"

deploy-docker:
	@echo "🚀 Deploying Docker container..."
	docker-compose -f v3/docker-compose.yml up -d
	@echo "✓ Docker deployment complete"

# ========================================
# Database
# ========================================

db-init:
	@echo "🗄️  Initializing database..."
	mkdir -p data/sessions
	mkdir -p data/models
	mkdir -p data/orders
	@echo "✓ Database initialized"

db-clean:
	@echo "🗑️  Cleaning database..."
	rm -rf data/sessions/*
	rm -rf data/models/*
	rm -rf data/orders/*
	@echo "✓ Database cleaned"

# ========================================
# Data Processing
# ========================================

process-jsonl:
	@echo "⚙️  Processing JSONL data..."
	cd v3/go && go run ./cmd/processor/main.go
	@echo "✓ JSONL processing complete"

export-ml-data:
	@echo "📊 Exporting ML training data..."
	cd v3/go && go run ./cmd/ml-export/main.go
	@echo "✓ ML data exported"

# ========================================
# Cleanup
# ========================================

clean:
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd v3/go && go clean
	@echo "✓ Cleanup complete"

clean-all: clean db-clean
	@echo "✓ Full cleanup complete"

# ========================================
# Documentation
# ========================================

docs:
	@echo "📚 Generating documentation..."
	mkdir -p docs
	@echo "✓ Documentation generated"

# ========================================
# Development Utilities
# ========================================

shell:
	@echo "🐚 Starting Python shell..."
	python

shell-go:
	@echo "🐚 Starting Go REPL..."
	cd v3/go && go run

logs:
	@echo "📋 Showing logs..."
	tail -f logs/app.log

logs-error:
	@echo "❌ Showing error logs..."
	tail -f logs/error.log

# ========================================
# Status
# ========================================

status:
	@echo "📊 System Status"
	@echo "==============="
	@echo "Flask Server: $(shell curl -s http://localhost:5000/health || echo 'Not running')"
	@echo "Session Manager: $(shell curl -s http://localhost:8765/health || echo 'Not running')"
	@echo "Blender: $(shell curl -s http://localhost:9876/health || echo 'Not running')"
	@echo ""

# ========================================
# Quick Start
# ========================================

quickstart: install db-init dev
	@echo "✓ Quick start complete"

# ========================================
# CI/CD
# ========================================

ci: lint test build
	@echo "✓ CI pipeline complete"

cd: build docker-build docker-push
	@echo "✓ CD pipeline complete"
