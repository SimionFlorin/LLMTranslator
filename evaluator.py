import pandas as pd
from typing import Dict, List, Tuple
from sklearn.metrics import accuracy_score
import numpy as np
from translator import TranslationService

class TranslationEvaluator:
    def __init__(self):
        self.translator = TranslationService()

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """Load the evaluation dataset."""
        return pd.read_csv(file_path)

    def evaluate_translation(self, original_text: str, translated_text: str, 
                           reference_text: str) -> Dict[str, float]:
        """Evaluate the quality of a translation using various metrics."""
        # Simple word overlap score
        original_words = set(original_text.lower().split())
        translated_words = set(translated_text.lower().split())
        reference_words = set(reference_text.lower().split())
        
        # Calculate word overlap with reference
        overlap_with_reference = len(translated_words.intersection(reference_words)) / len(reference_words)
        
        # Calculate word preservation from original
        preserved_words = len(translated_words.intersection(original_words)) / len(original_words)
        
        return {
            'overlap_with_reference': overlap_with_reference,
            'preserved_words': preserved_words
        }

    def compare_with_baseline(self, text: str, target_language: str) -> Dict[str, str]:
        """Compare LLM translation with Google Translate baseline."""
        llm_translation = self.translator.translate_with_llm(text, target_language)
        google_translation = self.translator.translate_with_google(text, target_language)
        
        return {
            'llm_translation': llm_translation,
            'google_translation': google_translation
        }

    def evaluate_dataset(self, dataset_path: str) -> Dict[str, float]:
        """Evaluate the entire dataset and return average metrics."""
        df = self.load_dataset(dataset_path)
        metrics = []
        
        for _, row in df.iterrows():
            original_text = row['original_text']
            reference_text = row['reference_text']
            
            # Get translations
            llm_translation = self.translator.translate_with_llm(original_text, 'Hungarian')
            google_translation = self.translator.translate_with_google(original_text, 'Hungarian')
            
            if llm_translation and google_translation:
                llm_metrics = self.evaluate_translation(original_text, llm_translation, reference_text)
                google_metrics = self.evaluate_translation(original_text, google_translation, reference_text)
                
                metrics.append({
                    'llm': llm_metrics,
                    'google': google_metrics
                })
        
        # Calculate average metrics
        avg_metrics = {
            'llm_overlap': np.mean([m['llm']['overlap_with_reference'] for m in metrics]),
            'llm_preserved': np.mean([m['llm']['preserved_words'] for m in metrics]),
            'google_overlap': np.mean([m['google']['overlap_with_reference'] for m in metrics]),
            'google_preserved': np.mean([m['google']['preserved_words'] for m in metrics])
        }
        
        return avg_metrics 