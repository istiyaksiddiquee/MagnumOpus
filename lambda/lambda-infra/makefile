deploy:
	docker-compose -f docker-compose.yml up --build -V

destroy:
	docker-compose -f docker-compose.yml down

clean:
	rm -rf terraform/.terraform
	rm -f terraform/terraform.lock.hcl terraform/terraform.tfstate terraform/terraform.tfstate.backup