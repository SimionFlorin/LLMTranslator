# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY requirements.txt .
COPY *.py .
COPY translated_output.csv .
COPY .env .


# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
# CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"] 
CMD ["streamlit", "run", "streamlit_app.py" ] 