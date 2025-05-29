terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Random ID for unique resource names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_vpc" "default" {
  default = true
}
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# S3 Bucket
resource "aws_s3_bucket" "main" {
  bucket = "candlestick-dev-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "candlestick-dev-${random_id.bucket_suffix.hex}"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_website_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.project_name}-oac"
  description                       = "OAC for ${var.bucket_name}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100" # Free tier compatible

  origin {
    domain_name              = aws_s3_bucket.main.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.main.id
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_s3_bucket.main.id

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name        = "${var.project_name}-cdn"
    Project     = var.project_name
    Environment = var.environment
  }
}

# S3 Bucket Policy for CloudFront
resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.main.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.main.arn
          }
        }
      }
    ]
  })
}

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"

  username_attributes = ["email"]
  
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
  }

  schema {
    name                = "wallet_address"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  tags = {
    Name        = "${var.project_name}-user-pool"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
}

# DynamoDB Table
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users"
  billing_mode = "PAY_PER_REQUEST" # Free tier: 25 GB storage, 25 WCU, 25 RCU

  hash_key = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "wallet_address"
    type = "S"
  }

  global_secondary_index {
    name            = "wallet_address_index"
    hash_key        = "wallet_address"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-users"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Lambda Function
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.main.arn}/*"
      }
    ]
  })
}

resource "aws_lambda_function" "solExtractor" {
  filename      = "lambda_function.zip"
  function_name = "solExtractor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.12"
  memory_size   = 128 # Free tier: 1M requests, 400,000 GB-seconds
  timeout       = 60

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.main.id
    }
  }

  tags = {
    Name        = "solExtractor"
    Project     = var.project_name
    Environment = var.environment
  }
}

# EventBridge Rule for Lambda
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "${var.project_name}-extractor-schedule"
  description         = "Trigger solExtractor every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "solExtractorTarget"
  arn       = aws_lambda_function.solExtractor.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.solExtractor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}

# ECR Repository
resource "aws_ecr_repository" "main" {
  name                 = "candlestick-nano-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false # Free tier doesn't include scanning
  }

  tags = {
    Name        = "candlestick-nano-repo"
    Project     = var.project_name
    Environment = var.environment
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled" # Keep costs down
  }

  tags = {
    Name        = "${var.project_name}-cluster"
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch Log Groups for ECS
resource "aws_cloudwatch_log_group" "ecs_buy_monitor" {
  name              = "/ecs/${var.project_name}/buy-monitor"
  retention_in_days = 1 # Minimize storage costs

  tags = {
    Name        = "${var.project_name}-buy-monitor-logs"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "ecs_exit_monitor" {
  name              = "/ecs/${var.project_name}/exit-monitor"
  retention_in_days = 1 # Minimize storage costs

  tags = {
    Name        = "${var.project_name}-exit-monitor-logs"
    Project     = var.project_name
    Environment = var.environment
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# EC2 Spot Instance Launch Template
resource "aws_launch_template" "spot" {
  name_prefix   = "${var.project_name}-spot-"
  image_id      = "ami-0c2d06d50ce30b442" # Amazon Linux 2 in us-west-2 (Free tier eligible)
  instance_type = "t2.micro" # Free tier: 750 hours/month

  instance_market_options {
    market_type = "spot"
    spot_options {
      max_price = "0.0035" # Well below on-demand price to ensure cost control
    }
  }

  monitoring {
    enabled = false # Keep costs down
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.project_name}-spot"
      Project     = var.project_name
      Environment = var.environment
    }
  }
}

# Auto Scaling Group for Spot Instance
resource "aws_autoscaling_group" "spot" {
  name                = "${var.project_name}-spot-asg"
  vpc_zone_identifier = data.aws_subnets.default.ids
  min_size            = 0
  max_size            = 1
  desired_capacity    = 1

  launch_template {
    id      = aws_launch_template.spot.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-spot-asg"
    propagate_at_launch = true
  }
}

# Budget Alerts
resource "aws_budgets_budget" "cost" {
  name         = "candlestick-budget"
  budget_type  = "COST"
  limit_amount = "1"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 85
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.notification_email]
  }
}

resource "aws_budgets_budget" "free_tier_usage" {
  name         = "${var.project_name}-free-tier-usage"
  budget_type  = "USAGE"
  limit_amount = "1"
  limit_unit   = "PERCENTAGE"
  time_unit    = "MONTHLY"

  cost_types {
    include_credit             = false
    include_discount           = true
    include_other_subscription = true
    include_recurring          = true
    include_refund             = false
    include_subscription       = true
    include_support            = true
    include_tax                = true
    include_upfront            = true
    use_blended                = false
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 85
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.notification_email]
  }
}

# Secrets Manager for API Keys
resource "aws_secretsmanager_secret" "api_keys" {
  name = "${var.project_name}-api-keys"

  tags = {
    Name        = "${var.project_name}-api-keys"
    Project     = var.project_name
    Environment = var.environment
  }
} 