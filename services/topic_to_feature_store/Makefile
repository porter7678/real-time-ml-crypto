run-live-dev:
	cp live.dev.env .env
	poetry run python src/main.py

run-historical-dev:
	cp historical.dev.env .env
	poetry run python src/main.py

# build:
# 	docker build -t trade_producer .

# run: build
# 	docker run \
# 		--network=redpanda_network \
# 		--env-file=prod.env \
# 		trade_producer