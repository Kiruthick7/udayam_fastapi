#!/bin/bash

# Test Production Code Locally
# This script simulates Lambda environment to test AWS Secrets Manager integration

echo "🧪 Testing Production Code Locally..."
echo ""
echo "This will:"
echo "1. Load database credentials from AWS Secrets Manager"
echo "2. Load JWT secret from AWS Secrets Manager"
echo "3. Run the API in production mode"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured!"
    echo "Run: aws configure"
    echo ""
    echo "You need:"
    echo "- AWS Access Key ID"
    echo "- AWS Secret Access Key"
    echo "- Default region: ap-south-1"
    exit 1
fi

echo "✅ AWS credentials configured"
echo ""

# Check secrets exist
echo "🔍 Checking secrets in AWS Secrets Manager..."

if aws secretsmanager get-secret-value --secret-id trial-balance-db-secret --region ap-south-1 &> /dev/null; then
    echo "✅ trial-balance-db-secret found"
else
    echo "❌ trial-balance-db-secret not found!"
    echo "Run: ./setup_secrets.sh"
    exit 1
fi

if aws secretsmanager get-secret-value --secret-id trial-balance-jwt-secret --region ap-south-1 &> /dev/null; then
    echo "✅ trial-balance-jwt-secret found"
else
    echo "❌ trial-balance-jwt-secret not found!"
    echo "Run: ./setup_secrets.sh"
    exit 1
fi

echo ""
echo "🚀 Starting server in PRODUCTION mode..."
echo "   (Using AWS Secrets Manager)"
echo ""

# Simulate Lambda environment
export AWS_LAMBDA_FUNCTION_NAME=test-local-production
export DB_SECRET_NAME=trial-balance-db-secret
export JWT_SECRET_NAME=trial-balance-jwt-secret
export AWS_REGION=ap-south-1

# Run uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
