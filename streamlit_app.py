import streamlit as st
from translator import TranslationService
from evaluator import TranslationEvaluator
import pandas as pd
import altair as alt
import io
import csv
from typing import Dict
import nltk

# Initialize services
translator = TranslationService()
evaluator = TranslationEvaluator()

# Set page config
st.set_page_config(
    page_title="Broker Translation",
    page_icon="🌐",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stSelectbox > div > div > select {
        font-size: 16px;
    }
    .stTextArea > div > div > textarea {
        font-size: 16px;
    }
    .main {
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🌐 Broker Translation Service")
st.markdown("""
    Translate your content into multiple languages using advanced AI technology.
    Compare results between our LLM-based translation and Google Translate.
""")

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["Translator", "Batch Processing", "Evaluation"])

if page == "Translator":
    # Main translation interface
    st.header("Translation Interface")
    
    # Input text
    input_text = st.text_area("Enter text to translate", height=150,
                             placeholder="Enter your English text here...")
    
    # Language selection
    languages = list(translator.get_supported_languages().keys())
    target_lang = st.selectbox("Select target language", languages)
    
    if st.button("Translate", type="primary"):
        if input_text:
            with st.spinner("Translating..."):
                # Get translations
                llm_result = translator.translate_with_llm(input_text, target_lang)
                google_result = translator.translate_with_google(input_text, target_lang)
                
                # Display results in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🤖 LLM Translation")
                    st.info(llm_result if llm_result else "Translation failed")
                
                with col2:
                    st.subheader("🔄 Google Translation")
                    st.info(google_result if google_result else "Translation failed")
        else:
            st.warning("Please enter some text to translate")

elif page == "Batch Processing":
    st.header("Batch Translation")
    st.markdown("""
        Upload a CSV file with English text to translate in bulk. The CSV should have one column named 'english'.
        The translated text will be saved in a new CSV file with two columns: 'english' and 'translated_value'.
        
        **Note**: Please ensure your CSV file is saved with UTF-8 encoding.
    """)
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    # Language selection for batch processing
    languages = list(translator.get_supported_languages().keys())
    target_lang = st.selectbox("Select target language", languages)
    
    # Translation method selection
    translation_method = st.radio(
        "Select translation method",
        ["LLM (GPT-4)", "Google Translate"],
        horizontal=True
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file with UTF-8 encoding
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            # Validate the CSV structure
            if 'english' not in df.columns:
                st.error("The CSV file must contain a column named 'english'")
            else:
                st.write("Preview of the input data:")
                st.dataframe(df.head())
                
                if st.button("Start Batch Translation", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    error_log = []
                    
                    # Create a new column for translations
                    df['translated_value'] = None
                    total_rows = len(df)
                    
                    # Perform translations
                    for idx, row in df.iterrows():
                        try:
                            status_text.text(f"Translating row {idx + 1} of {total_rows}...")
                            
                            # Ensure the input text is properly encoded
                            input_text = str(row['english']).strip()
                            
                            if translation_method == "LLM (GPT-4)":
                                translation = translator.translate_with_llm(input_text, target_lang)
                            else:
                                translation = translator.translate_with_google(input_text, target_lang)
                            
                            if translation:
                                df.at[idx, 'translated_value'] = translation
                            else:
                                error_log.append(f"Row {idx + 1}: Translation failed")
                                df.at[idx, 'translated_value'] = "TRANSLATION_FAILED"
                            
                            progress_bar.progress((idx + 1) / total_rows)
                        except Exception as e:
                            error_msg = f"Row {idx + 1}: {str(e)}"
                            error_log.append(error_msg)
                            df.at[idx, 'translated_value'] = "ERROR"
                            continue
                    
                    # Create download link for the translated CSV
                    output = io.StringIO()
                    df.to_csv(output, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
                    output.seek(0)
                    
                    st.success("Translation completed!")
                    
                    # Display any errors that occurred
                    if error_log:
                        st.warning("Some translations had issues:")
                        for error in error_log:
                            st.write(f"- {error}")
                    
                    st.download_button(
                        label="Download Translated CSV",
                        data=output.getvalue().encode('utf-8-sig'),
                        file_name=f"translated_{target_lang.lower()}.csv",
                        mime="text/csv"
                    )
                    
                    st.write("Preview of the translated data:")
                    st.dataframe(df.head())
                    
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            st.info("Please ensure your CSV file is saved with UTF-8 encoding.")

else:  # Evaluation page
    st.header("Translation Evaluation")
    
    # Dataset evaluation
    st.subheader("Dataset Evaluation Results")
    
    # Add evaluate button
    if st.button("Start Evaluation", type="primary"):
        try:
            # Create placeholders for progress and metrics
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_container = st.empty()
            
            def update_progress(current: int, total: int, current_metrics: Dict):
                # Update progress bar
                progress = float(current) / float(total)
                progress_bar.progress(progress)
                
                # Update status text
                status_text.text(f"Processed {current}/{total} translations")
                
                # Update current metrics
                with metrics_container.container():
                    st.markdown("### Current Metrics (Running Average)")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("LLM METEOR Score", f"{current_metrics['llm_meteor']:.3f}")
                        st.metric("LLM BLEU Score", f"{current_metrics['llm_bleu']:.3f}")
                    
                    with col2:
                        st.metric("Google METEOR Score", f"{current_metrics['google_meteor']:.3f}")
                        st.metric("Google BLEU Score", f"{current_metrics['google_bleu']:.3f}")
            
            # Run evaluation with progress callback
            with st.spinner("Evaluating translations..."):
                metrics = evaluator.evaluate_dataset('translated_output.csv', progress_callback=update_progress)
            
            # Clear the progress indicators
            progress_bar.empty()
            status_text.empty()
            metrics_container.empty()
            
            # Display final metrics
            st.markdown("### Final METEOR Scores")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "LLM METEOR Score", 
                    f"{metrics['llm_meteor']:.3f}",
                    f"±{metrics['llm_meteor_std']:.3f}"
                )
            
            with col2:
                st.metric(
                    "Google METEOR Score", 
                    f"{metrics['google_meteor']:.3f}",
                    f"±{metrics['google_meteor_std']:.3f}"
                )
            
            st.markdown("### Final BLEU Scores")
            col3, col4 = st.columns(2)
            
            with col3:
                st.metric(
                    "LLM BLEU Score", 
                    f"{metrics['llm_bleu']:.3f}",
                    f"±{metrics['llm_bleu_std']:.3f}"
                )
            
            with col4:
                st.metric(
                    "Google BLEU Score", 
                    f"{metrics['google_bleu']:.3f}",
                    f"±{metrics['google_bleu_std']:.3f}"
                )
                
        except Exception as e:
            st.error(f"Error evaluating dataset: {str(e)}")
    
    # Add information about the evaluation process
    st.info("""
        Click 'Start Evaluation' to:
        1. Load the reference translations
        2. Generate new translations using both LLM and Google Translate
        3. Calculate METEOR and BLEU scores
        4. Display comparative results
        
        Note: This process may take several minutes depending on the dataset size.
        You can monitor the progress in real-time as translations are processed.
    """)
    
    # Methodology explanation
    st.subheader("Evaluation Methodology")
    st.markdown("""
        Our evaluation system uses two complementary industry-standard metrics to provide a comprehensive assessment of translation quality:
        
        ### 1. METEOR Score (Metric for Evaluation of Translation with Explicit ORdering)
        - **What it measures**: Evaluates translations by considering exact matches, stems, synonyms, and paraphrases
        - **Score range**: 0 to 1 (higher is better)
        - **Key features**:
            - Handles word order and synonyms
            - More flexible than BLEU for legitimate translation variations
            - Better correlation with human judgments
            - Particularly good at recognizing valid paraphrases
        
        ### 2. BLEU Score (BiLingual Evaluation Understudy)
        - **What it measures**: Compares n-gram overlaps between the candidate translation and reference translation
        - **Score range**: 0 to 1 (higher is better)
        - **Key features**:
            - Industry standard metric
            - Measures exact phrase matches
            - Penalizes both too-short and too-long translations
            - Good at capturing translation fluency
        
        ### Evaluation Process
        1. **Data Preparation**:
           - Load reference translations from the dataset
           - Column 'english' contains source text
           - Column 'label' contains human reference translations
        
        2. **Translation Generation**:
           - Generate translations using both LLM (GPT-4) and Google Translate
           - Process each text while preserving special placeholders
        
        3. **Metric Calculation**:
           - Calculate both METEOR and BLEU scores for each translation
           - Compare against human reference translations
           - Track running averages and standard deviations
        
        4. **Statistical Analysis**:
           - Calculate mean scores across all translations
           - Compute standard deviations to measure consistency
           - Present results with error bars showing variation
        
        ### Interpreting Results
        - **Higher scores** indicate better translation quality
        - **Standard deviations** (±) show consistency across different texts
        - **Comparing metrics**:
            - METEOR: Better for evaluating meaning preservation
            - BLEU: Better for evaluating phrase accuracy
        
        ### Limitations
        - Metrics are approximations of human judgment
        - Perfect scores are rare due to translation complexity
        - Multiple valid translations may exist for the same text
        - Scores should be considered alongside human evaluation
    """)
   