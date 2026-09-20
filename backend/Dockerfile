FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY data ./data
RUN useradd --create-home afdd
USER afdd
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
