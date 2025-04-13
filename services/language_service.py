import requests
import os
import uuid
import time

class LanguageService:
    def translate_text(self, text, language):
        """Translate text to the specified language"""
        try:
            # Get language code
            target_lang = self._get_language_code(language)
            
            # Simple implementation using a free translation API
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"Translation API error: {response.status_code}, {response.text}")
                return text
            
            # Extract translated text from response
            result = response.json()
            translated_text = ""
            
            # Parse the nested structure
            if result and isinstance(result, list) and len(result) > 0:
                for segment in result[0]:
                    if segment and isinstance(segment, list) and len(segment) > 0:
                        translated_text += segment[0]
            
            if not translated_text:
                print("No translation returned")
                return text
                
            return translated_text
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text on error
    
    def text_to_speech(self, text, language):
        """Convert text to speech using browser TTS - placeholder"""
        # Since we're using browser TTS, this isn't needed
        # But keeping it for the API
        return None
    
    def _get_language_code(self, language):
        """Map common language names to language codes"""
        language_map = {
            "english": "en",
            "hindi": "hi",
            "telugu": "te",
            "tamil": "ta",
            "spanish": "es",
            "french": "fr",
            "german": "de",
            "chinese": "zh",
            "japanese": "ja",
            "korean": "ko",
            "russian": "ru",
            "arabic": "ar",
            "bengali": "bn",
            "malayalam": "ml",
            "marathi": "mr",
            "kannada": "kn",
            "punjabi": "pa",
            "gujarati": "gu",
            "urdu": "ur"
        }
        return language_map.get(language.lower(), "en")