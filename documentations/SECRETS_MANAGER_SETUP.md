# AWS Secrets Manager Migration Guide

## ✅ Changes Made

Your code has been updated to use **AWS Secrets Manager** instead of Lambda environment variables for sensitive credentials.

### Updated Files:
1. **database.py** - Loads DB credentials from Secrets Manager
2. **config.py** - Loads JWT_SECRET from Secrets Manager
3. **requirements.txt** - Added `boto3==1.34.19`
4. **setup_secrets.sh** - Script to create secrets in AWS

## 📋 Setup Instructions

### Step 1: Create Secrets in AWS

Run the provided script (requires AWS CLI configured):

```bash
./setup_secrets.sh
```

This will:
- Prompt for your RDS database credentials
- Generate a secure JWT secret
- Create two secrets in AWS Secrets Manager:
  - `trial-balance-db-secret` (database credentials)
  - `trial-balance-jwt-secret` (JWT secret)

**Or create manually:**

```bash
# Database secret
aws secretsmanager create-secret \
  --name trial-balance-db-secret \
  --description "Database credentials for Trial Balance API" \
  --secret-string '{"host":"your-rds-endpoint.amazonaws.com","database":"udayam_25_26_281225","user":"admin","password":"your-password"}' \
  --region ap-south-1

# JWT secret
aws secretsmanager create-secret \
  --name trial-balance-jwt-secret \
  --description "JWT secret for Trial Balance API" \
  --secret-string '{"JWT_SECRET":"your-generated-secret-from-openssl-rand-hex-32"}' \
  --region ap-south-1
```

### Step 2: Update Lambda IAM Role

Add this policy to your Lambda execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-south-1:*:secret:trial-balance-db-secret-*",
        "arn:aws:secretsmanager:ap-south-1:*:secret:trial-balance-jwt-secret-*"
      ]
    }
  ]
}
```

**To attach via Console:**
1. Go to **Lambda Console** → Your Function → **Configuration** → **Permissions**
2. Click on the **Role name** (opens IAM)
3. Click **Add permissions** → **Create inline policy**
4. Paste the JSON above → **Review policy** → Name it → **Create policy**

**To attach via CLI:**
```bash
aws iam put-role-policy \
  --role-name your-lambda-execution-role \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets-policy.json
```

### Step 3: Set Lambda Environment Variables

Set these environment variables in Lambda Console:

| Variable | Value | Required |
|----------|-------|----------|
| `DB_SECRET_NAME` | `trial-balance-db-secret` | Yes |
| `JWT_SECRET_NAME` | `trial-balance-jwt-secret` | Yes |
| `AWS_REGION` | `ap-south-1` | Yes |

**Via Console:**
Lambda Console → Configuration → Environment variables → Edit

**Via CLI:**
```bash
aws lambda update-function-configuration \
  --function-name your-function-name \
  --environment Variables="{DB_SECRET_NAME=trial-balance-db-secret,JWT_SECRET_NAME=trial-balance-jwt-secret,AWS_REGION=ap-south-1}"
```

### Step 4: Deploy Updated Code

```bash
./deploy_lambda.sh
```

Upload the generated `aws_lambda.zip` to Lambda Console.

## 🔍 How It Works

### Database Credentials (database.py)

```python
def get_db_credentials():
    # In Lambda: Loads from Secrets Manager
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        secret = secretsmanager.get_secret_value(SecretId="trial-balance-db-secret")
        return json.loads(secret['SecretString'])

    # Local dev: Loads from .env file
    else:
        return {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            ...
        }
```

### JWT Secret (config.py)

```python
def get_jwt_secret():
    # In Lambda: Loads from Secrets Manager
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        secret = secretsmanager.get_secret_value(SecretId="trial-balance-jwt-secret")
        return json.loads(secret['SecretString'])['JWT_SECRET']

    # Local dev: Loads from .env file
    else:
        return os.getenv("JWT_SECRET")
```

### Caching
- Credentials are cached in memory after first load
- Reduces API calls to Secrets Manager
- Lambda containers reuse credentials across invocations

## 🧪 Local Development

Your `.env` file continues to work for local development:

```env
DB_HOST=your-rds-endpoint.amazonaws.com
DB_NAME=udayam_25_26_281225
DB_USER=admin
DB_PASSWORD=your-password
JWT_SECRET=your-local-jwt-secret
```

The code automatically detects if it's running in Lambda (`AWS_LAMBDA_FUNCTION_NAME` env var) and uses Secrets Manager only in production.

## 💰 Cost

- **Storage**: $0.40/month per secret
- **API Calls**: $0.05 per 10,000 calls

**Total**: ~$0.80/month for 2 secrets (with caching, API calls are minimal)

## 🔐 Security Benefits

✅ No hardcoded credentials in code
✅ No plain text secrets in Lambda environment variables
✅ Centralized secret management
✅ Automatic encryption at rest
✅ Secret rotation support (future)
✅ Audit trail via CloudTrail

## 🚨 Troubleshooting

### Error: "AccessDeniedException"
- IAM role doesn't have `secretsmanager:GetSecretValue` permission
- Check the IAM policy is attached to Lambda execution role

### Error: "ResourceNotFoundException"
- Secret name doesn't match environment variable
- Verify `DB_SECRET_NAME` and `JWT_SECRET_NAME` are correct

### Error: "Failed to load database credentials"
- Secret JSON format is incorrect
- Must have keys: `host`, `database`, `user`, `password`

### Local development not working
- Ensure `.env` file exists with all variables
- Run `source venv/bin/activate` before testing locally

## 📝 Secret JSON Format

### trial-balance-db-secret
```json
{
  "host": "your-rds-endpoint.rds.amazonaws.com",
  "database": "udayam_25_26_281225",
  "user": "admin",
  "password": "your-secure-password"
}
```

### trial-balance-jwt-secret
```json
{
  "JWT_SECRET": "your-64-character-hex-string"
}
```

## 🔄 Rotating Secrets

### Manual Rotation:
```bash
# Update database password
aws secretsmanager update-secret \
  --secret-id trial-balance-db-secret \
  --secret-string '{"host":"...","database":"...","user":"...","password":"NEW_PASSWORD"}' \
  --region ap-south-1

# Update JWT secret
aws secretsmanager update-secret \
  --secret-id trial-balance-jwt-secret \
  --secret-string '{"JWT_SECRET":"NEW_SECRET"}' \
  --region ap-south-1
```

Lambda will automatically use new secrets on next cold start (or force by updating function config).

## ✅ Verification

After deployment, check CloudWatch Logs for:

```
Loaded database credentials from Secrets Manager: trial-balance-db-secret
Loaded JWT secret from Secrets Manager: trial-balance-jwt-secret
Created database connection pool to your-rds-endpoint.rds.amazonaws.com
```

If you see these messages, Secrets Manager is working correctly! 🎉
