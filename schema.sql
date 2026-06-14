-- =============================================================
-- schema.sql
-- E-Commerce Star Schema DDL + Bulk Load
-- PostgreSQL 15+
-- =============================================================

-- Drop tables in FK-safe order (fact first, then dims)
DROP TABLE IF EXISTS fact_sales    CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_products  CASCADE;
DROP TABLE IF EXISTS dim_stores    CASCADE;
DROP TABLE IF EXISTS dim_time      CASCADE;

-- =============================================================
-- DIMENSION TABLES
-- =============================================================

-- ── dim_customers ─────────────────────────────────────────────
CREATE TABLE dim_customers (
    customer_sk       SERIAL          PRIMARY KEY,
    customer_id       UUID            NOT NULL UNIQUE,
    first_name        VARCHAR(80)     NOT NULL,
    last_name         VARCHAR(80)     NOT NULL,
    email             VARCHAR(200)    NOT NULL UNIQUE,
    phone             VARCHAR(50),
    city              VARCHAR(100),
    state             VARCHAR(10),
    country           CHAR(2),
    gender            VARCHAR(10)     CHECK (gender IN ('M','F','Other')),
    age               SMALLINT        CHECK (age BETWEEN 18 AND 120),
    loyalty_tier      VARCHAR(20)     CHECK (loyalty_tier IN ('Bronze','Silver','Gold','Platinum')),
    registration_date DATE,
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── dim_products ──────────────────────────────────────────────
CREATE TABLE dim_products (
    product_sk        SERIAL          PRIMARY KEY,
    product_id        UUID            NOT NULL UNIQUE,
    product_name      VARCHAR(200)    NOT NULL,
    category          VARCHAR(80)     NOT NULL,
    sub_category      VARCHAR(80),
    brand             VARCHAR(80),
    unit_cost         NUMERIC(10,2)   NOT NULL CHECK (unit_cost >= 0),
    unit_price        NUMERIC(10,2)   NOT NULL CHECK (unit_price >= 0),
    weight_kg         NUMERIC(8,2),
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE,
    launch_date       DATE,
    supplier_country  CHAR(2),
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── dim_stores ────────────────────────────────────────────────
CREATE TABLE dim_stores (
    store_sk          SERIAL          PRIMARY KEY,
    store_id          UUID            NOT NULL UNIQUE,
    store_name        VARCHAR(200)    NOT NULL,
    store_type        VARCHAR(30)     CHECK (store_type IN ('Flagship','Express','Online','Outlet','Pop-Up')),
    city              VARCHAR(100),
    state             VARCHAR(10),
    country           CHAR(2),
    region            VARCHAR(20),
    sq_footage        INTEGER         CHECK (sq_footage > 0),
    open_date         DATE,
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE,
    manager_name      VARCHAR(120),
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── dim_time ──────────────────────────────────────────────────
CREATE TABLE dim_time (
    time_sk           SERIAL          PRIMARY KEY,
    full_date         DATE            NOT NULL,
    year              SMALLINT        NOT NULL,
    quarter           SMALLINT        NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month             SMALLINT        NOT NULL CHECK (month  BETWEEN 1 AND 12),
    month_name        VARCHAR(12)     NOT NULL,
    week              SMALLINT        NOT NULL CHECK (week   BETWEEN 1 AND 53),
    day_of_month      SMALLINT        NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week       SMALLINT        NOT NULL CHECK (day_of_week  BETWEEN 1 AND 7),
    day_name          VARCHAR(12)     NOT NULL,
    hour              SMALLINT        NOT NULL CHECK (hour BETWEEN 0 AND 23),
    is_weekend        BOOLEAN         NOT NULL DEFAULT FALSE,
    is_holiday        BOOLEAN         NOT NULL DEFAULT FALSE,
    fiscal_year       SMALLINT        NOT NULL,
    fiscal_quarter    SMALLINT        NOT NULL CHECK (fiscal_quarter BETWEEN 1 AND 4),
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- =============================================================
-- FACT TABLE
-- =============================================================

CREATE TABLE fact_sales (
    sale_sk           SERIAL          PRIMARY KEY,

    -- Foreign Keys (Star Schema relationships)
    customer_sk       INTEGER         NOT NULL
                      REFERENCES dim_customers(customer_sk) ON DELETE RESTRICT,
    product_sk        INTEGER         NOT NULL
                      REFERENCES dim_products(product_sk)  ON DELETE RESTRICT,
    store_sk          INTEGER         NOT NULL
                      REFERENCES dim_stores(store_sk)      ON DELETE RESTRICT,
    time_sk           INTEGER         NOT NULL
                      REFERENCES dim_time(time_sk)         ON DELETE RESTRICT,

    -- Degenerate dimension
    order_id          UUID            NOT NULL,

    -- Additive measures
    quantity          SMALLINT        NOT NULL CHECK (quantity > 0),
    unit_price        NUMERIC(10,2)   NOT NULL,
    unit_cost         NUMERIC(10,2)   NOT NULL,
    discount_pct      NUMERIC(5,2)    NOT NULL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 100),
    discount_amount   NUMERIC(10,2)   NOT NULL DEFAULT 0,
    gross_revenue     NUMERIC(12,2)   NOT NULL,
    net_revenue       NUMERIC(12,2)   NOT NULL,
    total_cost        NUMERIC(12,2)   NOT NULL,
    profit            NUMERIC(12,2)   NOT NULL,
    tax_amount        NUMERIC(10,2)   NOT NULL DEFAULT 0,
    shipping_cost     NUMERIC(8,2)    NOT NULL DEFAULT 0,
    return_amount     NUMERIC(10,2)   NOT NULL DEFAULT 0,

    -- Semi-additive / categorical measures
    payment_method    VARCHAR(30),
    sales_channel     VARCHAR(30),
    return_flag       BOOLEAN         NOT NULL DEFAULT FALSE,

    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- =============================================================
-- INDEXES  (accelerate the analytical queries)
-- =============================================================

-- Fact table FK indexes
CREATE INDEX idx_fact_customer ON fact_sales(customer_sk);
CREATE INDEX idx_fact_product  ON fact_sales(product_sk);
CREATE INDEX idx_fact_store    ON fact_sales(store_sk);
CREATE INDEX idx_fact_time     ON fact_sales(time_sk);

-- Analytical query accelerators
CREATE INDEX idx_fact_channel  ON fact_sales(sales_channel);
CREATE INDEX idx_fact_return   ON fact_sales(return_flag);
CREATE INDEX idx_time_year_month ON dim_time(year, month);
CREATE INDEX idx_product_category ON dim_products(category);
CREATE INDEX idx_customer_tier    ON dim_customers(loyalty_tier);

-- =============================================================
-- BULK LOAD  (COPY from CSV files mounted at /data/)
-- Disable FK checks during load for speed, re-enable after
-- =============================================================

-- Load dimensions first (no FK dependencies)
COPY dim_customers (customer_sk, customer_id, first_name, last_name, email,
                    phone, city, state, country, gender, age, loyalty_tier,
                    registration_date, is_active)
FROM '/data/dim_customers.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

COPY dim_products (product_sk, product_id, product_name, category, sub_category,
                   brand, unit_cost, unit_price, weight_kg, is_active,
                   launch_date, supplier_country)
FROM '/data/dim_products.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

COPY dim_stores (store_sk, store_id, store_name, store_type, city, state,
                 country, region, sq_footage, open_date, is_active, manager_name)
FROM '/data/dim_stores.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

COPY dim_time (time_sk, full_date, year, quarter, month, month_name, week,
               day_of_month, day_of_week, day_name, hour, is_weekend,
               is_holiday, fiscal_year, fiscal_quarter)
FROM '/data/dim_time.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

-- Sync SERIAL sequences after explicit PK inserts
SELECT setval('dim_customers_customer_sk_seq', (SELECT MAX(customer_sk) FROM dim_customers));
SELECT setval('dim_products_product_sk_seq',   (SELECT MAX(product_sk)  FROM dim_products));
SELECT setval('dim_stores_store_sk_seq',        (SELECT MAX(store_sk)   FROM dim_stores));
SELECT setval('dim_time_time_sk_seq',           (SELECT MAX(time_sk)    FROM dim_time));

-- Load fact table last (all FK targets must exist)
COPY fact_sales (sale_sk, customer_sk, product_sk, store_sk, time_sk,
                 order_id, quantity, unit_price, unit_cost, discount_pct,
                 discount_amount, gross_revenue, net_revenue, total_cost,
                 profit, tax_amount, shipping_cost, payment_method,
                 sales_channel, return_flag, return_amount)
FROM '/data/fact_sales.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

SELECT setval('fact_sales_sale_sk_seq', (SELECT MAX(sale_sk) FROM fact_sales));

-- =============================================================
-- QUICK VALIDATION
-- =============================================================
DO $$
DECLARE
    v_customers  BIGINT;
    v_products   BIGINT;
    v_stores     BIGINT;
    v_time       BIGINT;
    v_sales      BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_customers FROM dim_customers;
    SELECT COUNT(*) INTO v_products  FROM dim_products;
    SELECT COUNT(*) INTO v_stores    FROM dim_stores;
    SELECT COUNT(*) INTO v_time      FROM dim_time;
    SELECT COUNT(*) INTO v_sales     FROM fact_sales;

    RAISE NOTICE '=== Load Validation ===';
    RAISE NOTICE 'dim_customers : % rows', v_customers;
    RAISE NOTICE 'dim_products  : % rows', v_products;
    RAISE NOTICE 'dim_stores    : % rows', v_stores;
    RAISE NOTICE 'dim_time      : % rows', v_time;
    RAISE NOTICE 'fact_sales    : % rows', v_sales;
    RAISE NOTICE 'Total         : % rows', v_customers+v_products+v_stores+v_time+v_sales;
END $$;
