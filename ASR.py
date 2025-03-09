import requests
import os
import base64
from dotenv import load_dotenv
load_dotenv()

class SpeechToText:
    def __init__(self):
        self.api_url = "https://api.assemblyai.com/v2/transcript"
        self.api_key = os.getenv('ASSEMBLYAI_API_KEY') or 'ef8740c7c38d43a18f3c8f17e109b6ab'
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
        
    def speech_to_text(self, audio_file_path):
        try:
            upload_url = self._upload_file(audio_file_path)
            if "error" in upload_url:
                return upload_url
                
            transcript_response = self._request_transcript(upload_url)
            if "error" in transcript_response:
                return transcript_response
                
            transcript_id = transcript_response["id"]
            return self._get_transcript_result(transcript_id)
            
        except Exception as e:
            print(f"Error processing audio file: {e}")
            return {"error": str(e)}
    
    def _upload_file(self, audio_file_path):
        try:
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
                
            upload_endpoint = "https://api.assemblyai.com/v2/upload"
            upload_response = requests.post(
                upload_endpoint,
                headers={"authorization": self.api_key},
                data=audio_data
            )
            upload_response.raise_for_status()
            return upload_response.json()["upload_url"]
        except Exception as e:
            return {"error": f"Error uploading file: {str(e)}"}
    
    def _request_transcript(self, audio_url):
        try:
            json_data = {
                "audio_url": audio_url,
                "language_code": "en"  # Default to English
            }
            response = requests.post(
                self.api_url,
                json=json_data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Error requesting transcript: {str(e)}"}
    
    def _get_transcript_result(self, transcript_id):
        try:
            polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            while True:
                polling_response = requests.get(
                    polling_endpoint,
                    headers=self.headers
                )
                polling_response.raise_for_status()
                
                status = polling_response.json()
                if status["status"] == "completed":
                    return status["text"]
                elif status["status"] == "error":
                    return {"error": f"Transcription error: {status.get('error', 'Unknown error')}"}
                
                # Wait a bit before polling again
                import time
                time.sleep(3)
        except Exception as e:
            return {"error": f"Error getting transcript result: {str(e)}"}