terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }

  backend "s3" {
    bucket         = "jobhunt-pro-terraform-state"
    key            = "eks/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# ─── Variables ───────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "jobhunt-pro-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.29"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API key"
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
}

variable "telegram_bot_token" {
  description = "Telegram bot token"
  type        = string
  sensitive   = true
}

# ─── VPC ─────────────────────────────────────────────────────

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = {
    Environment = var.environment
    Project     = "jobhunt-pro"
  }
}

# ─── EKS Cluster ─────────────────────────────────────────────

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.8.4"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Managed node groups
  eks_managed_node_groups = {
    # Core system nodes (web, API, database)
    core = {
      name           = "jobhunt-core"
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 5
      desired_size   = 3

      labels = {
        role = "core"
      }

      tags = {
        Environment = var.environment
        NodeGroup   = "core"
      }
    }

    # Swarm agent nodes (auto-scaling)
    swarm = {
      name           = "jobhunt-swarm"
      instance_types = ["t3.large"]
      min_size       = 3
      max_size       = 50
      desired_size   = 5

      labels = {
        role = "swarm"
      }

      taints = [{
        key    = "dedicated"
        value  = "swarm"
        effect = "NO_SCHEDULE"
      }]

      tags = {
        Environment = var.environment
        NodeGroup   = "swarm"
      }
    }

    # AI processing nodes (GPU-optional)
    ai = {
      name           = "jobhunt-ai"
      instance_types = ["t3.xlarge"]
      min_size       = 1
      max_size       = 10
      desired_size   = 2

      labels = {
        role = "ai-processing"
      }

      tags = {
        Environment = var.environment
        NodeGroup   = "ai"
      }
    }
  }

  # Cluster access
  enable_cluster_creator_admin_permissions = true

  tags = {
    Environment = var.environment
    Project     = "jobhunt-pro"
  }
}

# ─── RDS PostgreSQL (Multi-AZ) ───────────────────────────────

resource "aws_db_subnet_group" "jobhunt" {
  name       = "${var.cluster_name}-db"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.cluster_name}-db-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.cluster_name}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_rds_cluster" "jobhunt" {
  cluster_identifier = "${var.cluster_name}-db"
  engine             = "aurora-postgresql"
  engine_version     = "15.4"
  database_name      = "jobhunt_pro"
  master_username    = "jobhunt"
  master_password    = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.jobhunt.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  storage_encrypted = true
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "${var.cluster_name}-final-snapshot"

  tags = {
    Environment = var.environment
  }
}

resource "aws_rds_cluster_instance" "jobhunt" {
  count              = 2
  identifier         = "${var.cluster_name}-db-${count.index}"
  cluster_identifier = aws_rds_cluster.jobhunt.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.jobhunt.engine
  engine_version     = aws_rds_cluster.jobhunt.engine_version

  performance_insights_enabled = true

  tags = {
    Environment = var.environment
  }
}

# ─── ElastiCache Redis ───────────────────────────────────────

resource "aws_elasticache_replication_group" "jobhunt" {
  replication_group_id = "${var.cluster_name}-redis"
  description          = "JobHunt Pro Redis cluster"

  node_type            = "cache.r6g.large"
  num_cache_clusters   = 2
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.jobhunt.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  automatic_failover_enabled = true
  multi_az_enabled           = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_elasticache_subnet_group" "jobhunt" {
  name       = "${var.cluster_name}-redis"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.cluster_name}-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ─── S3 Bucket (CVs, Assets) ────────────────────────────────

resource "aws_s3_bucket" "assets" {
  bucket = "${var.cluster_name}-assets"

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# ─── CloudWatch Alarms ──────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.cluster_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EKS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "EKS cluster CPU utilization > 80%"

  dimensions = {
    ClusterName = var.cluster_name
  }
}

# ─── Outputs ─────────────────────────────────────────────────

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "rds_endpoint" {
  value = aws_rds_cluster.jobhunt.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.jobhunt.primary_endpoint_address
}

output "s3_bucket" {
  value = aws_s3_bucket.assets.id
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
