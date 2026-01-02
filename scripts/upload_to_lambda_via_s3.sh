#!/bin/bash

echo "🚀 Uploading Lambda deployment package via S3..."

# Configuration
FUNCTION_NAME="udayam-fastapi"
REGION="ap-south-1"
S3_BUCKET="udayam-lambda-deployments"  # Change this to your S3 bucket name
S3_KEY="trial-balance-api/aws_lambda.zip"
ZIP_FILE="aws_lambda.zip"

# Check if zip file exists
if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ Error: $ZIP_FILE not found!"
    echo "Run ./deploy_lambda.sh first to create the deployment package."
    exit 1
fi

echo ""
echo "📦 Package size: $(du -h $ZIP_FILE | cut -f1)"
echo ""

# Step 1: Create S3 bucket if it doesn't exist
echo "1️⃣  Checking if S3 bucket exists..."
if aws s3 ls "s3://$S3_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "   Creating S3 bucket: $S3_BUCKET"
    aws s3 mb "s3://$S3_BUCKET" --region "$REGION"
    echo "   ✅ Bucket created"
else
    echo "   ✅ Bucket already exists"
fi

# Step 2: Upload to S3
echo ""
echo "2️⃣  Uploading $ZIP_FILE to S3..."
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY" --region "$REGION"
if [ $? -eq 0 ]; then
    echo "   ✅ Upload successful"
else
    echo "   ❌ Upload failed"
    exit 1
fi

# Step 3: Update Lambda function code from S3
echo ""
echo "3️⃣  Updating Lambda function code..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$S3_BUCKET" \
    --s3-key "$S3_KEY" \
    --region "$REGION" \
    --output json

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Lambda function updated successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Verify environment variables are set in Lambda Console"
    echo "2. Test the function with /health endpoint"
    echo "3. Check CloudWatch logs if there are any errors"
else
    echo ""
    echo "❌ Lambda update failed"
    exit 1
fi
