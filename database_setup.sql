-- Trial Balance Database Setup
-- Run this script on your MySQL database

-- Step 1: Add indexes for performance

-- Check before creating
SHOW INDEX FROM DAYBUK;
SHOW INDEX FROM SHOPSTKGODOWN;
SHOW INDEX FROM SHOPINVESTMENT;

-- Drop existing indexes if they exist
DROP INDEX idx_daybuk_main ON DAYBUK;
DROP INDEX idx_daybuk_cash ON DAYBUK;
DROP INDEX idx_stock ON SHOPSTKGODOWN;
DROP INDEX idx_invest ON SHOPINVESTMENT;

-- Create index normally
CREATE INDEX idx_daybuk_main ON DAYBUK (comp, GRPCOD, TRNDAT, DBCR);
CREATE INDEX idx_daybuk_cash ON DAYBUK (CUSCOD, ABC3, TRNDAT);

-- SHOPSTKGODOWN
CREATE INDEX idx_stock ON SHOPSTKGODOWN (FIRCOD);

-- SHOPINVESTMENT
CREATE INDEX idx_invest ON SHOPINVESTMENT (FIRCOD, DATE);

-- DAYBUK
CREATE INDEX idx_daybuk_grp_trndat ON DAYBUK (GRPCOD, TRNDAT);
CREATE INDEX idx_daybuk_cuscod_trndat ON DAYBUK (CUSCOD, TRNDAT);
CREATE INDEX idx_daybuk_jrt ON DAYBUK (JRT3, DBCR, TRNDAT);

-- PRCUSMAS
CREATE INDEX idx_prcusmas_bank ON PRCUSMAS (GRPCOD, TPLCOD, CUSCOD);

-- STKMAS
CREATE INDEX idx_stkmas_root ON STKMAS (ROOT);


