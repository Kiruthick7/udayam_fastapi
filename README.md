# Udayam Trial Balance API

FastAPI backend for multi-company trial balance reporting, deployed on AWS Lambda with MySQL database.

> **Security Note**: This README uses example values. Replace all placeholders with your actual values. Never commit actual secrets, credentials, or production URLs to version control.

## Architecture

- **Runtime**: Python 3.10 on AWS Lambda
- **Database**: MySQL with connection pooling
- **Authentication**: JWT with access & refresh tokens
- **Secrets**: AWS Secrets Manager
- **Deployment**: Lambda + API Gateway

## Local Development Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
Create `.env` file for local development:
```env
JWT_SECRET=your-secret-key-here
DB_HOST=localhost
DB_NAME=your_database_name
DB_USER=root
DB_PASSWORD=your_password
DB_PORT=3306
```

For production (Lambda), secrets are managed via AWS Secrets Manager:
- `your-app-db-secret` - Database credentials (JSON format with host, username, password, database)
- `your-app-jwt-secret` - JWT secret key

Example secret structure:
```json
// Database secret (your-app-db-secret)
{
  "host": "your-rds-endpoint.region.rds.amazonaws.com",
  "username": "your_db_user",
  "password": "your_db_password",
  "database": "your_database_name"
}

// JWT secret (your-app-jwt-secret)
{
  "secret_key": "your-long-random-secret-key-here"
}
```

See [AWS_SECURITY_GUIDE.md](AWS_SECURITY_GUIDE.md) for setup instructions.

4. **Run database setup:**
Execute the SQL scripts in `database/` folder to create:
- Users table
- Indexes
- Stored procedure `get_trial_balance_shop()`
- Stored procedure `get_customer_sales_full_details()` with manager/salesman information

5. **Run the API:**
```bash
uvicorn main:app --reload
```

API will be available at: http://localhost:8000

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Production: https://your-api-id.execute-api.region.amazonaws.com/docs

## Endpoints

### Authentication
- `POST /auth/login` - Authenticate user, returns access + refresh tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Revoke tokens

### Reports
- `GET /api/companies` - List all companies (requires auth)
- `POST /api/trial-balance` - Get trial balance report (requires auth)
- `POST /api/trial-balance_store` - Get trial balance for stores (requires auth)
- `POST /api/daily-sales` - Get daily sales summary (requires auth)
- `POST /api/sales-details` - Get detailed sales for a specific bill (requires auth)

### Health Check
- `GET /health` - API health status

## Testing

```bash
# Test health endpoint (local)
curl http://localhost:8000/health

# Test health endpoint (production)
curl https://your-api-id.execute-api.region.amazonaws.com/health

# Test login (local)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'

# Test login (production)
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'
```

## Production Deployment

### Prerequisites
- AWS CLI configured with appropriate credentials
- Docker installed (for building Lambda package)
- AWS Lambda function created
- API Gateway configured
- AWS Secrets Manager secrets created

### Build Lambda Package

```bash
# Build deployment package with Linux-compatible dependencies
./deploy_lambda.sh
```

This creates `aws_lambda.zip` (~42MB) with all dependencies compiled for Linux ARM64.

### Deploy to Lambda

**Option 1: Via AWS Console**
1. Go to Lambda Console
2. Upload `aws_lambda.zip` (if < 50MB)
3. Configure environment variables:
   - `DB_SECRET_NAME=your-app-db-secret`
   - `JWT_SECRET_NAME=your-app-jwt-secret`
   - `AWS_REGION=your-aws-region` (e.g., us-east-1, ap-south-1)

**Option 2: Via S3 (for packages > 50MB)**
```bash
# Manual steps (requires AWS CLI):
# 1. Create S3 bucket
aws s3 mb s3://your-lambda-deployments

# 2. Upload package
aws s3 cp aws_lambda.zip s3://your-lambda-deployments/

# 3. Update Lambda function
aws lambda update-function-code \
  --function-name your-function-name \
  --s3-bucket your-lambda-deployments \
  --s3-key aws_lambda.zip
```

### Lambda Configuration
- **Runtime**: Python 3.10
- **Handler**: `main.handler`
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Architecture**: arm64 (Graviton2)

## Key Features

- JWT authentication with token refresh
- Token revocation on logout
- AWS Secrets Manager integration
- Environment detection (Lambda vs local)
- Connection pooling for MySQL
- Automatic token verification
- CORS configured for mobile app
- Daily sales reports with detailed breakdowns
- Sales detail view with customer information
- Manager and salesman contact information via stored procedures
- Comprehensive error handling and validation

## Security

- All secrets stored in AWS Secrets Manager
- No credentials in code or environment variables
- JWT with short-lived access tokens
- Token revocation table for logout
- Secure password hashing

## Documentation

- [AWS Security Guide](AWS_SECURITY_GUIDE.md) - Secrets Manager setup
- [AWS Console Setup Guide](AWS_CONSOLE_SETUP_GUIDE.md) - Step-by-step Lambda deployment
- [Secrets List](SECRETS_LIST.md) - Required AWS secrets

## Troubleshooting

**Lambda Import Errors:**
- Ensure native extensions are compiled for Linux
- Use Docker build in `deploy_lambda.sh`
- Check Lambda logs in CloudWatch

**Database Connection Issues:**
- Verify security groups allow Lambda → RDS
- Check Secrets Manager secret format
- Ensure database credentials are correct

**API Gateway 502 Errors:**
- Check Lambda execution logs
- Verify Lambda timeout is sufficient
- Check memory allocation
