#!/bin/bash

echo "Starting Lambda deployment package creation..."

# Clean old package and zip
echo "Cleaning old package..."
rm -rf package aws_lambda.zip

# Create package directory
echo "Creating package directory..."
mkdir -p package

# Install dependencies using Docker (ensures Linux compatibility for Lambda)
echo "Installing dependencies using Docker..."
docker run --rm \
  -v "$PWD":/var/task \
  -w /var/task \
  public.ecr.aws/sam/build-python3.10 \
  bash -c "pip install --upgrade pip && pip install -r requirements.txt -t /var/task/package --no-cache-dir"

# Copy application files
echo "Copying application files..."
cp -r routers package/
cp main.py auth_utils.py config.py database.py package/

# Copy .env file (if it exists and you want it in Lambda - optional)
# cp .env package/

# Create zip file
echo "Creating deployment package..."
cd package
zip -r ../aws_lambda.zip . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"
cd ..

echo "✅ Deployment package created: aws_lambda.zip"
echo ""
echo "Next steps:"
echo "1. Upload aws_lambda.zip to AWS Lambda Console"
echo "   OR"
echo "2. Use AWS CLI:"
echo "   aws lambda update-function-code --function-name UDAYAM-FASTAPI --zip-file fileb://aws_lambda.zip"
echo ""
echo "Don't forget to set Lambda environment variables/ aws secret manager:"
echo "  - DB_HOST"
echo "  - DB_USER"
echo "  - DB_PASSWORD"
echo "  - DB_NAME"
echo "  - JWT_SECRET_KEY"
