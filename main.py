from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, companies, trial_balance_store, trial_balance

app = FastAPI(
    title="Trial Balance API",
    description="Multi-company trial balance reporting API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(trial_balance.router)
app.include_router(trial_balance_store.router)


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
            "trial_balance_store": "/api/trial-balance-store"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
