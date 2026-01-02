# 🖥️ AWS Secrets Manager Setup - Console UI Guide

## Step-by-Step Guide for AWS Console

---

## Part 1: Create Database Secret

### Step 1: Open AWS Secrets Manager

1. Log in to **AWS Console**
2. Search for **"Secrets Manager"** in the top search bar
3. Click on **AWS Secrets Manager**
4. Click **"Store a new secret"** button (orange button)

### Step 2: Choose Secret Type

1. Select **"Other type of secret"**
2. In the **Key/value** section, click **"Plaintext"** tab
3. **Delete the default text** and paste this JSON:

```json
{
  "host": "softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com",
  "database": "udayam_25_26",
  "user": "admin",
  "password": "Softrend123!"
}
```

4. Keep **Encryption key** as default: `aws/secretsmanager`
5. Click **Next**

### Step 3: Configure Secret Name

1. **Secret name:** `trial-balance-db-secret`
2. **Description:** `Database credentials for Trial Balance API`
3. **Tags (optional):**
   - Key: `Application` | Value: `TrialBalance`
   - Key: `Environment` | Value: `Production`
4. Click **Next**

### Step 4: Configure Rotation (Skip for now)

1. Select **"Disable automatic rotation"**
2. Click **Next**

### Step 5: Review and Store

1. Review the secret details
2. Click **Store**
3. ✅ You should see: "Secret trial-balance-db-secret has been stored successfully"

---

## Part 2: Create JWT Secret

### Step 1: Generate JWT Secret

Open **Terminal** or **CloudShell** (in AWS Console):

```bash
openssl rand -hex 32
```

**Copy the output** (it will look like this):
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### Step 2: Create Secret in Console

1. In **Secrets Manager**, click **"Store a new secret"** again
2. Select **"Other type of secret"**
3. Click **"Plaintext"** tab
4. **Delete the default text** and paste this JSON (replace with your generated secret):

```json
{
  "JWT_SECRET": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"
}
```

5. Click **Next**

### Step 3: Configure Secret Name

1. **Secret name:** `trial-balance-jwt-secret`
2. **Description:** `JWT secret for Trial Balance API authentication`
3. Click **Next**

### Step 4: Skip Rotation and Store

1. Select **"Disable automatic rotation"**
2. Click **Next**
3. Review and click **Store**
4. ✅ You should see: "Secret trial-balance-jwt-secret has been stored successfully"

---

## Part 3: Verify Secrets Created

1. In **Secrets Manager** dashboard, you should now see:
   - `trial-balance-db-secret`
   - `trial-balance-jwt-secret`

2. Click on each secret to verify:
   - **Secret ARN** is displayed
   - **Last retrieved** shows "Never" (will change after Lambda uses it)

---

## Part 4: Add IAM Permissions to Lambda Role

### Step 1: Find Lambda Execution Role

1. Go to **Lambda Console** (search "Lambda" in top bar)
2. Click on your function (e.g., `trial-balance-api`)
3. Click **Configuration** tab
4. Click **Permissions** in left sidebar
5. Under **Execution role**, click the **Role name** link (opens IAM in new tab)

### Step 2: Add Secrets Manager Policy

1. In the IAM Role page, click **Add permissions** dropdown
2. Select **Create inline policy**
3. Click **JSON** tab
4. **Delete the default JSON** and paste this:

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

5. Click **Review policy**
6. **Policy name:** `SecretsManagerAccessPolicy`
7. **Description:** `Allow Lambda to read Trial Balance API secrets`
8. Click **Create policy**
9. ✅ You should see the policy listed under "Permissions policies"

---

## Part 5: Configure Lambda Environment Variables

### Step 1: Go to Lambda Configuration

1. Go back to **Lambda Console**
2. Click on your function
3. Click **Configuration** tab
4. Click **Environment variables** in left sidebar
5. Click **Edit** button

### Step 2: Remove Old Variables (if they exist)

**Remove these if present:**
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `JWT_SECRET`

Click the **Remove** button next to each.

### Step 3: Add New Variables

Click **Add environment variable** for each:

| Key | Value |
|-----|-------|
| `DB_SECRET_NAME` | `trial-balance-db-secret` |
| `JWT_SECRET_NAME` | `trial-balance-jwt-secret` |
| `AWS_REGION` | `ap-south-1` |

### Step 4: Save Changes

1. Click **Save** button
2. ✅ Lambda will update (takes a few seconds)

---

## Part 6: Deploy Updated Code

### Step 1: Build Lambda Package

In your **local terminal**:

```bash
cd /Users/h1598349/Personal/udayam/trial_balance_api
./deploy_lambda.sh
```

This creates `aws_lambda.zip` with boto3 included.

### Step 2: Upload to Lambda

#### Option A: Via Console (for files < 50MB)

1. Go to **Lambda Console** → Your function
2. Click **Code** tab
3. Click **Upload from** dropdown → **".zip file"**
4. Click **Upload**
5. Select `aws_lambda.zip` from your project folder
6. Click **Save**
7. Wait for upload to complete

