from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from database import get_db
from auth import verify_token # type: ignore

router = APIRouter(prefix="/api", tags=["companies"])

class Company(BaseModel):
    SNO_ID: int
    FIRCOD_ID: str
    FIRCOD: str
    FIRNAME: str
    SCGRPCOD: str
    SDGRPCOD: str

@router.get("/companies", response_model=List[Company])
def get_companies(current_user: dict = Depends(verify_token)):
# def get_companies():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get distinct companies from INVOCE table
        # query = """
        #     SELECT DISTINCT
        #         ROW_NUMBER() OVER (ORDER BY i.comp) as id,
        #         i.comp as code,
        #         COALESCE(
        #             (SELECT p.cusnam FROM PRCUSMAS p WHERE p.cuscod = i.comp LIMIT 1),
        #             i.comp
        #         ) as name
        #     FROM INVOCE i
        #     WHERE i.comp IS NOT NULL AND i.comp != ''
        #     ORDER BY i.comp
        # """
        # query= """
        #     SELECT * FROM FIRMASN;
        # """

        query = """
            SELECT
                SNO_ID,
                COALESCE(FIRCOD_ID, '') as FIRCOD_ID,
                COALESCE(FIRCOD, '') as FIRCOD,
                FIRNAME,
                COALESCE(SCGRPCOD, '') as SCGRPCOD,
                COALESCE(SDGRPCOD, '') as SDGRPCOD
            FROM FIRMASN
            WHERE FIRCOD IS NOT NULL
            AND FIRCOD != ''
            AND FIRNAME IS NOT NULL
            AND FIRNAME != ''
            ORDER BY SNO_ID
        """

        cursor.execute(query)
        companies = cursor.fetchall()

        return companies
    finally:
        cursor.close()
        conn.close()
