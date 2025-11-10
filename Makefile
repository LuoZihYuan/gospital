.PHONY: help deploy destroy start stop log shell clean status update

# Variables
TERRAFORM_DIR := terraform
AWS_REGION := us-west-2
PROJECT_NAME := gospital
DB_PASSWORD ?= GospitalSecure123

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Gospital - Hospital Management API"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-15s %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment variables:"
	@echo "  DB_PASSWORD - Database password (default: GospitalSecure123)"

deploy: ## Deploy infrastructure to AWS
	@echo "Deploying Gospital to AWS..."
	@cd $(TERRAFORM_DIR) && terraform init
	@cd $(TERRAFORM_DIR) && terraform apply -var="db_password=$(DB_PASSWORD)" -auto-approve
	@echo ""
	@echo "Deployment complete!"
	@echo "API URL: $$(cd $(TERRAFORM_DIR) && terraform output -raw alb_url)"

update: ## Rebuild Docker image and update ECS service
	@echo "Rebuilding Docker image..."
	@ECR_URL=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecr_repository_url) && \
	CLUSTER=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_cluster_name) && \
	SERVICE=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_service_name) && \
	echo "Logging in to ECR..." && \
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $$ECR_URL && \
	echo "Building Docker image for linux/amd64..." && \
	docker build --platform linux/amd64 -t $(PROJECT_NAME)-api . && \
	echo "Tagging image..." && \
	docker tag $(PROJECT_NAME)-api:latest $$ECR_URL:latest && \
	echo "Pushing image to ECR..." && \
	docker push $$ECR_URL:latest && \
	echo "Forcing ECS service to deploy new image..." && \
	aws ecs update-service \
		--cluster $$CLUSTER \
		--service $$SERVICE \
		--force-new-deployment \
		--region $(AWS_REGION) > /dev/null && \
	echo "Update complete! New image deployed to ECS."

destroy: ## Destroy all infrastructure
	@echo "WARNING: This will destroy all infrastructure!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd $(TERRAFORM_DIR) && terraform destroy -var="db_password=$(DB_PASSWORD)" -auto-approve; \
		echo "Removing local Docker images..."; \
		docker rmi $(PROJECT_NAME)-api:latest -f 2>/dev/null || true; \
		docker images | grep $(PROJECT_NAME) | awk '{print $$3}' | xargs -r docker rmi -f 2>/dev/null || true; \
		echo "Infrastructure destroyed."; \
	else \
		echo "Destroy cancelled."; \
	fi

start: ## Start ECS service (scale to desired count)
	@echo "Starting ECS service..."
	@CLUSTER=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_cluster_name) && \
	SERVICE=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_service_name) && \
	aws ecs update-service \
		--cluster $$CLUSTER \
		--service $$SERVICE \
		--desired-count 2 \
		--region $(AWS_REGION)
	@echo "ECS service started."

stop: ## Stop ECS service (scale to 0)
	@echo "Stopping ECS service..."
	@CLUSTER=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_cluster_name) && \
	SERVICE=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_service_name) && \
	aws ecs update-service \
		--cluster $$CLUSTER \
		--service $$SERVICE \
		--desired-count 0 \
		--region $(AWS_REGION)
	@echo "ECS service stopped."

log: ## View ECS service logs
	@echo "Fetching ECS logs..."
	@CLUSTER=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_cluster_name) && \
	SERVICE=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_service_name) && \
	TASK=$$(aws ecs list-tasks --cluster $$CLUSTER --service-name $$SERVICE --region $(AWS_REGION) --query 'taskArns[0]' --output text) && \
	if [ "$$TASK" = "None" ] || [ -z "$$TASK" ]; then \
		echo "No running tasks found."; \
	else \
		echo "Streaming logs from task: $$TASK"; \
		aws logs tail /ecs/$(PROJECT_NAME) --follow --region $(AWS_REGION); \
	fi

shell: ## Get shell access to running ECS container
	@echo "Connecting to ECS container..."
	@CLUSTER=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_cluster_name) && \
	SERVICE=$$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_service_name) && \
	TASK=$$(aws ecs list-tasks --cluster $$CLUSTER --service-name $$SERVICE --region $(AWS_REGION) --query 'taskArns[0]' --output text) && \
	if [ "$$TASK" = "None" ] || [ -z "$$TASK" ]; then \
		echo "No running tasks found. Start the service first with 'make start'"; \
	else \
		echo "Opening shell in task: $$TASK"; \
		aws ecs execute-command \
			--cluster $$CLUSTER \
			--task $$TASK \
			--container api \
			--interactive \
			--command "/bin/sh" \
			--region $(AWS_REGION); \
	fi

clean: ## Clean up local Terraform files and Docker artifacts
	@echo "Cleaning up Terraform files..."
	@rm -rf $(TERRAFORM_DIR)/.terraform
	@rm -rf $(TERRAFORM_DIR)/.terraform.lock.hcl
	@rm -rf $(TERRAFORM_DIR)/terraform.tfstate*
	@rm -rf docs/
	@echo "Cleaning up Docker artifacts..."
	@docker system prune -f
	@echo "Cleanup complete."

status: ## Show deployment status
	@echo "Gospital Deployment Status"
	@echo "=========================="
	@if [ -f "$(TERRAFORM_DIR)/terraform.tfstate" ]; then \
		echo "API URL: $$(cd $(TERRAFORM_DIR) && terraform output -raw alb_url 2>/dev/null || echo 'Not deployed')"; \
		echo "RDS Endpoint: $$(cd $(TERRAFORM_DIR) && terraform output -raw rds_endpoint 2>/dev/null || echo 'Not deployed')"; \
		echo "ECS Cluster: $$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_cluster_name 2>/dev/null || echo 'Not deployed')"; \
		echo "ECS Service: $$(cd $(TERRAFORM_DIR) && terraform output -raw ecs_service_name 2>/dev/null || echo 'Not deployed')"; \
	else \
		echo "Infrastructure not deployed yet."; \
	fi