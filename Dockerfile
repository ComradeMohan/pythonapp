FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    chromium \
    chromium-driver \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libgdk-pixbuf2.0-0 \
    libasound2 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for headless Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV DISPLAY=:99

# Set up the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code
COPY . .

# Expose the Flask app port
EXPOSE 5000

# Run the Flask app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
