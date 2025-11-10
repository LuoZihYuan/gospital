# Data source to get existing LabRole (required for AWS Learner Lab)
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# Note: AWS Learner Lab does not allow creating custom IAM roles
# We must use the pre-created LabRole for ECS task execution and task roles
# This role has broad permissions suitable for learning environments

# Output the role ARN for reference
output "lab_role_arn" {
  description = "ARN of the LabRole used for ECS tasks"
  value       = data.aws_iam_role.lab_role.arn
}
