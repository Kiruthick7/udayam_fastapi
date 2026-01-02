# 🔐 AWS Secrets Manager - Complete Secret Values Guide

## Secrets to Store in AWS Secrets Manager

Based on your Trial Balance API application, here are **ALL** the secret values that should be stored in AWS Secrets Manager:

---

## 1️⃣ Database Credentials Secret

**Secret Name:** `trial-balance-db-secret`

**Purpose:** MySQL RDS database connection credentials

**JSON Format:**
```json
{
  "host": "softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com",
  "database": "udayam_25_26",
  "user": "admin",
  "password": "Softrend123!"
}
```

**Required Fields:**
- `host` - RDS endpoint URL
- `database` - Database name
- `user` - Database username
- `password` - Database password (⚠️ MOST SENSITIVE)

**Create via CLI:**
```bash
aws secretsmanager create-secret \
  --name trial-balance-db-secret \
  --description "Database credentials for Trial Balance API" \
  --secret-string '{"host":"softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com","database":"udayam_25_26","user":"admin","password":"Softrend123!"}' \
  --region ap-south-1
```

---

## 2️⃣ JWT Authentication Secret

**Secret Name:** `trial-balance-jwt-secret`

**Purpose:** JWT token signing and verification

**JSON Format:**
```json
{
  "JWT_SECRET": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"
}
```

**Required Fields:**
- `JWT_SECRET` - Strong random string (64+ characters recommended)

**Generate secure JWT secret:**
```bash
openssl rand -hex 32
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**Create via CLI:**
```bash
JWT_SECRET=$(openssl rand -hex 32)

aws secretsmanager create-secret \
  --name trial-balance-jwt-secret \
  --description "JWT secret for Trial Balance API authentication" \
  --secret-string "{\"JWT_SECRET\":\"$JWT_SECRET\"}" \
  --region ap-south-1
```

---

## 📋 Summary Table

| Secret Name | Contains | Sensitivity Level | Used By |
|-------------|----------|-------------------|---------|
| `trial-balance-db-secret` | DB host, database name, username, password | 🔴 CRITICAL | database.py |
| `trial-balance-jwt-secret` | JWT signing key | 🔴 CRITICAL | config.py, auth_utils.py |

---

## 🚫 Values That Should NOT Be in Environment Variables

After migrating to Secrets Manager, these should NOT be in Lambda environment variables:

❌ `DB_HOST`
❌ `DB_NAME`
❌ `DB_USER`
❌ `DB_PASSWORD`
❌ `JWT_SECRET`

---

## ✅ Values That CAN Remain in Environment Variables

These are **configuration values** (not secrets) and can stay in Lambda environment variables:

✅ `AWS_REGION` - Public AWS region identifier (e.g., "ap-south-1")
✅ `DB_SECRET_NAME` - Name of the secret to fetch (not the secret itself)
✅ `JWT_SECRET_NAME` - Name of the JWT secret to fetch
✅ `JWT_ALGORITHM` - Algorithm name (e.g., "HS256") - **optional, has default**
✅ `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time - **optional, has default**

---

## 🔧 Quick Setup Script

Run the automated setup script included in your project:

```bash
cd /Users/h1598349/Personal/udayam/trial_balance_api
./setup_secrets.sh
```

This will:
1. Prompt for your database credentials
2. Generate a secure JWT secret
3. Create both secrets in AWS Secrets Manager
4. Output the required IAM policy

---

## 🔐 Manual Creation (Alternative)

If you prefer to create secrets manually:

### Step 1: Create Database Secret
```bash
aws secretsmanager create-secret \
  --name trial-balance-db-secret \
  --description "Database credentials for Trial Balance API" \
  --secret-string '{"host":"softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com","database":"udayam_25_26","user":"admin","password":"Softrend123!"}' \
  --region ap-south-1
```

### Step 2: Create JWT Secret
```bash
# Generate secure random string
JWT_SECRET=$(openssl rand -hex 32)
echo "Generated JWT_SECRET: $JWT_SECRET"

# Create secret
aws secretsmanager create-secret \
  --name trial-balance-jwt-secret \
  --description "JWT secret for Trial Balance API" \
  --secret-string "{\"JWT_SECRET\":\"$JWT_SECRET\"}" \
  --region ap-south-1
```

### Step 3: Verify Secrets Created
```bash
aws secretsmanager list-secrets --region ap-south-1 \
  --filters Key=name,Values=trial-balance
```

---

## 🔑 Lambda IAM Permissions Required

Your Lambda execution role needs this policy to access secrets:

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

**Attach via Console:**
1. Go to **IAM Console** → **Roles**
2. Find your Lambda execution role (e.g., `trial-balance-lambda-role`)
3. Click **Add permissions** → **Create inline policy**
4. Paste JSON above → Name: `SecretsManagerAccess` → Create

