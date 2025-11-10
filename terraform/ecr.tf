# ECR Repository for Gospital API
resource "aws_ecr_repository" "gospital" {
  name                 = "${var.project_name}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-api"
  }
}

# ECR Lifecycle Policy to clean up old images
resource "aws_ecr_lifecycle_policy" "gospital" {
  repository = aws_ecr_repository.gospital.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Null resource to build and push Docker image to ECR
resource "null_resource" "build_and_push_image" {
  triggers = {
    # Re-build when Dockerfile changes
    dockerfile_hash = filemd5("${path.module}/../Dockerfile")
    # Re-build when go.mod changes (dependencies updated)
    gomod_hash = filemd5("${path.module}/../go.mod")
    # Force rebuild - uncomment to always rebuild
    # always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOF
      set -e
      
      echo "Logging in to ECR..."
      aws ecr get-login-password --region ${var.aws_region} | \
        docker login --username AWS --password-stdin ${aws_ecr_repository.gospital.repository_url}
      
      echo "Building Docker image for linux/amd64..."
      docker build --platform linux/amd64 -t gospital-api ${path.module}/../
      
      echo "Tagging image..."
      docker tag gospital-api:latest ${aws_ecr_repository.gospital.repository_url}:latest
      
      echo "Pushing image to ECR..."
      docker push ${aws_ecr_repository.gospital.repository_url}:latest
      
      echo "Image pushed successfully!"
    EOF
  }

  depends_on = [aws_ecr_repository.gospital]
}
