FROM python:3.12-slim

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock /app/
COPY packages/shared /app/packages/shared
COPY packages/api /app/packages/api
RUN uv sync --frozen --no-dev

ENV PORT=8000
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "liveintent_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
