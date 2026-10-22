FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py database.py ./
COPY templates ./templates
COPY db ./db

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
