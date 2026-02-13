FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Install project dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel hatchling && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir "uvicorn[standard]"

# Install server specific dependencies if they exist
# Assuming mcp-servers/llm-tracker-server might have requirements, but likely handled by root for now
# We can add a check just in case
RUN if [ -f mcp_servers/llm-tracker-server/requirements.txt ]; then pip install --no-cache-dir -r mcp_servers/llm-tracker-server/requirements.txt; fi

EXPOSE 8001

# Adjust the python path to include the root so imports work
ENV PYTHONPATH=/app

CMD ["uvicorn", "mcp_servers.llm_tracker_server.main:app", "--host", "0.0.0.0", "--port", "8001"]
