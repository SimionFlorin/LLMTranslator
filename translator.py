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
        Any text within square brackets [] is considered a placeholder.
        Uses Unicode characters unlikely to be modified by translation.
        """
        placeholders = []
        processed_text = text
        
        # Find all text within square brackets
        pattern = r'\[([^\]]+)\]'
        matches = list(re.finditer(pattern, text))
        
        # Replace each placeholder with a marker using special Unicode characters
        for i, match in enumerate(matches):
            full_placeholder = match.group(0)  # The complete [placeholder]
            placeholders.append(full_placeholder)
            # Use Unicode markers that are less likely to be modified
            marker = f"❮❮PH{i}❯❯"
            processed_text = processed_text.replace(full_placeholder, marker)
        
        return processed_text, placeholders

    def _restore_placeholders(self, text: str, placeholders: List[str], is_google: bool = False, target_language: str = None) -> str:
        """
        Restore placeholders in the translated text with additional verification.
        Handles various possible formats that might appear in translations.
        """
        result = text
        
        # Special handling for Japanese Google Translate
        if is_google and target_language == 'Japanese':
            # Fix common Japanese Google Translate placeholder mangling
            result = re.sub(r'ph(\d+)❯❯', r'❮❮PH\1❯❯', result)
            result = re.sub(r'PH(\d+)❯❯', r'❮❮PH\1❯❯', result)
        
        # Define possible placeholder patterns that might appear
        placeholder_patterns = [
            r'❮❮PH(\d+)❯❯',           # Our special Unicode markers
            r'__PLACEHOLDER_(\d+)__',   # Standard format
            r'PLACEHOLDER_(\d+)',       # Modified format
            r'PlaceHolder_(\d+)',       # Another possible format
            r'Placeholder_(\d+)',       # Case variation
            r'placeholder_(\d+)',       # Lowercase variation
            r'PH(\d+)',                 # Shortened format
            r'ph(\d+)',                 # Lowercase shortened format
        ]
        
        # First, try to restore our special Unicode markers
        for i, placeholder in enumerate(placeholders):
            marker = f"❮❮PH{i}❯❯"
            if marker in result:
                result = result.replace(marker, placeholder)
        
        # Then check for any remaining placeholder patterns and restore them
        for pattern in placeholder_patterns:
            matches = re.finditer(pattern, result, re.IGNORECASE)
            for match in matches:
                try:
                    index = int(match.group(1))
                    if 0 <= index < len(placeholders):
                        result = result.replace(match.group(0), placeholders[index])
                except (ValueError, IndexError):
                    continue
        
        return result

    def translate_with_llm(self, text: str, target_language: str) -> str:
        """Translate text using OpenAI's LLM."""
        # Preserve placeholders
        text_with_markers, placeholders = self._preserve_placeholders(text)
        
        # Prepare the prompt with explicit instructions about placeholders
        system_prompt = """You are a professional translator. Follow these rules strictly:
1. Translate ONLY the provided text, without adding any explanations or notes
2. Preserve all ❮❮PHX❯❯ markers exactly as they appear
3. Return ONLY the translated text, nothing else
4. Do not explain what you're doing
5. Do not include any metadata or instructions in the output"""

        user_prompt = f"""Translate this text to {target_language}, keeping all ❮❮PHX❯❯ markers unchanged: {text_with_markers}"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # Changed to GPT-4
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            # Restore placeholders
            result = self._restore_placeholders(translated_text, placeholders)
            
            # Verify all placeholders were restored
            missing_placeholders = []
            for placeholder in placeholders:
                if placeholder not in result:
                    missing_placeholders.append(placeholder)
            
            if missing_placeholders:
                # If any placeholders are missing, try one more time with a more strict prompt
                retry_prompt = f"""Translate this text to {target_language}. The markers ❮❮PHX❯❯ MUST appear exactly as shown in the output: {text_with_markers}

Return ONLY the translation."""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",  # Changed to GPT-4
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": retry_prompt}
                    ],
                    temperature=0.2  # Lower temperature for more consistent output
                )
                
                translated_text = response.choices[0].message.content.strip()
                result = self._restore_placeholders(translated_text, placeholders)
            
            return result
        except Exception as e:
            print(f"Error in LLM translation: {str(e)}")
            return None

    async def _async_google_translate(self, text: str, lang_code: str) -> str:
        """Async function to perform Google translation."""
        try:
            translation = await self.google_translator.translate(text, dest=lang_code)
            return translation.text
        except Exception as e:
            print(f"Error in async Google translation: {str(e)}")
            return None

    def translate_with_google(self, text: str, target_language: str) -> str:
        """Translate text using Google Translate as a baseline."""
        try:
            # Preserve placeholders before Google translation
            text_with_markers, placeholders = self._preserve_placeholders(text)
            
            lang_code = self.supported_languages.get(target_language)
            if not lang_code:
                raise ValueError(f"Unsupported language: {target_language}")
            
            # Run the async translation in a thread pool
            loop = asyncio.new_event_loop()
            with ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: loop.run_until_complete(
                    self._async_google_translate(text_with_markers, lang_code)))
                result = future.result()
            
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