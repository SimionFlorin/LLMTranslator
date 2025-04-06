# Broker Translation Application

A multilingual translation application using LLM (Large Language Model) to translate web content into multiple languages.

## Prerequisites

- Python 3.10 (required for compatibility)
- Docker (recommended for easy setup)

## Setup

Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

### Option 1: Docker Setup (Recommended)

1. Build the Docker image:
```bash
docker build -t brokertranslator .
```

2. Run the container:
```bash
docker run -p 8501:8501 brokertranslator
```

The application will be available at `http://localhost:8501`

### Option 2: Local Setup

1. Create and activate a virtual environment:

   **For Linux/Mac:**
   ```bash
   # Create virtual environment
   python3.10 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate
   ```

   **For Windows:**
   ```bash
   # Create virtual environment
   python3.10 -m venv venv
   
   # Activate virtual environment
   venv\Scripts\activate
   ```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```

### Last Resort: Development Requirements

If both Docker and local setup fail, you can try using the development requirements which have more lenient version constraints:

1. Follow the local setup steps 1 and 3 above
2. Instead of installing requirements.txt, use:
```bash
pip install -r requirements_dev.txt
```

**Note:** The development requirements should only be used as a last resort if both Docker and standard local setup fail. They contain more lenient version constraints which might lead to compatibility issues.

## Features

- Modern, responsive Streamlit interface with three main sections:
  - Single text translation
  - Batch processing for multiple translations
  - Translation quality evaluation
- Powered by GPT-4 for high-quality translations
- Support for multiple languages (Spanish, French, German, Japanese, Arabic, Hindi, Portuguese, Hungarian)
- Smart placeholder preservation in translations
- Comprehensive translation quality evaluation using METEOR and BLEU scores
- Real-time progress tracking during batch processing
- Comparison with Google Translate as a baseline
- Detailed statistical analysis with standard deviations

## Project Structure

- `streamlit_app.py`: Main application interface with three pages:
  - Translation interface for single texts
  - Batch processing for multiple translations
  - Evaluation page with quality metrics
- `translator.py`: Core translation logic using GPT-4 and Google Translate
  - Handles placeholder preservation
  - Manages API interactions
  - Provides language support
- `evaluator.py`: Quality evaluation system
  - Implements METEOR and BLEU scoring
  - Handles batch processing
  - Provides statistical analysis
- `requirements.txt`: Project dependencies including:
  - OpenAI API client
  - Streamlit for the web interface
  - NLTK for evaluation metrics
  - Other essential libraries
- `requirements_dev.txt`: Last resort dependencies with more lenient version constraints (use only if other methods fail)
- `translated_output.csv`: Sample dataset for evaluation
- `Dockerfile`: Container configuration for easy deployment

## Evaluation Metrics

The application uses two industry-standard metrics for translation quality evaluation:

1. **METEOR Score (Metric for Evaluation of Translation with Explicit ORdering)**
   - Evaluates translations by considering exact matches, stems, synonyms, and paraphrases
   - Score range: 0 to 1 (higher is better)
   - Particularly good at recognizing valid paraphrases and handling word order variations
   - Better correlation with human judgments compared to other metrics

2. **BLEU Score (BiLingual Evaluation Understudy)**
   - Measures n-gram overlap between the candidate translation and reference translation
   - Score range: 0 to 1 (higher is better)
   - Industry standard metric for machine translation evaluation
   - Good at capturing translation fluency and phrase accuracy

The evaluation process:
- Compares translations against human reference translations
- Calculates both METEOR and BLEU scores for each translation
- Provides running averages and standard deviations during batch processing
- Allows comparison between LLM and Google Translate results 