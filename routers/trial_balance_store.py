from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date
from database import get_db
# from auth import verify_token # type: ignore

router = APIRouter(prefix="/api", tags=["trial-balance"])


class TrialBalanceRequest(BaseModel):
    companyIds: List[str]  # Company codes as strings
    startDate: date
    endDate: date

class TrialBalanceRow(BaseModel):
    accountCode: str
    accountName: str
    accountType: str
    debit: float
    credit: float
    balance: float

class CompanyReport(BaseModel):
    companyId: str
    companyName: str
    period: dict
    rows: List[TrialBalanceRow]

@router.post("/trial-balance-store")
def get_trial_balance(
    request: TrialBalanceRequest,
):
    conn = get_db()
    companies_data = []

    try:
        for company_code in request.companyIds:
            cursor = conn.cursor(dictionary=True)
            rows = []

            try:
                cursor.execute(
                    "SELECT FIRNAME, SCGRPCOD, SDGRPCOD FROM FIRMASN WHERE FIRCOD = %s LIMIT 1",
                    (company_code,)
                )
                company_info = cursor.fetchone()

                if not company_info:
                    continue

                company_name = company_info["FIRNAME"]
                scgrpcod = company_info["SCGRPCOD"] or ""
                sdgrpcod = company_info["SDGRPCOD"] or ""

                # Call stored procedure with company-specific codes
                cursor.callproc(
                    "get_trial_balance_shop_store",
                    [company_code, scgrpcod, sdgrpcod, request.startDate, request.endDate]
                )

                for result in cursor.stored_results():
                    for row in result.fetchall():
                        category = row.get("category")
                        amount = float(row.get("amount") or 0)
                        acc_type = row.get("type")

                        debit = credit = balance = 0.0

                        if acc_type == "ASSET":
                            debit = amount
                            balance = amount
                        elif acc_type == "LIABILITY":
                            credit = abs(amount)
                            if category == "NET PROFIT":
                                balance = -abs(amount)
                            else:
                                balance = abs(amount)

                        rows.append({
                            "accountName": category,
                            "accountType": acc_type,
                            "debit": debit,
                            "credit": credit,
                            "balance": balance
                        })

                companies_data.append({
                    "companyId": company_code,
                    "companyName": company_name,
                    "period": {
                        "start": str(request.startDate),
                        "end": str(request.endDate)
                    },
                    "rows": rows,
                })

            finally:
                cursor.close()

        return {"companies": companies_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