#### Option B: Via S3 (for larger files)

1. Upload `aws_lambda.zip` to an S3 bucket first
2. In Lambda Console → **Upload from** → **Amazon S3 location**
3. Enter S3 URL: `s3://your-bucket/aws_lambda.zip`
4. Click **Save**

---

## Part 7: Test Your API

### Step 1: Test Login Endpoint

1. Go to **API Gateway Console**
2. Find your HTTP API: `h32dbgnyv3.execute-api.ap-south-1.amazonaws.com`
3. Copy the **Invoke URL**

### Step 2: Test with Curl

```bash
curl -X POST https://h32dbgnyv3.execute-api.ap-south-1.amazonaws.com/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"yourpassword"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

### Step 3: Check CloudWatch Logs

1. Go to **CloudWatch Console**
2. Click **Log groups**
3. Find `/aws/lambda/your-function-name`
4. Click on the latest **Log stream**
5. Look for these messages:

```
Loaded database credentials from Secrets Manager: trial-balance-db-secret
Created database connection pool to softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com
```

✅ **Success!** Your API is now using Secrets Manager!

---

## 🎯 Visual Checklist

- [ ] ✅ Created `trial-balance-db-secret` in Secrets Manager
- [ ] ✅ Created `trial-balance-jwt-secret` in Secrets Manager
- [ ] ✅ Added IAM policy to Lambda execution role
- [ ] ✅ Removed old environment variables from Lambda
- [ ] ✅ Added new environment variables (DB_SECRET_NAME, JWT_SECRET_NAME, AWS_REGION)
- [ ] ✅ Built new Lambda package with boto3
- [ ] ✅ Uploaded aws_lambda.zip to Lambda
- [ ] ✅ Tested API login endpoint successfully
- [ ] ✅ Verified CloudWatch logs show Secrets Manager loading

---

## 🔍 Troubleshooting

### Issue: "AccessDeniedException" in CloudWatch logs

**Cause:** Lambda role doesn't have permission to read secrets

**Fix:**
1. Go to IAM → Roles → Your Lambda role
2. Check if `SecretsManagerAccessPolicy` is attached
3. Verify the policy JSON has correct secret ARNs
4. Make sure region in ARN matches `ap-south-1`

### Issue: "ResourceNotFoundException"

**Cause:** Secret name doesn't match environment variable

**Fix:**
1. Go to Secrets Manager → Verify exact secret names
2. Go to Lambda → Environment variables
3. Ensure `DB_SECRET_NAME=trial-balance-db-secret` (exact match)
4. Ensure `JWT_SECRET_NAME=trial-balance-jwt-secret` (exact match)

### Issue: "JWT_SECRET not found in Secrets Manager"

**Cause:** Secret JSON format is wrong

**Fix:**
1. Go to Secrets Manager → Click `trial-balance-jwt-secret`
2. Click **Retrieve secret value**
3. Click **Edit**
4. Verify JSON has `JWT_SECRET` key (case-sensitive):
   ```json
   {"JWT_SECRET": "your-secret-here"}
   ```
5. Click **Save**

### Issue: Local development not working

**Cause:** `.env` file missing

**Fix:**
1. Create `.env` in project root:
   ```env
   JWT_SECRET=dev-secret-key
   DB_HOST=softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com
   DB_NAME=udayam_25_26
   DB_USER=admin
   DB_PASSWORD=Softrend123!
   ```

---

## 📊 Secret Values Reference

### trial-balance-db-secret (Plaintext JSON)
```json
{
  "host": "softrend.civ3ldnimjay.ap-south-1.rds.amazonaws.com",
  "database": "udayam_25_26",
  "user": "admin",
  "password": "Softrend123!"
}
```

### trial-balance-jwt-secret (Plaintext JSON)
```json
{
  "JWT_SECRET": "your-64-character-hex-string-from-openssl"
}
```

---

## 🔄 Updating Secrets Later

### Update Database Password

1. Go to **Secrets Manager**
2. Click `trial-balance-db-secret`
3. Click **Retrieve secret value**
4. Click **Edit**
5. Update the password in JSON
6. Click **Save**
7. Lambda will use new password on next cold start

### Force Lambda to Use New Secret

1. Go to **Lambda Console** → Your function
2. Click **Configuration** → **Environment variables**
3. Click **Edit** → Click **Save** (no changes needed)
4. This forces Lambda to restart and reload secrets

---

## 💰 Cost Summary

- **2 secrets**: $0.40 × 2 = **$0.80/month**
- **API calls** (with caching): **~$0.05/month**
- **Total**: **~$0.85/month**

---

## 🎉 You're Done!

Your Trial Balance API is now securely using AWS Secrets Manager for all sensitive credentials. No more hardcoded secrets in environment variables!

**Next Steps:**
- Set up secret rotation (optional)
- Enable AWS CloudTrail for secret access auditing
- Test your Flutter app with the deployed API
