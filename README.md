# Trial Balance API

FastAPI backend for multi-company trial balance reporting.

## Setup

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
Create `.env` file with:
```
JWT_SECRET=your-secret-key-here
AWS_REGION=us-east-1
DB_SECRET_NAME=your-db-secret-name
DB_HOST=localhost
DB_NAME=your_database_name
DB_USER=root
DB_PASSWORD=your_password
```

4. **Run database setup:**
Execute the SQL scripts in `database/` folder to create:
- Users table
- Indexes
- Stored procedure `get_trial_balance_shop()`

5. **Run the API:**
```bash
uvicorn main:app --reload
```

API will be available at: http://localhost:8000

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `POST /auth/login` - Authenticate user
- `GET /api/companies` - List all companies
- `POST /api/trial-balance` - Get trial balance report
- `POST /api/trial-balance_store` - Get trial balance report of stores

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'
```
