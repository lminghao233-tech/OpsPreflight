FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY pyproject.toml README.md ./
COPY opspreflight ./opspreflight
RUN pip install --no-cache-dir .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "opspreflight.api:app", "--host", "0.0.0.0", "--port", "8000"]

