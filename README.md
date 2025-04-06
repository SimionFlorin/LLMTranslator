# Broker Translation Application

A multilingual translation application using LLM (Large Language Model) to translate web content into multiple languages.

## Setup


Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```


### Option 1: Local Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```

### Option 2: Docker Setup

1. Build the Docker image:
```bash
docker build -t brokertranslator .
```

2. Run the container:
```bash
docker run -p 8501:8501 brokertranslator
```

The application will be available at `http://localhost:8501`

## Features

- Modern, responsive Streamlit interface
- Translate text to multiple languages (Spanish, French, German, Japanese, Arabic, Hindi, Portuguese, Hungarian)
- Preserve placeholders in translations
- Interactive translation quality evaluation
- Visual comparison with Google Translate baseline
- Real-time translation and evaluation metrics

## Project Structure

- `streamlit_app.py`: Main Streamlit application
- `translator.py`: Translation logic using LLM
- `evaluator.py`: Translation quality evaluation
- `requirements.txt`: Project dependencies
- `translated_output.csv`: Evaluation dataset
- `Dockerfile`: Container configuration

## Evaluation Metrics

The application provides two main metrics for translation quality:
1. Reference Overlap: Measures similarity with reference translations
2. Word Preservation: Tracks maintenance of key terms and placeholders 