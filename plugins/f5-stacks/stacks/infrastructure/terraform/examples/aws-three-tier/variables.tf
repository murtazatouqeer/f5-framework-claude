# =============================================================================
# Project Variables
# =============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "example"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# =============================================================================
# VPC Configuration
# =============================================================================

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "single_nat_gateway" {
  description = "Use single NAT gateway"
  type        = bool
  default     = true
}

# =============================================================================
# Application Configuration
# =============================================================================

variable "container_image" {
  description = "Docker image for the application"
  type        = string
  default     = "nginx:alpine"
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 80
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/"
}

variable "task_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Fargate task memory in MB"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# =============================================================================
# Database Configuration
# =============================================================================

variable "database_engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"

  validation {
    condition     = contains(["postgres", "mysql"], var.database_engine)
    error_message = "Database engine must be postgres or mysql."
  }
}

variable "database_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "15.4"
}

variable "database_instance_class" {
  description = "Database instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "database_allocated_storage" {
  description = "Database allocated storage in GB"
  type        = number
  default     = 20
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "app"
}

variable "database_username" {
  description = "Database master username"
  type        = string
  default     = "admin"
}

variable "database_multi_az" {
  description = "Enable Multi-AZ for database"
  type        = bool
  default     = false
}

variable "database_backup_retention" {
  description = "Database backup retention in days"
  type        = number
  default     = 7
}
