FROM python:3.12-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install  -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE $PORT

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
