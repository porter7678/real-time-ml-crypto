start-redpanda:
	docker compose -f docker-compose-redpanda.yml up -d 

stop-redpanda:
	docker compose -f docker-compose-redpanda.yml down