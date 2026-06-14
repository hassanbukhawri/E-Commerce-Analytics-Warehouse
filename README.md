# my-analytics-warehouse

A full-stack, containerized analytical data warehouse pipeline designed to orchestrate, model, and visualize e-commerce retail operations. The entire ecosystem is deployed using Docker Compose to ensure clean service synchronization, isolated networking, and persistent storage volumes.

The underlying database utilizes a PostgreSQL engine structured as a high-performance Dimensional Star Schema optimized for complex analytical querying and multi-dimensional reporting.

## 1. Relational Architecture Model

The analytical database separates operational measurements from descriptive business context to optimize query efficiency:

* **Central Fact Hub:** `fact_sales` tracks transactional events and performance metrics including item quantity, unit prices, unit costs, gross revenue, net revenue, and profit.
* **Dimensional Contexts:** `dim_customers`, `dim_products`, `dim_stores`, and `dim_time` maintain historical attributes linked directly to the central hub via surrogate keys (`_sk`).

## 2. Tech Stack and Infrastructure Components

* **Database Engine:** PostgreSQL 15 (Alpine Linux Container)
* **Infrastructure Orchestration:** Docker and Docker Compose
* **Analytics Layer:** Streamlit (Python Core App Engine)
* **Administration Client:** pgAdmin 4 (Server Mode Web Environment)

## 3. Installation and Deployment

Follow these sequential steps to initialize the environment and launch the cluster stack:

### Step 3.1: Ingest and Seed Mock Retail Data
Execute the Python data generation script locally to seed the relational files required for pipeline ingestion:
```bash
python generate_data.py
