from fastapi import FastAPI, Request, Response
import logging
import os
import boto3
from routers import auth, companies, trial_balance_store, trial_balance, logout, sales_details, auth_check, token
from mangum import Mangum

app = FastAPI(
    title="Trial Balance API",
    description="Multi-company trial balance reporting API",
    version="2.0.0"
)

# SNS and crash logging setup
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")  # Set this in Lambda env vars if using SNS
if SNS_TOPIC_ARN:
    sns_client = boto3.client("sns")
else:
    sns_client = None

# Crash logging endpoint
@app.post("/log-error")
async def log_error(request: Request):
    data = await request.json()
    logging.error(f"APP CRASH REPORT: {data}")

    # Example: Alert if error contains critical keywords
    error_message = str(data.get("error", ""))
    if sns_client and SNS_TOPIC_ARN:
        if "null value" in error_message.lower() or "critical" in error_message.lower():
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="🚨 App Crash Alert",
                Message=f"Critical error reported:\n\n{data}"
            )
    return {"success": True}

handler = Mangum(app, lifespan="off")

# CORS middleware
@app.middleware("http")
async def security_headers_middleware(
    request: Request,
    call_next
):
    response: Response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    return response

# Include routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(trial_balance.router)
app.include_router(trial_balance_store.router)
app.include_router(sales_details.router)
app.include_router(logout.router)
app.include_router(auth_check.router)
app.include_router(token.router)

@app.get("/")
def root():
    return {
        "message": "Trial Balance API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "login": "/auth/login",
            "companies": "/api/companies",
            "trial_balance": "/api/trial-balance",
            "trial_balance_store": "/api/trial-balance-store",
            "sales_details": "/api/sales-details",
            "refresh_token": "/auth/refresh",
            "logout": "/auth/logout",
            "auth_check": "/auth/check"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
