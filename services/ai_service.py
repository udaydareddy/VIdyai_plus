# services/ai_service.py
import os
import requests
import json

class GeminiService:
    def _init_(self):
        self.api_key = os.getenv("AIzaSyB9u_DjHIUNRrMH0lLEhK4iSb0ZQRPcjyo")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flask:generateContent"
        
    def generate_content(self, prompt, language="english"):
        # Adjust prompt based on language
        if language != "english":
            prompt = f"Generate educational content in {language} for: {prompt}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 800,
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "Error generating content: " + response.text