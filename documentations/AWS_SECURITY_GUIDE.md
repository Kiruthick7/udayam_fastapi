# AWS Lambda + API Gateway Security Guide

## 🔒 Essential Security Measures

### 1. API Gateway Security

#### Rate Limiting & Throttling
```
API Gateway Console → Stages → $default → Throttle Settings
```
- **Default throttle**: 10,000 requests/second
- **Burst limit**: 5,000 requests
- **Recommended for production**:
  - Rate: 1000 req/s
  - Burst: 2000 req/s

#### Enable CloudWatch Logging
```
API Gateway Console → Settings → CloudWatch log format
```
- Enable **Access Logging**
- Enable **Execution Logging** (Info level)
- Log format: JSON for easy parsing

#### Enable Request Validation
```
API Gateway Console → Routes → Configure
```
- Validate request body
- Validate request parameters
- Reject malformed requests early

#### Enable AWS WAF (Web Application Firewall)
```
AWS WAF Console → Create Web ACL → Associate with API Gateway
```
**Recommended Rules:**
- SQL injection protection
- XSS (Cross-site scripting) protection
- Rate-based rule (block IPs exceeding 2000 req/5min)
- Geographic restrictions (if needed)
- Known bad inputs blocking

**Cost**: ~$5-10/month + $0.60 per million requests

### 2. Lambda Function Security

#### IAM Role - Least Privilege
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:Vpc": "arn:aws:ec2:region:account:vpc/vpc-xxxxx"
        }
      }
    }
  ]
}
```

#### Enable VPC Configuration
```
Lambda Console → Configuration → VPC
```
- Place Lambda in **private subnet**
- Use **NAT Gateway** for internet access (if needed)
- **Security group rules**:
  - Outbound: Allow MySQL (3306) to RDS security group
  - Inbound: None needed

#### Environment Variables Encryption
```
Lambda Console → Configuration → Environment variables → Encryption
```
- Enable encryption at rest using **AWS KMS**
- Use **Customer Managed Key (CMK)** for better control
- Encrypt sensitive values: `DB_PASSWORD`, `JWT_SECRET`

#### Enable Reserved Concurrency
```
Lambda Console → Configuration → Concurrency
```
- Set **Reserved concurrency**: 100-500 (based on needs)
- Prevents cost overruns from DDoS
- Ensures predictable billing

#### Lambda Function URL (Disable if using API Gateway)
```
Lambda Console → Configuration → Function URL
```
- **Delete Function URL** (use API Gateway only)
- Prevents bypassing API Gateway security

### 3. Database (RDS) Security

#### Network Security
```
RDS Console → Connectivity & security → Security groups
```
**Inbound Rules:**
- Type: MySQL/Aurora (3306)
- Source: Lambda security group
- Description: Allow Lambda access only

**Outbound Rules:**
- All traffic denied (default)

#### Encryption
```
RDS Console → Configuration → Encryption
```
- Enable **encryption at rest** (use AWS KMS)
- Enable **encryption in transit** (SSL/TLS)
- Enforce SSL connections in MySQL:
  ```sql
  GRANT USAGE ON *.* TO 'admin'@'%' REQUIRE SSL;
  ```

#### Automated Backups
```
RDS Console → Maintenance & backups
```
- Enable **automated backups** (7-35 days retention)
- Enable **backup encryption**
- Enable **Enhanced Monitoring** (1 minute granularity)

#### Parameter Group Settings
```
RDS Console → Parameter groups
```
- `max_connections`: 100 (adjust based on Lambda concurrency)
- `log_bin_trust_function_creators`: 1 (for stored procedures)
- `slow_query_log`: 1 (monitor slow queries)

### 4. Secrets Management

#### AWS Secrets Manager (Recommended)
```python
# database.py - Production version
import boto3
import json
from botocore.exceptions import ClientError

def get_db_credentials():
    """Load credentials from AWS Secrets Manager"""
    secret_name = "trial-balance-db-secret"
    region_name = "ap-south-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_value['SecretString'])
        return {
            'host': secret['host'],
            'database': secret['database'],
            'user': secret['username'],
            'password': secret['password']
        }
    except ClientError as e:
        raise e
```

**Create Secret:**
```bash
aws secretsmanager create-secret \
  --name trial-balance-db-secret \
  --description "Database credentials for Trial Balance API" \
  --secret-string '{
    "host":"your-rds-endpoint.amazonaws.com",
    "username":"admin",
    "password":"your-secure-password",
    "database":"udayam_25_26_281225"
  }'
```

**IAM Permission for Lambda:**
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:ap-south-1:*:secret:trial-balance-db-secret-*"
}
```

**Cost**: ~$0.40/month per secret + $0.05 per 10,000 API calls

### 5. Monitoring & Alerting

#### CloudWatch Alarms
```
CloudWatch Console → Alarms → Create alarm
```

**Recommended Alarms:**

1. **Lambda Errors**
   - Metric: Errors
   - Threshold: > 10 in 5 minutes
   - Action: SNS email notification

