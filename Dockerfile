FROM python:3.11-slim

# Install dependencies for Chromium and Google Chrome
RUN apt-get update && \
    apt-get install -y \
    chromium \
    google-chrome-stable \
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
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROME_PATH=/usr/bin/google-chrome-stable
ENV DISPLAY=:99  # Ensure this works with Render (you may not need it if headless mode works by default)

# Verify if Google Chrome is installed correctly
RUN google-chrome-stable --version  # Verifying Google Chrome installation
RUN chromium --version  # Verifying Chromium installation

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
