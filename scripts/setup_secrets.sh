#!/bin/bash

# Setup AWS Secrets Manager for Trial Balance API
# Run this script after configuring AWS CLI with your credentials

set -e

REGION="ap-south-1"
DB_SECRET_NAME="trial-balance-db-secret"
JWT_SECRET_NAME="trial-balance-jwt-secret"

echo "🔐 Setting up AWS Secrets Manager..."
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI is configured"
echo ""

# Prompt for database credentials
read -p "Enter RDS Endpoint (e.g., xxx.rds.amazonaws.com): " DB_HOST
read -p "Enter Database Name (default: udayam_25_26_281225): " DB_NAME
DB_NAME=${DB_NAME:-udayam_25_26_281225}
read -p "Enter Database Username (default: admin): " DB_USER
DB_USER=${DB_USER:-admin}
read -sp "Enter Database Password: " DB_PASSWORD
echo ""
echo ""

# Generate JWT secret
echo "🔑 Generating JWT secret..."
JWT_SECRET=$(openssl rand -hex 32)
echo "Generated JWT_SECRET: $JWT_SECRET"
echo ""

# Create database secret
echo "📦 Creating database secret: $DB_SECRET_NAME"
aws secretsmanager create-secret \
  --name "$DB_SECRET_NAME" \
  --description "Database credentials for Trial Balance API" \
  --secret-string "{\"host\":\"$DB_HOST\",\"database\":\"$DB_NAME\",\"user\":\"$DB_USER\",\"password\":\"$DB_PASSWORD\"}" \
  --region "$REGION" 2>/dev/null && echo "✅ Database secret created" || echo "⚠️  Secret already exists, updating..."

# Update if already exists
aws secretsmanager update-secret \
  --secret-id "$DB_SECRET_NAME" \
  --secret-string "{\"host\":\"$DB_HOST\",\"database\":\"$DB_NAME\",\"user\":\"$DB_USER\",\"password\":\"$DB_PASSWORD\"}" \
  --region "$REGION" &>/dev/null && echo "✅ Database secret updated"

# Create JWT secret
echo "📦 Creating JWT secret: $JWT_SECRET_NAME"
aws secretsmanager create-secret \
  --name "$JWT_SECRET_NAME" \
  --description "JWT secret for Trial Balance API authentication" \
  --secret-string "{\"JWT_SECRET\":\"$JWT_SECRET\"}" \
  --region "$REGION" 2>/dev/null && echo "✅ JWT secret created" || echo "⚠️  Secret already exists, updating..."

# Update if already exists
aws secretsmanager update-secret \
  --secret-id "$JWT_SECRET_NAME" \
  --secret-string "{\"JWT_SECRET\":\"$JWT_SECRET\"}" \
  --region "$REGION" &>/dev/null && echo "✅ JWT secret updated"

echo ""
echo "✅ Secrets created successfully!"
echo ""
echo "📋 IAM Policy Required for Lambda:"
echo ""
cat << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:$REGION:*:secret:$DB_SECRET_NAME-*",
        "arn:aws:secretsmanager:$REGION:*:secret:$JWT_SECRET_NAME-*"
      ]
    }
  ]
}
EOF
echo ""
echo "🔧 Lambda Environment Variables:"
echo "DB_SECRET_NAME=$DB_SECRET_NAME"
echo "JWT_SECRET_NAME=$JWT_SECRET_NAME"
echo "AWS_REGION=$REGION"
echo ""
echo "📝 Next Steps:"
echo "1. Attach the above IAM policy to your Lambda execution role"
echo "2. Set the environment variables in Lambda Console"
echo "3. Deploy your updated code with './deploy_lambda.sh'"
echo ""
