# IAM Summary - Candlestick Nano AWS Infrastructure

## IAM Roles Created

### 1. Lambda Execution Role
**Role Name**: `Candlestick-lambda-role`  
**Service**: Lambda (solExtractor function)  

**Permissions**:
- **CloudWatch Logs**: 
  - `logs:CreateLogGroup`
  - `logs:CreateLogStream` 
  - `logs:PutLogEvents`
- **S3 Access**:
  - `s3:PutObject` on `candlestick-dev-7f861eee/*`
  - `s3:GetObject` on `candlestick-dev-7f861eee/*`

**Purpose**: Allows Lambda function to write logs and store extraction data in S3.

### 2. ECS Task Execution Role  
**Role Name**: `Candlestick-ecs-task-execution-role`  
**Service**: ECS Tasks  

**Permissions**:
- **Managed Policy**: `AmazonECSTaskExecutionRolePolicy`
  - Pull images from ECR
  - Write logs to CloudWatch
  - Access Secrets Manager (for task secrets)

**Purpose**: Allows ECS tasks to run containers and access required AWS services.

## Security Notes

### ✅ **Least Privilege Applied**
- Lambda role only accesses its specific S3 bucket
- ECS role uses AWS-managed policy with minimal required permissions
- No cross-service access beyond what's needed

### ✅ **Resource-Level Restrictions**
- S3 permissions scoped to specific bucket only
- CloudWatch logs scoped to account and region
- No wildcard (*) permissions on sensitive resources

### ✅ **Service-Linked Roles**
- Roles can only be assumed by their respective AWS services
- No human users can assume these roles directly

## Budget and Cost Monitoring

### Cost Budget
- **Name**: `candlestick-budget`
- **Limit**: $1.00 USD/month
- **Alert**: 85% threshold
- **Notification**: kaushalbalagurusamy@berkeley.edu

### Free Tier Usage Budget  
- **Name**: `Candlestick-free-tier-usage`
- **Limit**: 85% of Free Tier quotas
- **Notification**: kaushalbalagurusamy@berkeley.edu

## Secrets Management

**Secret ARN**: `arn:aws:secretsmanager:us-west-2:050451385533:secret:Candlestick-api-keys-JQBhJ3`

This secret should store:
- QuickNode API endpoints
- Trading API keys
- Other sensitive configuration

Access is granted only to services that need it (ECS tasks, Lambda functions). 