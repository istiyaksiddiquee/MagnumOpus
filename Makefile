lake-up:
	docker-compose -f lakehouse.docker-compose.yml --env-file .\.env up --build

airflow-up:
	docker-compose -f airflow.docker-compose.yml --env-file .\.env up --build

down:
	docker-compose -f lakehouse.docker-compose.yml --env-file .\.env down
	docker-compose -f airflow.docker-compose.yml --env-file .\.env down 