from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from database import get_db
from auth_utils import verify_token

router = APIRouter(prefix="/api", tags=["Sales Details"])

class DailySalesSummary(BaseModel):
    """Daily sales summary for a bill"""
    billdate: date = Field(..., description="Sales date")
    billno: int = Field(..., description="Bill number")
    sno: Optional[str] = Field(None, description="Serial number")
    cuscod: str = Field(..., description="Customer code")
    cusnam: Optional[str] = Field(None, description="Customer name")
    adrone: Optional[str] = Field(None, description="Address line 1")
    adrtwo: Optional[str] = Field(None, description="Address line 2")
    phone: Optional[str] = Field(None, description="Phone number")
    tqty: float = Field(..., description="Total quantity")
    net: float = Field(..., description="Net amount")

    class Config:
        json_schema_extra = {
            "example": {
                "billdate": "2026-01-01",
                "billno": 26207,
                "sno": "1",
                "cuscod": "B0020",
                "cusnam": "John Doe",
                "adrone": "123 Main St",
                "adrtwo": "Apt 4B",
                "phone": "1234567890",
                "tqty": 10.0,
                "net": 1000.00
            }
        }


class CustomerSalesDetail(BaseModel):
    """Individual sales detail row with customer and item information"""
    billdate: date = Field(..., description="Sales date")
    billno: int = Field(..., description="Bill number")
    sno: Optional[str] = Field(None, description="Serial number")
    cuscod: str = Field(..., description="Customer code")
    cusnam: Optional[str] = Field(None, description="Customer name")
    adrone: Optional[str] = Field(None, description="Address line 1")
    adrtwo: Optional[str] = Field(None, description="Address line 2")
    phone: Optional[str] = Field(None, description="Phone number")
    salmannam: Optional[str] = Field(None, description="Salesman name")
    salmanphon: Optional[str] = Field(None, description="Salesman phone")
    managername: Optional[str] = Field(None, description="Manager name")
    managerphon: Optional[str] = Field(None, description="Manager phone")
    name: str = Field(..., description="Item name")
    rate: float = Field(..., description="Item rate")
    qty: float = Field(..., description="Item quantity")
    tprice: float = Field(..., description="Total item price")
    prcostrate: float = Field(..., description="Item cost rate")
    profit_loss: float = Field(..., description="Profit or loss for the item")
    tqty: float = Field(..., description="Total quantity")
    net: float = Field(..., description="Net amount")

    class Config:
        json_schema_extra = {
            "example": {
                "billdate": "2026-01-01",
                "billno": 26207,
                "sno": "1",
                "cuscod": "B0020",
                "cusnam": "John Doe",
                "adrone": "123 Main St",
                "adrtwo": "Apt 4B",
                "phone": "1234567890",
                "salmannam": "Alice Smith",
                "salmanphon": "0987654321",
                "managername": "Bob Johnson",
                "managerphon": "1122334455",
                "name": "Product A",
                "rate": 100.00,
                "qty": 2.0,
                "tprice": 200.00,
                "prcostrate": 80.00,
                "profit_loss": 40.00,
                "tqty": 2.0,
                "net": 200.00
            }
        }

class SalesDetailRequest(BaseModel):
    """Request model for fetching sales details"""
    billdate: date = Field(..., description="Sales date")
    billno: int = Field(..., description="Bill number", gt=0)
    cuscod: str = Field(..., description="Customer code", min_length=1, max_length=5)

    class Config:
        json_schema_extra = {
            "example": {
                "billdate": "2026-01-01",
                "billno": 26207,
                "cuscod": "B0020"
            }
        }


@router.post(
    "/sales-details",
    response_model=List[CustomerSalesDetail],
    summary="Get Customer Sales Details",
    description="Retrieve detailed sales information for a specific bill including customer info and all items"
)
async def get_sales_details(
    request: SalesDetailRequest,
    token: str = Depends(verify_token)
):
    """
    Get complete sales details for a specific bill.

    Returns:
    - Customer information (name, address, phone)
    - All items in the bill with quantities and prices
    - Bill totals

    **Requires authentication.**
    """
    connection = None
    cursor = None

    try:
        connection = get_db()
        cursor = connection.cursor(dictionary=True)

        # Call stored procedure
        cursor.callproc(
            'get_customer_sales_full_details',
            [request.billdate, request.billno, request.cuscod]
        )

        # Fetch results
        results = []
        for result in cursor.stored_results():
            results = result.fetchall()

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No sales details found for the specified bill."
            )

        # Convert column names to lowercase for Pydantic
        formatted_results = []
        for row in results:
            formatted_row = {
                'billdate': row['DATE'],
                'billno': row['BILLNO'],
                'sno': row.get('SNO'),
                'cuscod': row['CUSCOD'],
                'cusnam': row.get('CUSNAM'),
                'adrone': row.get('ADRONE'),
                'adrtwo': row.get('ADRTWO'),
                'phone': row.get('PHONE'),
                'salmannam': row.get('SALMANNAM'),
                'salmanphon': row.get('SALMANPHON'),
                'managername': row.get('MANAGERNAME'),
                'managerphon': row.get('MANAGERPHON'),
                'name': row.get('NAME') or '',
                'rate': float(row['RATE']) if row['RATE'] else 0.0,
                'qty': float(row['QTY']) if row['QTY'] else 0.0,
                'tprice': float(row['TPRICE']) if row['TPRICE'] else 0.0,
                'prcostrate': float(row['PRCOSTRATE']) if row['PRCOSTRATE'] else 0.0,
                'profit_loss': float(row['PROFIT_LOSS']) if row['PROFIT_LOSS'] else 0.0,
                'tqty': float(row['TQTY']) if row['TQTY'] else 0.0,
                'net': float(row['NET']) if row['NET'] else 0.0
            }
            formatted_results.append(formatted_row)

        return formatted_results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sales details: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/current-day-customer-sales", response_model=List[DailySalesSummary])
async def get_daily_sales_summary(token: str = Depends(verify_token)):
    """
    Get all sales orders placed today (current date).
    Returns a summary list without individual item details.
    """
    connection = None
    cursor = None

    try:
        # Get database connection
        connection = get_db()
        cursor = connection.cursor(dictionary=True)

        # Call stored procedure to get today's sales
        cursor.callproc('get_customer_sales_details')

        # Fetch results from the stored procedure
        results = []
        for result in cursor.stored_results():
            results = result.fetchall()

        if not results:
            return []  # Return empty list if no sales today

        # Convert column names to lowercase for Pydantic
        formatted_results = []
        for row in results:
            formatted_row = {
                'billdate': row['DATE'],
                'billno': row['BILLNO'],
                'sno': row.get('SNO'),
                'cuscod': row['CUSCOD'],
                'cusnam': row.get('CUSNAM'),
                'adrone': row.get('ADRONE'),
                'adrtwo': row.get('ADRTWO'),
                'phone': row.get('PHONE'),
                'tqty': float(row['TQTY']) if row['TQTY'] else 0.0,
                'net': float(row['NET']) if row['NET'] else 0.0
            }
            formatted_results.append(formatted_row)

        return formatted_results

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch daily sales summary: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