**Attach via CLI:**
```bash
aws iam put-role-policy \
  --role-name your-lambda-execution-role \
  --policy-name SecretsManagerAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["secretsmanager:GetSecretValue"],
        "Resource": [
          "arn:aws:secretsmanager:ap-south-1:*:secret:trial-balance-db-secret-*",
          "arn:aws:secretsmanager:ap-south-1:*:secret:trial-balance-jwt-secret-*"
        ]
      }
    ]
  }'
```

---

## 🌍 Lambda Environment Variables Configuration

After creating secrets in AWS Secrets Manager, configure these environment variables in Lambda:

| Variable | Value | Purpose |
|----------|-------|---------|
| `DB_SECRET_NAME` | `trial-balance-db-secret` | Name of DB credentials secret |
| `JWT_SECRET_NAME` | `trial-balance-jwt-secret` | Name of JWT secret |
| `AWS_REGION` | `ap-south-1` | AWS region where secrets are stored |

**Set via Console:**
Lambda Console → Configuration → Environment variables → Edit

**Set via CLI:**
```bash
aws lambda update-function-configuration \
  --function-name your-function-name \
  --environment "Variables={DB_SECRET_NAME=trial-balance-db-secret,JWT_SECRET_NAME=trial-balance-jwt-secret,AWS_REGION=ap-south-1}" \
  --region ap-south-1
```

---

## 🔄 Updating/Rotating Secrets

### Update Database Password
```bash
aws secretsmanager update-secret \
  --secret-id trial-balance-db-secret \
  --secret-string '{"host":"softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com","database":"udayam_25_26","user":"admin","password":"NEW_PASSWORD_HERE"}' \
  --region ap-south-1
```

### Update JWT Secret
```bash
NEW_JWT_SECRET=$(openssl rand -hex 32)

aws secretsmanager update-secret \
  --secret-id trial-balance-jwt-secret \
  --secret-string "{\"JWT_SECRET\":\"$NEW_JWT_SECRET\"}" \
  --region ap-south-1
```

**Note:** Lambda will automatically use new secrets on next cold start. To force immediate update:
```bash
aws lambda update-function-configuration \
  --function-name your-function-name \
  --description "Force update - $(date)"
```

---

## 💰 Cost Breakdown

| Item | Cost |
|------|------|
| Secret storage (2 secrets) | $0.80/month |
| API calls (with caching) | ~$0.05/month |
| **Total** | **~$0.85/month** |

---

## 🧪 Local Development

Your `.env` file remains unchanged for local development:

```env
# Local Development - .env file
JWT_SECRET=dev-secret-key-change-in-production
DB_HOST=softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com
DB_NAME=udayam_25_26
DB_USER=admin
DB_PASSWORD=Softrend123!
```

The code automatically detects Lambda environment and uses Secrets Manager only in production.

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Both secrets created in AWS Secrets Manager
- [ ] IAM policy attached to Lambda execution role
- [ ] Lambda environment variables set (DB_SECRET_NAME, JWT_SECRET_NAME, AWS_REGION)
- [ ] Lambda execution role has `secretsmanager:GetSecretValue` permission
- [ ] CloudWatch logs show: "Loaded database credentials from Secrets Manager"
- [ ] CloudWatch logs show: "Created database connection pool"
- [ ] API login endpoint works correctly

---

## 🚨 Security Best Practices

1. **Never commit secrets to Git**
   - `.env` is in `.gitignore`
   - Never hardcode secrets in code

2. **Rotate secrets regularly**
   - Database password: Every 90 days
   - JWT secret: Every 6-12 months

3. **Use different secrets per environment**
   - `trial-balance-db-secret-dev`
   - `trial-balance-db-secret-prod`

4. **Enable CloudTrail logging**
   - Track who accessed secrets
   - Audit secret modifications

5. **Use least privilege IAM**
   - Only grant `GetSecretValue` (not `PutSecretValue`)
   - Restrict to specific secret ARNs

---

## 📚 Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [Boto3 Secrets Manager Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [Secret Rotation Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html)

---

## 🆘 Troubleshooting

### Error: "ResourceNotFoundException"
**Cause:** Secret name doesn't exist or incorrect region
**Fix:** Verify secret name and region match

### Error: "AccessDeniedException"
**Cause:** Lambda role lacks `secretsmanager:GetSecretValue` permission
**Fix:** Attach IAM policy to Lambda execution role

### Error: "JWT_SECRET not found in Secrets Manager"
**Cause:** Secret JSON missing `JWT_SECRET` key
**Fix:** Update secret with correct JSON format

### Local dev error: "JWT_SECRET missing in environment"
**Cause:** `.env` file missing or not loaded
**Fix:** Create `.env` file with `JWT_SECRET=your-local-secret`

---

## 📞 Need Help?

1. Check CloudWatch Logs for detailed error messages
2. Verify secret JSON format matches exactly
3. Confirm IAM permissions are correctly attached
4. Test secret retrieval with AWS CLI:
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id trial-balance-db-secret \
     --region ap-south-1
   ```
