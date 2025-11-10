variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "gospital"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ deployment"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "gospital"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "medical_records_table" {
  description = "DynamoDB table name for medical records"
  type        = string
  default     = "medical_records"
}

variable "invoices_table" {
  description = "DynamoDB table name for invoices"
  type        = string
  default     = "invoices"
}

variable "container_cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Fargate task memory in MB"
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "container_port" {
  description = "Container port for the application"
  type        = number
  default     = 8080
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to connect to RDS for migrations (your IP)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change to your IP for security (e.g., ["1.2.3.4/32"])
}
