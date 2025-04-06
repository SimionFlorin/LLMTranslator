# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set NLTK data path
ENV NLTK_DATA=/usr/local/share/nltk_data

# Create NLTK data directory
RUN mkdir -p /usr/local/share/nltk_data

# Copy application files
COPY requirements.txt .
COPY *.py .
COPY translated_output.csv .
COPY .env .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download required NLTK data
RUN python -c "import nltk; nltk.download('wordnet', download_dir='/usr/local/share/nltk_data'); nltk.download('punkt', download_dir='/usr/local/share/nltk_data')"

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
# CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"] 
CMD ["streamlit", "run", "streamlit_app.py" ] 