-- Step 2: Create users table for app authentication
CREATE TABLE IF NOT EXISTS USERS4_CHECK (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test user (password: 'password')
-- Password hash generated with password_gen.py
INSERT INTO USERS4_CHECK (email, password_hash, role) VALUES
('admin@example.com',
 '$2b$12$pcssEvP/ykQJ2XFnetlzh.3CFSTlaMPX3JJ/Cch2OI7RbW63PCBEu',
 'admin'),

('user@example.com',
 '$2b$12$Q1HtCV6K3AxtAOmfGnFYDO72Ef4XrW25eWBDyta3PpbF0yPvUmAKC',
 'user');

-- Step 3: Create stored procedure for trial balance calculation

DELIMITER $$

DROP PROCEDURE IF EXISTS get_trial_balance_shop $$

CREATE PROCEDURE get_trial_balance_shop (
    IN p_company_code VARCHAR(5),
    IN p_scgrpcod VARCHAR(5),
    IN p_sdgrpcod VARCHAR(5),
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    DECLARE v_supplier_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_customer_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_arul_cash_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_gheeta_cash_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_vijay_cash_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_main_advance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_salary_advance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_rr_closing_stock DECIMAL(15,2) DEFAULT 0;
    DECLARE v_bank_liability_total DECIMAL(15,2) DEFAULT 0;
    DECLARE v_bank_asset_total DECIMAL(15,2) DEFAULT 0;
    DECLARE v_liability_total DECIMAL(15,2) DEFAULT 0;
    DECLARE v_assets_total DECIMAL(15,2) DEFAULT 0;
    DECLARE v_net_total DECIMAL(15,2) DEFAULT 0;


    -- ===============================
    -- SALARY BALANCE AMOUNT (SUN01)
    -- ===============================



    -- ===============================
    -- ALL SUPPLIERS BALANCE (SUN01)
    -- ===============================
    SELECT
        COALESCE(SUM(
            CASE
                WHEN DBCR='C' THEN TRNAMT
                WHEN DBCR='D' THEN -TRNAMT
            END
        ),0)
    INTO v_supplier_balance
    FROM DAYBUK
    WHERE GRPCOD = p_scgrpcod
    AND TRNDAT >= p_start_date;

    -- ====================================
    -- ALL CUSTOMERS BALANCE
    -- ====================================
    SELECT
        COALESCE(SUM(CASE WHEN DBCR='D' THEN TRNAMT ELSE -TRNAMT END),0)
    INTO v_customer_balance
    FROM DAYBUK
    WHERE GRPCOD = p_sdgrpcod
      AND TRNDAT >= p_start_date;

    -- ====================================
    -- ARUL CASH BALANCE
    -- ====================================
    SELECT COALESCE(SUM(CASE WHEN DBCR='D' THEN TRNAMT ELSE -TRNAMT END),0)
    INTO v_arul_cash_balance
    FROM DAYBUK
    WHERE CUSCOD='CAS01' AND ABC3='GHE01'
      AND TRNTYP NOT IN ('4','5')
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ====================================
    -- GHEETA CASH BALANCE
    -- ====================================
    SELECT COALESCE(SUM(CASE WHEN DBCR='D' THEN TRNAMT ELSE -TRNAMT END),0)
    INTO v_gheeta_cash_balance
    FROM DAYBUK
    WHERE CUSCOD='CAS01' AND ABC3='PRO01'
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ====================================
    -- VIJAY CASH BALANCE
    -- ====================================
    SELECT COALESCE(SUM(CASE WHEN DBCR='D' THEN TRNAMT ELSE -TRNAMT END),0)
    INTO v_vijay_cash_balance
    FROM DAYBUK
    WHERE CUSCOD='CAS01' AND ABC3='ACC01'
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ====================================
    -- MAIN ADVANCE
    -- ====================================
    SELECT COALESCE(SUM(
        CASE
            WHEN JRT3='2' AND DBCR='D' THEN TRNAMT
            WHEN (JRT3='4' OR (TRNTYP='3' AND JRT='3' AND TRNDET LIKE '%MAIN ADVANCE DUE CREDIT'))
                 AND DBCR='C' THEN -TRNAMT
            ELSE 0
        END
    ),0)
    INTO v_main_advance
    FROM DAYBUK
    WHERE TRNDAT >= p_start_date;


    -- ====================================
    -- SALARY ADVANCE
    -- ====================================
    SELECT
        COALESCE(
            SUM(
                CASE
                    WHEN JRT3 = '1' AND DBCR = 'D' THEN TRNAMT
                    WHEN JRT3 = '3' AND DBCR = 'C' THEN -TRNAMT
                    ELSE 0
                END
            ),
            0
        )
    INTO v_salary_advance
    FROM DAYBUK
    WHERE TRNDAT>=p_start_date AND TRNDAT<=p_end_date;

    -- ====================================
    -- RR CLOSING STOCK VALUE
    -- ====================================
    SELECT COALESCE(SUM(
        CASE WHEN ROOT='GHEE' THEN QTY*PRCOSTRATE ELSE QTY*BOXPRODRATE END
    ),0)
    INTO v_rr_closing_stock
    FROM STKMAS;

    -- ===============================
    -- PRODUCTION CLOSING STOCK VALUE
    -- ===============================


    -- ===============================
    -- TOTAL CALCULATIONS
    -- ===============================

    -- ===============================
    -- BANK LIABILITY TOTAL
    -- ===============================
    SELECT COALESCE(SUM(
        CASE
            WHEN d.DBCR='C' THEN d.TRNAMT
            WHEN d.DBCR='D' THEN -d.TRNAMT
        END
    ),0)
    INTO v_bank_liability_total
    FROM PRCUSMAS p
    JOIN DAYBUK d ON d.CUSCOD = p.CUSCOD
    WHERE p.GRPCOD='CAS02'
    AND p.TPLCOD='L'
    AND d.TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ===============================
    -- BANK ASSET TOTAL
    -- ===============================
    SELECT COALESCE(SUM(
        CASE
            WHEN d.DBCR='D' THEN d.TRNAMT
            WHEN d.DBCR='C' THEN -d.TRNAMT
        END
    ),0)
    INTO v_bank_asset_total
    FROM PRCUSMAS p
    JOIN DAYBUK d ON d.CUSCOD = p.CUSCOD
    WHERE p.GRPCOD='CAS02'
    AND p.TPLCOD='A'
    AND d.TRNDAT BETWEEN p_start_date AND p_end_date;


    -- ===============================
    -- LIABILITY CALCULATION
    -- ===============================
    SET v_liability_total = v_supplier_balance + v_bank_liability_total;

    -- ===============================
    -- ASSETS CALCULATION
    -- ===============================
    SET v_assets_total =
        v_customer_balance
        + v_arul_cash_balance
        + v_gheeta_cash_balance
        + v_vijay_cash_balance
        + v_main_advance
        + v_salary_advance
        + v_rr_closing_stock
        + v_bank_asset_total;

    -- ===============================
    -- NET TOTAL CALCULATION
    -- ===============================
    SET v_net_total = v_assets_total - v_liability_total;

    -- ===============================
    -- FINAL RESULT SET
    -- ===============================

    SELECT 'ALL SUPPLIERS BALANCE'    AS category, v_supplier_balance as amount, 'LIABILITY' AS type

    -- ===============================
    -- LIST ALL BANKS (LIABILITY)
    -- ===============================

    UNION ALL
    SELECT
        p.CUSNAM AS category,
        SUM(
            CASE
                WHEN d.DBCR='C' THEN d.TRNAMT
                WHEN d.DBCR='D' THEN -d.TRNAMT
            END
        ) AS amount,
        'LIABILITY' AS type
    FROM PRCUSMAS p
    LEFT JOIN DAYBUK d
        ON d.CUSCOD = p.CUSCOD
    AND d.TRNDAT BETWEEN p_start_date AND p_end_date
    WHERE p.GRPCOD = 'CAS02' AND p.TPLCOD = 'L'
    GROUP BY p.CUSNAM, p.TPLCOD
    HAVING amount <> 0

    UNION ALL
    SELECT 'TOTAL LIABILITIES', v_liability_total, 'LIABILITY'

    -- ===============================
    -- CUSTOMER & CASH ASSETS
    -- ===============================
    UNION ALL
    SELECT 'ALL CUSTOMER BALANCE', v_customer_balance, 'ASSET'
    UNION ALL
    SELECT 'ARUL CASH BALANCE', v_arul_cash_balance, 'ASSET'
    UNION ALL
    SELECT 'GHEETA CASH BALANCE', v_gheeta_cash_balance, 'ASSET'
    UNION ALL
    SELECT 'VIJAY CASH BALANCE', v_vijay_cash_balance, 'ASSET'
    UNION ALL
    SELECT 'MAIN ADVANCE', v_main_advance, 'ASSET'
    UNION ALL
    SELECT 'SALARY ADVANCE', v_salary_advance, 'ASSET'

    -- ===============================
    -- LIST ALL BANKS (ASSETS)
    -- ===============================

    UNION ALL
    SELECT
        p.CUSNAM AS category,
        SUM(
            CASE
                WHEN d.DBCR='D' THEN d.TRNAMT
                WHEN d.DBCR='C' THEN -d.TRNAMT
            END
        ) AS amount,
        'ASSET' AS type
    FROM PRCUSMAS p
    LEFT JOIN DAYBUK d
        ON d.CUSCOD = p.CUSCOD
    AND d.TRNDAT BETWEEN p_start_date AND p_end_date
    WHERE p.GRPCOD = 'CAS02' AND p.TPLCOD = 'A'
    GROUP BY p.CUSNAM, p.TPLCOD
    HAVING amount <> 0

    UNION ALL
    SELECT 'RR CLOSING STOCK VALUE', v_rr_closing_stock, 'ASSET'
    UNION ALL
    SELECT 'TOTAL ASSETS', v_assets_total, 'ASSET'
    UNION ALL
    SELECT 'NET TOTAL', v_net_total, 'NET';

END $$

DELIMITER ;


-- Step 4: Create stored procedure for trial balance store calculation

DELIMITER $$

DROP PROCEDURE IF EXISTS get_trial_balance_shop_store $$

CREATE PROCEDURE get_trial_balance_shop_store (
    IN p_company_code VARCHAR(5),
    IN p_scgrpcod VARCHAR(5),
    IN p_sdgrpcod VARCHAR(5),
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    -- ===============================
    -- Declare variables
    -- ===============================
    DECLARE v_customer_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_petty_cash DECIMAL(15,2) DEFAULT 0;
    DECLARE v_vijay_cash DECIMAL(15,2) DEFAULT 0;
    DECLARE v_vijay_shop_cash DECIMAL(15,2) DEFAULT 0;
    DECLARE v_stock_value DECIMAL(15,2) DEFAULT 0;
    DECLARE v_supplier_balance DECIMAL(15,2) DEFAULT 0;
    DECLARE v_investment DECIMAL(15,2) DEFAULT 0;
    DECLARE v_gross_total DECIMAL(15,2) DEFAULT 0;
    DECLARE v_net_profit DECIMAL(15,2) DEFAULT 0;

    -- ===============================
    -- CUSTOMER BALANCE (SUN04)
    -- ===============================
    SELECT
        COALESCE(SUM(CASE WHEN DBCR = 'D' THEN TRNAMT ELSE -TRNAMT END), 0)
    INTO v_customer_balance
    FROM DAYBUK
    WHERE comp = p_company_code
      AND GRPCOD = p_sdgrpcod
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ===============================
    -- PETTY CASH (CAS01)
    -- ===============================
    SELECT
        COALESCE(SUM(
            CASE
                WHEN DBCR = 'D' AND TRNTYP IN ('1','5') THEN TRNAMT
                WHEN DBCR = 'C' AND TRNTYP IN ('2','5') THEN -TRNAMT
            END
        ), 0)
    INTO v_petty_cash
    FROM DAYBUK
    WHERE CUSCOD = 'CAS01'
      AND ABC3 = p_company_code
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ===============================
    -- VIJAY CASH (ACC01)
    -- ===============================
    SELECT
        COALESCE(SUM(
            CASE
                WHEN DBCR = 'D' AND (TRNTYP='1' OR (TRNTYP='3' AND JRT='1')) THEN TRNAMT
                WHEN DBCR = 'C' AND (TRNTYP='2' OR (TRNTYP='3' AND JRT='2')) THEN -TRNAMT
            END
        ), 0)
    INTO v_vijay_cash
    FROM DAYBUK
    WHERE ABC3 = 'ACC01'
      AND comp = p_company_code
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ===============================
    -- VIJAY SHOP CASH IN HAND (SUN09)
    -- ===============================
    SELECT
        COALESCE(SUM(CASE WHEN DBCR='D' THEN TRNAMT ELSE -TRNAMT END), 0)
    INTO v_vijay_shop_cash
    FROM DAYBUK
    WHERE GRPCOD = 'SUN09'
      AND comp = p_company_code
      AND TRNDAT BETWEEN p_start_date AND p_end_date;

    -- ===============================
    -- CURRENT STOCK VALUE
    -- ===============================
    SELECT
        COALESCE(SUM((QTY * PURRATE) + ((QTY * PURRATE) * (TAX / 100))), 0)
    INTO v_stock_value
    FROM SHOPSTKGODOWN
    WHERE FIRCOD = p_company_code;

    -- ===============================
    -- SUPPLIER BALANCE (SUN10)
    -- ===============================
    SELECT
        COALESCE(SUM(CASE WHEN DBCR='D' THEN TRNAMT ELSE -TRNAMT END), 0)
    INTO v_supplier_balance
    FROM DAYBUK
    WHERE comp = p_company_code
      AND GRPCOD = p_scgrpcod
      AND TRNDAT >=p_start_date;

    -- ===============================
    -- INVESTMENT
    -- ===============================
    SELECT
        COALESCE(SUM(AMT), 0)
    INTO v_investment
    FROM SHOPINVESTMENT
    WHERE FIRCOD = p_company_code
      AND DATE BETWEEN p_start_date AND p_end_date;

    -- ===============================
    -- GROSS TOTAL & NET PROFIT
    -- ===============================
    SET v_gross_total =
          v_customer_balance
        + v_petty_cash
        + v_vijay_cash
        + v_vijay_shop_cash
        + v_stock_value
        + v_supplier_balance;

    SET v_net_profit = v_gross_total - v_investment;

    -- ===============================
    -- FINAL RESULT SET
    -- ===============================
    SELECT 'CUSTOMER BALANCE'        AS category, v_customer_balance AS amount, 'ASSET' AS type
    UNION ALL
    SELECT 'PETTY CASH AT SHOP',     v_petty_cash, 'ASSET' AS type
    UNION ALL
    SELECT 'VIJAY CASH BALANCE',     v_vijay_cash, 'ASSET' AS type
    UNION ALL
    SELECT 'VIJAY SHOP CASH IN HAND',v_vijay_shop_cash, 'ASSET' AS type
    UNION ALL
    SELECT 'CURRENT STOCK VALUE',    v_stock_value, 'ASSET' AS type
    UNION ALL
    SELECT 'SUPPLIER BALANCE',       v_supplier_balance, 'LIABILITY' AS type
    UNION ALL
    SELECT 'GROSS TOTAL',            v_gross_total, 'ASSET' AS type
    UNION ALL
    SELECT 'INVESTMENT',             v_investment, 'LIABILITY' AS type
    UNION ALL
    SELECT 'NET PROFIT',             v_net_profit, 'LIABILITY' AS type;

END $$

DELIMITER ;

-- Test the stored procedure
-- Replace 'SHOP1' with your actual company code
-- CALL get_trial_balance_shop('SHOP1', '2023-04-01', '2024-03-31');
