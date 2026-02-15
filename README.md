# CostGuard AI

CostGuard AI is an autonomous cloud resource and AI model cost optimization platform. It utilizes Model Context Protocol (MCP) based agents to continuously monitor cloud spending and LLM usage, identify optimization opportunities, and facilitate autonomous resource allocation adjustments.

## Project Overview

The platform deploys intelligent agents that interface with cloud provider billing APIs and LLM usage logs. These agents analyze cost data against historical baselines to detect anomalies. When an optimization opportunity or cost spike is identified, the system orchestrates a response through Archestra.AI, allowing for automated remediation with optional human-in-the-loop approval workflows.

NOTE: Project was made with the help of Antigravity AI tools.

## Key Features

- **Automated Anomaly Detection**: Implementation of rolling-average baseline analysis to detect significant cost deviations in real-time.
- **LLM Usage Analytics**: Granular tracking of token usage, model latency, and quality scores across multiple providers (OpenAI, Anthropic).
- **Intelligent Resource Optimization**: Automated recommendation and execution of cost-saving measures, such as switching to cost-efficient models or scaling down underutilized cloud resources.
- **Integrated Communication Bridge**: An A2A (Agent-to-Agent) communication layer that facilitates seamless interaction between the CostGuard backend and Archestra.AI orchestration agents.
- **Unified Dashboard**: A comprehensive Streamlit-based interface providing real-time visualization of cost trends, provider breakdowns, and active optimization states.

## Architecture

CostGuard AI follows a modular architecture designed for scalability and reliability.

### System Flow
1. **Data Ingestion**: Cloud and LLM usage data are collected via backend repositories.
2. **Analysis**: The Detective Agent compares current metrics against historical 7-day averages.
3. **Orchestration**: Identified anomalies trigger optimization workflows via the Archestra.AI A2A bridge.
4. **Execution**: The Executor Agent implements approved changes, providing instantaneous feedback via the integrated dashboard chat.

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **Frontend**: Streamlit
- **Protocols**: Model Context Protocol (MCP), JSON-RPC 2.0
- **Database**: PostgreSQL
- **Orchestration**: Archestra.AI
- **Infrastructure**: Docker, Docker Compose

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.10 or higher
- Access keys for OpenAI, Anthropic, or Archestra.AI (depending on configuration)

### Local Setup
1. Clone the repository and navigate to the project root.
2. Initialize the environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Populate the required API keys in the `.env` file.
4. Launch the platform using Docker Compose:
   ```bash
   docker-compose up --build
   ```
5. Access the Dashboard at `http://localhost:8501`.
6. Access the API Documentation at `http://localhost:8000/docs`.

## Deployment

The platform is designed for containerized deployment. For production environments, it is recommended to utilize orchestration services like Railway or AWS ECS. Detailed deployment instructions can be found in the `deployment_guide.md` file.

## API Documentation

The backend service provides an interactive OpenAPI (Swagger) documentation available at the `/docs` endpoint. This documentation includes detailed schema definitions and request/response examples for all cost monitoring and agent control endpoints.




