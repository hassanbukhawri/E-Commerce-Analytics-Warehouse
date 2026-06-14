-- =============================================================
-- procedures.sql
-- 3 Analytical Stored Functions for E-Commerce Data Warehouse
-- PostgreSQL 15+
-- =============================================================

-- =============================================================
-- FUNCTION 1: get_top_selling_products
-- Returns the top N products by net revenue and quantity sold,
-- enriched with profit margin and category for charting
-- =============================================================
CREATE OR REPLACE FUNCTION get_top_selling_products(p_limit INT DEFAULT 10)
RETURNS TABLE (
    product_sk       INT,
    product_name     TEXT,
    category         TEXT,
    brand            TEXT,
    total_quantity   BIGINT,
    total_revenue    NUMERIC,
    total_cost       NUMERIC,
    total_profit     NUMERIC,
    profit_margin    NUMERIC,
    avg_unit_price   NUMERIC,
    total_orders     BIGINT,
    avg_discount_pct NUMERIC
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        p.product_sk,
        p.product_name::TEXT,
        p.category::TEXT,
        p.brand::TEXT,
        SUM(f.quantity)::BIGINT                                 AS total_quantity,
        ROUND(SUM(f.net_revenue), 2)                           AS total_revenue,
        ROUND(SUM(f.total_cost), 2)                            AS total_cost,
        ROUND(SUM(f.profit), 2)                                AS total_profit,
        ROUND(
            CASE WHEN SUM(f.net_revenue) = 0 THEN 0
                 ELSE SUM(f.profit) / SUM(f.net_revenue) * 100
            END, 2)                                            AS profit_margin,
        ROUND(AVG(f.unit_price), 2)                            AS avg_unit_price,
        COUNT(DISTINCT f.order_id)::BIGINT                     AS total_orders,
        ROUND(AVG(f.discount_pct), 2)                          AS avg_discount_pct
    FROM fact_sales   f
    JOIN dim_products p ON p.product_sk = f.product_sk
    WHERE f.return_flag = FALSE
    GROUP BY p.product_sk, p.product_name, p.category, p.brand
    ORDER BY total_revenue DESC
    LIMIT p_limit;
$$;

COMMENT ON FUNCTION get_top_selling_products(INT) IS
    'Returns top N products by net revenue with profit, margin, and discount data.';


-- =============================================================
-- FUNCTION 2: get_monthly_revenue_trends
-- Aggregates revenue, profit, orders and returns by year+month
-- Optional year filter; NULL = all years
-- =============================================================
CREATE OR REPLACE FUNCTION get_monthly_revenue_trends(p_year INT DEFAULT NULL)
RETURNS TABLE (
    year             INT,
    month            INT,
    month_name       TEXT,
    total_revenue    NUMERIC,
    total_profit     NUMERIC,
    total_cost       NUMERIC,
    total_orders     BIGINT,
    total_quantity   BIGINT,
    avg_order_value  NUMERIC,
    total_returns    BIGINT,
    return_rate      NUMERIC,
    mom_revenue_chg  NUMERIC   -- month-over-month % change
)
LANGUAGE SQL
STABLE
AS $$
    WITH monthly AS (
        SELECT
            t.year::INT,
            t.month::INT,
            t.month_name::TEXT,
            ROUND(SUM(f.net_revenue), 2)             AS total_revenue,
            ROUND(SUM(f.profit), 2)                  AS total_profit,
            ROUND(SUM(f.total_cost), 2)              AS total_cost,
            COUNT(DISTINCT f.order_id)::BIGINT       AS total_orders,
            SUM(f.quantity)::BIGINT                  AS total_quantity,
            ROUND(AVG(f.net_revenue), 2)             AS avg_order_value,
            SUM(CASE WHEN f.return_flag THEN 1 ELSE 0 END)::BIGINT AS total_returns
        FROM fact_sales f
        JOIN dim_time   t ON t.time_sk = f.time_sk
        WHERE (p_year IS NULL OR t.year = p_year)
        GROUP BY t.year, t.month, t.month_name
    )
    SELECT
        m.year,
        m.month,
        m.month_name,
        m.total_revenue,
        m.total_profit,
        m.total_cost,
        m.total_orders,
        m.total_quantity,
        m.avg_order_value,
        m.total_returns,
        ROUND(
            CASE WHEN m.total_orders = 0 THEN 0
                 ELSE m.total_returns::NUMERIC / m.total_orders * 100
            END, 2)                                   AS return_rate,
        ROUND(
            CASE
                WHEN LAG(m.total_revenue) OVER (ORDER BY m.year, m.month) IS NULL
                  OR LAG(m.total_revenue) OVER (ORDER BY m.year, m.month) = 0
                THEN NULL
                ELSE (m.total_revenue
                      - LAG(m.total_revenue) OVER (ORDER BY m.year, m.month))
                     / LAG(m.total_revenue) OVER (ORDER BY m.year, m.month) * 100
            END, 2)                                   AS mom_revenue_chg
    FROM monthly m
    ORDER BY m.year, m.month;
$$;

COMMENT ON FUNCTION get_monthly_revenue_trends(INT) IS
    'Monthly revenue, profit, orders and return trends. Pass a year to filter, NULL for all.';


-- =============================================================
-- FUNCTION 3: get_top_customers
-- Returns top N customers by total spending, with loyalty tier,
-- order count, AOV, and favourite category
-- =============================================================
CREATE OR REPLACE FUNCTION get_top_customers(p_limit INT DEFAULT 10)
RETURNS TABLE (
    customer_sk        INT,
    full_name          TEXT,
    email              TEXT,
    loyalty_tier       TEXT,
    country            TEXT,
    age                INT,
    total_revenue      NUMERIC,
    total_profit       NUMERIC,
    total_orders       BIGINT,
    total_quantity     BIGINT,
    avg_order_value    NUMERIC,
    total_returns      BIGINT,
    favourite_category TEXT,
    favourite_channel  TEXT
)
LANGUAGE SQL
STABLE
AS $$
    WITH customer_stats AS (
        SELECT
            c.customer_sk,
            (c.first_name || ' ' || c.last_name)::TEXT          AS full_name,
            c.email::TEXT,
            c.loyalty_tier::TEXT,
            c.country::TEXT,
            c.age::INT,
            ROUND(SUM(f.net_revenue), 2)                         AS total_revenue,
            ROUND(SUM(f.profit), 2)                              AS total_profit,
            COUNT(DISTINCT f.order_id)::BIGINT                   AS total_orders,
            SUM(f.quantity)::BIGINT                              AS total_quantity,
            ROUND(AVG(f.net_revenue), 2)                         AS avg_order_value,
            SUM(CASE WHEN f.return_flag THEN 1 ELSE 0 END)::BIGINT AS total_returns
        FROM fact_sales   f
        JOIN dim_customers c ON c.customer_sk = f.customer_sk
        GROUP BY c.customer_sk, c.first_name, c.last_name,
                 c.email, c.loyalty_tier, c.country, c.age
    ),
    fav_category AS (
        SELECT DISTINCT ON (f.customer_sk)
            f.customer_sk,
            p.category::TEXT AS favourite_category
        FROM fact_sales   f
        JOIN dim_products p ON p.product_sk = f.product_sk
        GROUP BY f.customer_sk, p.category
        ORDER BY f.customer_sk, SUM(f.net_revenue) DESC
    ),
    fav_channel AS (
        SELECT DISTINCT ON (customer_sk)
            customer_sk,
            sales_channel::TEXT AS favourite_channel
        FROM fact_sales
        GROUP BY customer_sk, sales_channel
        ORDER BY customer_sk, COUNT(*) DESC
    )
    SELECT
        cs.customer_sk,
        cs.full_name,
        cs.email,
        cs.loyalty_tier,
        cs.country,
        cs.age,
        cs.total_revenue,
        cs.total_profit,
        cs.total_orders,
        cs.total_quantity,
        cs.avg_order_value,
        cs.total_returns,
        fc.favourite_category,
        fch.favourite_channel
    FROM customer_stats cs
    LEFT JOIN fav_category fc  ON fc.customer_sk  = cs.customer_sk
    LEFT JOIN fav_channel  fch ON fch.customer_sk = cs.customer_sk
    ORDER BY cs.total_revenue DESC
    LIMIT p_limit;
$$;

COMMENT ON FUNCTION get_top_customers(INT) IS
    'Returns top N customers by spend with loyalty tier, AOV, and behavioural signals.';


-- =============================================================
-- BONUS VIEWS  (lightweight, no parameters needed)
-- =============================================================

-- Category performance summary
CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    p.category,
    COUNT(DISTINCT f.product_sk)             AS unique_products,
    SUM(f.quantity)                          AS total_quantity,
    ROUND(SUM(f.net_revenue), 2)             AS total_revenue,
    ROUND(SUM(f.profit), 2)                  AS total_profit,
    ROUND(AVG(f.discount_pct), 2)            AS avg_discount_pct,
    ROUND(
        CASE WHEN SUM(f.net_revenue) = 0 THEN 0
             ELSE SUM(f.profit) / SUM(f.net_revenue) * 100
        END, 2)                              AS profit_margin_pct
FROM fact_sales   f
JOIN dim_products p ON p.product_sk = f.product_sk
WHERE f.return_flag = FALSE
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Sales channel breakdown
CREATE OR REPLACE VIEW vw_channel_performance AS
SELECT
    sales_channel,
    COUNT(DISTINCT order_id)                 AS total_orders,
    SUM(quantity)                            AS total_units,
    ROUND(SUM(net_revenue), 2)               AS total_revenue,
    ROUND(AVG(net_revenue), 2)               AS avg_order_value,
    ROUND(AVG(discount_pct), 2)              AS avg_discount_pct,
    SUM(CASE WHEN return_flag THEN 1 ELSE 0 END) AS total_returns
FROM fact_sales
GROUP BY sales_channel
ORDER BY total_revenue DESC;

-- Store region performance
CREATE OR REPLACE VIEW vw_region_performance AS
SELECT
    s.region,
    s.country,
    COUNT(DISTINCT f.store_sk)               AS store_count,
    ROUND(SUM(f.net_revenue), 2)             AS total_revenue,
    ROUND(SUM(f.profit), 2)                  AS total_profit,
    COUNT(DISTINCT f.order_id)               AS total_orders,
    ROUND(AVG(f.net_revenue), 2)             AS avg_order_value
FROM fact_sales f
JOIN dim_stores s ON s.store_sk = f.store_sk
GROUP BY s.region, s.country
ORDER BY total_revenue DESC;

-- Quick sanity check
SELECT 'Functions and views created successfully' AS status;
