install:
	pip install -r requirements.txt

run:
	uvicorn api.main:app --reload

test:
	pytest tests/ --cov=. --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .

up:
	docker-compose up -d

down:
	docker-compose down

train:
	python -m ml.train_predictor