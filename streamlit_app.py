import streamlit as st
from translator import TranslationService
from evaluator import TranslationEvaluator
import pandas as pd
import altair as alt

# Initialize services
translator = TranslationService()
evaluator = TranslationEvaluator()

# Set page config
st.set_page_config(
    page_title="BrokerChooser Translation",
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
st.title("🌐 BrokerChooser Translation Service")
st.markdown("""
    Translate your content into multiple languages using advanced AI technology.
    Compare results between our LLM-based translation and Google Translate.
""")

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["Translator", "Evaluation"])

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

else:  # Evaluation page
    st.header("Translation Evaluation")
    
    # Dataset evaluation
    st.subheader("Dataset Evaluation Results")
    
    try:
        with st.spinner("Evaluating translations..."):
            metrics = evaluator.evaluate_dataset('translated_output.csv')
            
            # Prepare data for Altair chart
            chart_data = pd.DataFrame({
                'Metric': ['Reference Overlap', 'Word Preservation'] * 2,
                'Score': [
                    metrics['llm_overlap'], metrics['llm_preserved'],
                    metrics['google_overlap'], metrics['google_preserved']
                ],
                'Model': ['LLM', 'LLM', 'Google Translate', 'Google Translate']
            })
            
            # Create Altair chart
            chart = alt.Chart(chart_data).mark_bar().encode(
                x='Metric:N',
                y='Score:Q',
                color='Model:N',
                column='Model:N'
            ).properties(
                title='Translation Quality Metrics'
            )
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("LLM Metrics")
                st.metric("Reference Overlap", f"{metrics['llm_overlap']:.2%}")
                st.metric("Word Preservation", f"{metrics['llm_preserved']:.2%}")
            
            with col2:
                st.subheader("Google Translate Metrics")
                st.metric("Reference Overlap", f"{metrics['google_overlap']:.2%}")
                st.metric("Word Preservation", f"{metrics['google_preserved']:.2%}")
            
            # Display the chart
            st.altair_chart(chart, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error evaluating dataset: {str(e)}")
    
    # Methodology explanation
    st.subheader("Evaluation Methodology")
    st.markdown("""
        Our evaluation methodology consists of two main metrics:
        1. **Reference Overlap**: Measures how well the translation matches the reference translation
        2. **Word Preservation**: Measures how well important terms and placeholders are preserved
        
        The evaluation is performed on a Hungarian dataset to assess translation quality and consistency.
    """) 