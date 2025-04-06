import os
from typing import List, Dict, Tuple, Set
import openai
from googletrans import Translator
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

load_dotenv()

class TranslationService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.google_translator = Translator()
        self.supported_languages = {
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Japanese': 'ja',
            'Arabic': 'ar',
            'Hindi': 'hi',
            'Portuguese': 'pt',
            'Hungarian': 'hu',
        }
        # Common placeholders found in the dataset
        self.known_placeholders = {
            'brokerName', 'dataPoints', 'countryName', 'year', 'countryTheName',
            'country', 'param name', 'param description', 'firstBrokerName',
            'secondBrokerName', 'number', 'popularity', 'Broker name'
        }
        # Create a thread pool for running async code
        self.executor = ThreadPoolExecutor(max_workers=1)

    def _preserve_placeholders(self, text: str) -> Tuple[str, List[str]]:
        """
        Preserve placeholders in the text by replacing them with temporary markers.
        Only text within square brackets [] that matches known placeholders or contains valid placeholder content
        will be preserved.
        """
        placeholders = []
        processed_text = text
        
        # Find all text within square brackets
        pattern = r'\[([^\]]+)\]'
        matches = list(re.finditer(pattern, text))
        
        # Replace each valid placeholder with a marker
        for i, match in enumerate(matches):
            full_placeholder = match.group(0)  # The complete [placeholder]
            inner_text = match.group(1)  # The text inside brackets
            
            # Only preserve if it's a known placeholder or contains valid placeholder content
            if (inner_text in self.known_placeholders or 
                any(word in inner_text for word in ['Name', 'name', 'number', 'count', 'year', 'param', 'data'])):
                placeholders.append(full_placeholder)
                processed_text = processed_text.replace(full_placeholder, f"__PH{i}__")
        
        return processed_text, placeholders

    def _restore_placeholders(self, text: str, placeholders: List[str], is_google: bool = False, target_language: str = None) -> str:
        """
        Restore placeholders in the translated text.
        Only restore markers that correspond to actual placeholders.
        """
        result = text
        
        # First pass: restore exact matches
        for i, placeholder in enumerate(placeholders):
            marker = f"__PH{i}__"
            if marker in result:
                result = result.replace(marker, placeholder)
        
        # Second pass: clean up any remaining markers that shouldn't be there
        result = re.sub(r'__PH\d+__', '', result)  # Remove any unmatched markers
        result = re.sub(r'❮❮PHX❯❯', '', result)  # Remove any legacy markers
        result = re.sub(r'\s+', ' ', result)  # Clean up extra spaces
        result = result.strip()
        
        return result

    def translate_with_llm(self, text: str, target_language: str) -> str:
        """Translate text using OpenAI's LLM."""
        # Prepare the prompt with explicit instructions about preserving square brackets
        system_prompt = """You are a professional translator. Follow these rules strictly:
1. Translate ONLY the provided text, without adding any explanations or notes
2. Preserve ALL text within square brackets [] exactly as it appears, do not translate it
3. Return ONLY the translated text, nothing else
4. Do not explain what you're doing
5. Do not include any metadata or instructions in the output"""

        user_prompt = f"""Translate this text to {target_language}, keeping all text within square brackets [] unchanged: {text}"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Verify all square brackets are preserved
            original_brackets = re.findall(r'\[.*?\]', text)
            translated_brackets = re.findall(r'\[.*?\]', translated_text)
            
            if len(original_brackets) != len(translated_brackets):
                # If brackets are missing, try one more time with a more strict prompt
                retry_prompt = f"""Translate this text to {target_language}. 
IMPORTANT: Keep ALL text within square brackets [] EXACTLY as it appears, do not translate or modify it.
Text to translate: {text}

Return ONLY the translation."""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": retry_prompt}
                    ],
                    temperature=0.1  # Lower temperature for more consistent output
                )
                
                translated_text = response.choices[0].message.content.strip()
            
            return translated_text
        except Exception as e:
            print(f"Error in LLM translation: {str(e)}")
            return None

    def translate_with_google(self, text: str, target_language: str) -> str:
        """Translate text using Google Translate as a baseline."""
        try:
            # Preserve placeholders before Google translation
            text_with_markers, placeholders = self._preserve_placeholders(text)
            
            lang_code = self.supported_languages.get(target_language)
            if not lang_code:
                raise ValueError(f"Unsupported language: {target_language}")
            
            # Perform synchronous translation
            translation = self.google_translator.translate(text_with_markers, dest=lang_code)
            result = translation.text if translation else None
            
            # Restore placeholders after translation
            if result:
                final_result = self._restore_placeholders(result, placeholders, is_google=True, target_language=target_language)
                
                # Verify all placeholders were restored
                missing_placeholders = []
                for placeholder in placeholders:
                    if placeholder not in final_result:
                        missing_placeholders.append(placeholder)
                
                if missing_placeholders:
                    print(f"Warning: Some placeholders were not restored in Google translation: {missing_placeholders}")
                
                return final_result
            return None
        except Exception as e:
            print(f"Error in Google translation: {str(e)}")
            return None

    def get_supported_languages(self) -> Dict[str, str]:
        """Return the list of supported languages and their codes."""
        return self.supported_languages 