variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ami_id" {
  type        = string
  default     = "ami-0c1fe732b5494dc14"  
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
}