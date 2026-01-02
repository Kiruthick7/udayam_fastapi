from fastapi import FastAPI, Request, Response
from routers import auth, companies, trial_balance_store, trial_balance, logout, sales_details
from mangum import Mangum

app = FastAPI(
    title="Trial Balance API",
    description="Multi-company trial balance reporting API",
    version="1.0.0"
)

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
            "sales_details": "/api/sales-details"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
