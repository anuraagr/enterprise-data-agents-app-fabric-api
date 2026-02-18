FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# Create .streamlit config for production
RUN mkdir -p .streamlit && \
    echo '[server]' > .streamlit/config.toml && \
    echo 'headless = true' >> .streamlit/config.toml && \
    echo 'enableCORS = false' >> .streamlit/config.toml && \
    echo 'enableXsrfProtection = false' >> .streamlit/config.toml && \
    echo '' >> .streamlit/config.toml && \
    echo '[browser]' >> .streamlit/config.toml && \
    echo 'gatherUsageStats = false' >> .streamlit/config.toml && \
    echo '' >> .streamlit/config.toml && \
    echo '[theme]' >> .streamlit/config.toml && \
    echo 'primaryColor = "#667eea"' >> .streamlit/config.toml && \
    echo 'backgroundColor = "#ffffff"' >> .streamlit/config.toml && \
    echo 'secondaryBackgroundColor = "#f8f9fa"' >> .streamlit/config.toml && \
    echo 'textColor = "#1a1a2e"' >> .streamlit/config.toml

EXPOSE 8501

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