2. **Lambda Throttles**
   - Metric: Throttles
   - Threshold: > 0
   - Action: SNS email notification

3. **API Gateway 4XX/5XX Errors**
   - Metric: 4XXError / 5XXError
   - Threshold: > 50 in 5 minutes
   - Action: SNS email notification

4. **RDS CPU Usage**
   - Metric: CPUUtilization
   - Threshold: > 80%
   - Action: SNS email notification

5. **RDS Database Connections**
   - Metric: DatabaseConnections
   - Threshold: > 80 (or 80% of max_connections)
   - Action: SNS email notification

#### AWS X-Ray Tracing
```
Lambda Console → Configuration → Monitoring tools
```
- Enable **Active tracing**
- Trace API Gateway → Lambda → RDS flow
- Identify performance bottlenecks

**Add to requirements.txt:**
```
aws-xray-sdk==2.12.0
```

**Add to main.py:**
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

xray_recorder.configure(service='trial-balance-api')
```

### 6. Additional Security Best Practices

#### Input Validation
```python
# routers/auth.py
from pydantic import BaseModel, EmailStr, constr

class LoginRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: constr(min_length=8, max_length=100)  # Length validation
```

#### SQL Injection Prevention
- ✅ Using parameterized queries (already implemented)
- ✅ Using mysql-connector-python (safe by default)
- ❌ Never use string concatenation for SQL

#### JWT Security
```python
# auth_utils.py - Add token blacklist
from datetime import datetime
import redis

# Initialize Redis for token blacklist
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def revoke_token(token: str):
    """Add token to blacklist"""
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    exp = decoded.get('exp')
    ttl = exp - datetime.utcnow().timestamp()
    redis_client.setex(f"revoked:{token}", int(ttl), "1")

def is_token_revoked(token: str) -> bool:
    """Check if token is revoked"""
    return redis_client.exists(f"revoked:{token}") > 0
```

#### Password Policy
```python
# auth_utils.py - Add password strength validation
import re

def validate_password_strength(password: str) -> bool:
    """
    Password must contain:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True
```

### 7. Compliance & Audit

#### Enable CloudTrail
```
CloudTrail Console → Create trail
```
- Log all API Gateway API calls
- Log all Lambda function invocations
- Store logs in S3 (encrypted)
- Retain for 90+ days

#### Enable VPC Flow Logs
```
VPC Console → VPC → Flow logs
```
- Monitor all network traffic
- Detect unusual patterns
- Identify unauthorized access attempts

#### Regular Security Audits
- Run **AWS Trusted Advisor** weekly
- Run **AWS Security Hub** for compliance checks
- Review IAM permissions quarterly
- Update dependencies monthly

## 📋 Security Checklist

### Critical (Must-Have)
- [ ] API Gateway throttling enabled (1000 req/s)
- [ ] Lambda in VPC with private subnet
- [ ] RDS in private subnet
- [ ] RDS security group restricts access to Lambda only
- [ ] Environment variables encrypted with KMS
- [ ] JWT secret is strong random string
- [ ] SSL/TLS enabled for RDS
- [ ] Automated RDS backups enabled
- [ ] CloudWatch alarms configured
- [ ] IAM roles use least privilege

### Recommended
- [ ] AWS WAF enabled with SQL injection rules
- [ ] AWS Secrets Manager for credentials
- [ ] Reserved concurrency configured
- [ ] X-Ray tracing enabled
- [ ] CloudTrail logging enabled
- [ ] VPC Flow Logs enabled
- [ ] Password strength validation
- [ ] Request body validation

### Optional (Advanced)
- [ ] Token blacklist with Redis
- [ ] Multi-region deployment
- [ ] DDoS mitigation with AWS Shield
- [ ] API versioning
- [ ] Rate limiting per user/IP
- [ ] Geo-blocking with AWS WAF

## 💰 Estimated Security Costs

| Service | Monthly Cost | Description |
|---------|--------------|-------------|
| Lambda (with security) | $5-20 | Includes VPC NAT Gateway |
| AWS WAF | $5-10 | Basic rules + 1M requests |
| Secrets Manager | $0.40 | Per secret |
| CloudWatch Logs | $0.50-2 | 5GB logs per month |
| CloudTrail | $2 | First trail free, logs in S3 |
| KMS | $1 | Customer managed key |
| **Total** | **$13-35/month** | For small-medium traffic |

## 🚨 Incident Response Plan

1. **Detect**: CloudWatch alarms notify via email/SMS
2. **Assess**: Check CloudWatch Logs and X-Ray traces
3. **Contain**: Disable Lambda function or API Gateway
4. **Eradicate**: Fix vulnerability, rotate credentials
5. **Recover**: Redeploy with fixes
6. **Review**: Update security measures

## 📚 Resources

- [AWS Lambda Security Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html)
- [API Gateway Security](https://docs.aws.amazon.com/apigateway/latest/developerguide/security.html)
- [RDS Security](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.html)
- [AWS WAF Rules](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups.html)
