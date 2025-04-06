import pandas as pd
from typing import Dict, List, Tuple, Callable
import numpy as np
from translator import TranslationService
from nltk.translate.meteor_score import meteor_score
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import nltk
import warnings

# Download required NLTK data
try:
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
except Exception as e:
    warnings.warn(f"Failed to download NLTK data: {str(e)}")

class TranslationEvaluator:
    def __init__(self):
        self.translator = TranslationService()
        self.smoothing = SmoothingFunction().method1

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """Load the evaluation dataset."""
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if 'translated_value' in df.columns:
            df = df.rename(columns={'translated_value': 'label'})
        return df

    def calculate_meteor_score(self, reference: str, candidate: str) -> float:
        """Calculate METEOR score for a translation."""
        try:
            # Tokenize the strings
            reference_tokens = nltk.word_tokenize(reference.lower())
            candidate_tokens = nltk.word_tokenize(candidate.lower())
            return meteor_score([reference_tokens], candidate_tokens)
        except Exception as e:
            print(f"Error calculating METEOR score: {str(e)}")
            return 0.0

    def calculate_bleu_score(self, reference: str, candidate: str) -> float:
        """Calculate BLEU score for a translation."""
        try:
            # Tokenize the strings
            reference_tokens = [nltk.word_tokenize(reference.lower())]
            candidate_tokens = nltk.word_tokenize(candidate.lower())
            return sentence_bleu(reference_tokens, candidate_tokens, smoothing_function=self.smoothing)
        except Exception as e:
            print(f"Error calculating BLEU score: {str(e)}")
            return 0.0

    def evaluate_translation(self, reference_text: str, llm_translation: str, 
                           google_translation: str) -> Dict[str, float]:
        """Evaluate translations using METEOR and BLEU scores."""
        # Calculate METEOR scores
        llm_meteor = self.calculate_meteor_score(reference_text, llm_translation)
        google_meteor = self.calculate_meteor_score(reference_text, google_translation)
        
        # Calculate BLEU scores
        llm_bleu = self.calculate_bleu_score(reference_text, llm_translation)
        google_bleu = self.calculate_bleu_score(reference_text, google_translation)
        
        return {
            'llm_meteor': llm_meteor,
            'google_meteor': google_meteor,
            'llm_bleu': llm_bleu,
            'google_bleu': google_bleu
        }

    def evaluate_dataset(self, dataset_path: str, target_language: str = 'Hungarian', 
                        progress_callback: Callable[[int, int, Dict], None] = None) -> Dict[str, float]:
        """
        Evaluate the entire dataset using both translation methods and multiple metrics.
        
        Args:
            dataset_path: Path to the dataset CSV file
            target_language: Target language for translation
            progress_callback: Callback function for progress updates
                             Args: current_row, total_rows, latest_metrics
        """
        df = self.load_dataset(dataset_path)
        metrics_list = []
        
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            try:
                original_text = row['english']
                reference_text = row['label']
                
                # Get translations
                llm_translation = self.translator.translate_with_llm(original_text, target_language)
                google_translation = self.translator.translate_with_google(original_text, target_language)
                
                if llm_translation and google_translation:
                    metrics = self.evaluate_translation(reference_text, llm_translation, google_translation)
                    metrics_list.append(metrics)
                    
                    # Calculate running averages for progress updates
                    if progress_callback and metrics_list:
                        current_metrics = {
                            'llm_meteor': np.mean([m['llm_meteor'] for m in metrics_list]),
                            'google_meteor': np.mean([m['google_meteor'] for m in metrics_list]),
                            'llm_bleu': np.mean([m['llm_bleu'] for m in metrics_list]),
                            'google_bleu': np.mean([m['google_bleu'] for m in metrics_list])
                        }
                        progress_callback(idx + 1, total_rows, current_metrics)
                
            except Exception as e:
                print(f"Error processing row {idx}: {str(e)}")
                continue
        
        # Calculate final metrics
        avg_metrics = {
            'llm_meteor': np.mean([m['llm_meteor'] for m in metrics_list]),
            'google_meteor': np.mean([m['google_meteor'] for m in metrics_list]),
            'llm_bleu': np.mean([m['llm_bleu'] for m in metrics_list]),
            'google_bleu': np.mean([m['google_bleu'] for m in metrics_list])
        }
        
        # Calculate standard deviations
        std_metrics = {
            'llm_meteor_std': np.std([m['llm_meteor'] for m in metrics_list]),
            'google_meteor_std': np.std([m['google_meteor'] for m in metrics_list]),
            'llm_bleu_std': np.std([m['llm_bleu'] for m in metrics_list]),
            'google_bleu_std': np.std([m['google_bleu'] for m in metrics_list])
        }
        
        # Combine metrics
        all_metrics = {**avg_metrics, **std_metrics}
        
        return all_metrics 