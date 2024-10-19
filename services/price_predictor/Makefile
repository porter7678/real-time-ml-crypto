# To run the training script without Docker
training-dev:
	poetry run python src/training.py

# To run the API locally without Docker
api-dev:
	poetry run uvicorn src.api:app --reload --port 8000

# To check the health of the API
check-health-dev:
	curl -X GET http://localhost:8000/health

# To make a prediction request to the API
predict-request-dev:
	curl -X GET "http://localhost:8000/predict?product_id=BTC%2FUSD"

# Build the Docker image
build:
	docker build -t price_predictor .

# Run the training script inside the Docker container
training: build
	docker run \
		--env-file .env \
		-e TRAINING_OR_PREDICTION=training \
		price_predictor

# Run the API inside the Docker container
api: build
	docker run \
		-p 8000:80 \
		--env-file .env \
		-e TRAINING_OR_PREDICTION=prediction \
		price_predictor

# # check health of our production API FIXME
# check-health-prod:
# 	curl -X GET https://price-predictor-plabartabajo-realtimemlsystemcohort-e3624228.deployments.quix.io/health

# # make a prediction request to our production API FIXME:
# predict-request-prod:
# 	curl -X GET "https://price-predictor-plabartabajo-realtimemlsystemcohort-e3624228.deployments.quix.io/predict?product_id=BTC%2FUSD"