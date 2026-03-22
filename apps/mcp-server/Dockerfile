FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY pytest.ini ./
COPY src ./src
COPY tests ./tests

RUN uv pip install --system . pytest pytest-asyncio

EXPOSE 8000

CMD ["python", "-m", "pokemon_mcp.server"]