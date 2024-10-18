training-dev:
	poetry run python src/training.py

build:
	docker build -t price_predictor_training .

train: build
	docker run --env-file .env price_predictor_training
	
api-dev:
	poetry run uvicorn src.api:app --reload --port 9999

check-health:
	curl -X GET http://localhost:9999/health

predict-request:
	curl -X GET "http://localhost:9999/predict?product_id=BTC%2FUSD"