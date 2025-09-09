# Copy this file to terraform.tfvars and update the values

aws_region = "us-east-1"
project_name = "stock-bot"
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]
kubernetes_version = "1.28"
node_desired_size = 2
node_max_size = 4
node_min_size = 1
node_instance_types = ["t3.medium"]
