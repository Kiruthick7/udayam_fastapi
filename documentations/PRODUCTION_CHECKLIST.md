# Production Deployment Checklist

## ✅ Code Ready
- [x] JWT authentication enabled
- [x] Password hashing with bcrypt
- [x] Proper error handling
- [x] Database connection pooling
- [x] Lambda handler configured
- [x] Clean production code (no debug logs)

## ⚠️ Configuration Required

### 1. AWS Lambda Environment Variables
Set these in Lambda Console → Configuration → Environment variables:

```
DB_HOST=your-rds-endpoint.amazonaws.com
DB_USER=admin
DB_PASSWORD=your-secure-password
DB_NAME=udayam_25_26_281225
JWT_SECRET=generate-with-openssl-rand-hex-32
```

Generate JWT secret:
```bash
openssl rand -hex 32
```

### 2. CORS Configuration
Update `main.py` line 16-21 with your actual frontend URLs:
```python
allow_origins=[
    "https://your-production-domain.com",
    "http://localhost:3000",  # Keep for local dev
]
```

### 3. Lambda Configuration
- **Handler**: `main.handler`
- **Runtime**: Python 3.10
- **Timeout**: 30 seconds
- **Memory**: 512 MB minimum

### 4. Database Security
- Ensure RDS security group allows Lambda security group access on port 3306
- If Lambda not in VPC, make RDS publicly accessible (not recommended)
- Better: Put Lambda in same VPC as RDS

### 5. API Gateway
- Stage: `$default`
- Enable throttling (recommended: 1000 requests/second)
- Enable CloudWatch logging

## 📦 Deployment Steps

1. **Build package**:
   ```bash
   ./deploy_lambda.sh
   ```

2. **Upload to Lambda**:
   - Manual: Upload `aws_lambda.zip` in Lambda Console
   - CLI: `aws lambda update-function-code --function-name YOUR_FUNCTION --zip-file fileb://aws_lambda.zip`

3. **Set environment variables** (see above)

4. **Test endpoints**:
   - GET `/health` - Should return `{"status": "healthy"}`
   - POST `/auth/login` - Test login
   - GET `/api/companies` - Test database connection

5. **Update Flutter app**:
   - Update API URL in `api_service.dart`

## 🔒 Security Recommendations

- [ ] Change JWT_SECRET to a strong random value
- [ ] Restrict CORS to specific domains
- [ ] Enable RDS encryption at rest
- [ ] Use AWS Secrets Manager for DB credentials (future enhancement)
- [ ] Enable API Gateway WAF for DDoS protection
- [ ] Set up CloudWatch alarms for errors
- [ ] Enable RDS automated backups

## 📊 Monitoring

- **CloudWatch Logs**: `/aws/lambda/YOUR_FUNCTION_NAME`
- **CloudWatch Metrics**: Lambda duration, errors, throttles
- **RDS Metrics**: CPU, connections, storage

## 🐛 Troubleshooting

### Login fails with "Internal Server Error"
- Check bcrypt is compiled correctly (use Docker build)
- Verify database connection
- Check CloudWatch logs

### "Unable to import module 'main'"
- Verify handler is set to `main.handler`
- Check all dependencies in requirements.txt

### Database connection timeout
- Check Lambda VPC configuration
- Verify security groups allow port 3306
- Check RDS is publicly accessible (if Lambda not in VPC)

## ✅ Production Ready Checklist
- [ ] All environment variables set in Lambda
- [ ] CORS configured with actual domains
- [ ] JWT_SECRET set to random secure value
- [ ] Lambda timeout increased to 30s
- [ ] Database security groups configured
- [ ] CloudWatch logging enabled
- [ ] API tested in production
- [ ] Flutter app updated with production URL
