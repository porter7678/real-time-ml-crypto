run-live-dev:
	cp live.dev.env .env
	poetry run python src/main.py

run-historical-dev: # TODO: Test
	cp historical.dev.env .env
	poetry run python src/main.py

build:
	docker build -t trade_to_ohlc .

run-live: build
	docker run \
		--network=redpanda_network \
		--env-file live.prod.env \
		trade_to_ohlc

run-historical: build # TODO: Test
	docker run \
		--network=redpanda_network \
		--env-file historical.prod.env \
		trade_to_ohlc