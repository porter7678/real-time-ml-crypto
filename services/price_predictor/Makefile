training:
	poetry run python src/training.py

build:
	docker build -t price_predictor_training .

run: build
	docker run --env-file .env price_predictor_training