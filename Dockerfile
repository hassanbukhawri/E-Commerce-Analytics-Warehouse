# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (leverages layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application file
COPY app.py /app/app.py

# Streamlit native configuration & dark theme styling
RUN mkdir -p /app/.streamlit
RUN cat > /app/.streamlit/config.toml << 'EOF'
[server]
headless             = true
port                 = 8501
enableCORS           = false
enableXsrfProtection = false

[theme]
base                     = "dark"
primaryColor             = "#6366f1"
backgroundColor          = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor                = "#e2e8f0"
EOF

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]