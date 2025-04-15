from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import requests
import json
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)

def transcribe_and_translate_with_whisper(audio_file_path):
    """Transcribe and translate audio using OpenAI's Whisper API"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None, "Error: No OpenAI API key found"
            
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Convert audio to MP3 format for better compatibility with Whisper
        mp3_file_path = audio_file_path.replace('.webm', '.mp3')
        try:
            # Try to convert using ffmpeg if available
            import subprocess
            subprocess.run(['ffmpeg', '-i', audio_file_path, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', mp3_file_path], 
                          check=True, capture_output=True)
            print(f"Converted audio to MP3 format: {mp3_file_path}")
            file_to_use = mp3_file_path
        except Exception as e:
            print(f"Could not convert audio to MP3: {str(e)}")
            file_to_use = audio_file_path
        
        with open(file_to_use, 'rb') as audio_file:
            # First, get the transcription in the original language
            files_transcribe = {
                'file': ('audio.mp3' if file_to_use.endswith('.mp3') else 'audio.webm', audio_file, 
                         'audio/mp3' if file_to_use.endswith('.mp3') else 'audio/webm'),
                'model': (None, 'whisper-1'),
                'language': (None, 'zh'),  # Mandarin Chinese
                'response_format': (None, 'json')
            }
            
            response_transcribe = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files_transcribe
            )
            
            if response_transcribe.status_code != 200:
                error_info = response_transcribe.json()
                print(f"Transcription error: {error_info}")
                
                # Check for quota exceeded error
                if 'error' in error_info and 'insufficient_quota' in str(error_info):
                    return None, "API Error: OpenAI quota exceeded. Please update your API key or check your billing details."
                    
                return None, f"API Error: {error_info.get('error', {}).get('message', 'Unknown error')}"
                
            transcription_data = response_transcribe.json()
            transcription = transcription_data.get('text', '')
            print(f"Transcription result: {transcription}")
            
            # If we got a transcription, use GPT for translation as it's more reliable
            if transcription:
                translation = translate_with_gpt(transcription)
                return transcription, translation
            
            # If transcription failed, try the direct translation endpoint as fallback
            audio_file.seek(0)
            
            # Now, get the translation to English
            files_translate = {
                'file': ('audio.mp3' if file_to_use.endswith('.mp3') else 'audio.webm', audio_file,
                         'audio/mp3' if file_to_use.endswith('.mp3') else 'audio/webm'),
                'model': (None, 'whisper-1'),
                'response_format': (None, 'json'),
                'prompt': (None, 'Translate this Mandarin Chinese speech to English accurately.'),
            }
            
            response_translate = requests.post(
                "https://api.openai.com/v1/audio/translations",
                headers=headers,
                files=files_translate
            )
            
            if response_translate.status_code != 200:
                error_info = response_translate.json()
                print(f"Translation error: {error_info}")
                
                # Check for quota exceeded error
                if 'error' in error_info and 'insufficient_quota' in str(error_info):
                    return transcription, "API Error: OpenAI quota exceeded. Please update your API key or check your billing details."
                    
                return transcription, f"Translation API Error: {error_info.get('error', {}).get('message', 'Unknown error')}"
                
            translation_data = response_translate.json()
            translation = translation_data.get('text', '')
            print(f"Translation result: {translation}")
            
            return transcription or "No transcription available", translation
    except Exception as e:
        print(f"Processing error: {str(e)}")
        return None, f"Processing error: {str(e)}"

def translate_with_gpt(text):
    """Translate text using OpenAI's GPT API (fallback method)"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "Error: No OpenAI API key found"
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a professional Mandarin Chinese to English translator. Translate the following Mandarin text to English, maintaining the tone and context accurately."},
                {"role": "user", "content": text}
            ]
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            error_info = response.json()
            return f"API Error: {error_info.get('error', {}).get('message', 'Unknown error')}"
            
        response_data = response.json()
        if 'choices' not in response_data or len(response_data['choices']) == 0:
            return "Error: No translation received from API"
            
        return response_data['choices'][0]['message']['content']
    except Exception as e:
        return f"Translation error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    """Process audio file: transcribe and translate with Whisper in one step"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
        
    audio_file = request.files['audio']
    
    # Save the audio file temporarily
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_audio:
        audio_file.save(temp_audio.name)
        temp_audio_path = temp_audio.name
    
    # Get file size for debugging
    file_size = os.path.getsize(temp_audio_path)
    print(f"Received audio file of size: {file_size} bytes")
    
    if file_size < 1000:  # If file is too small (less than 1KB)
        return jsonify({
            "transcription": "Audio file too small. Please speak longer or check your microphone.",
            "translation": "Please try recording again with a longer speech sample."
        })
    
    try:
        # Transcribe and translate the audio in one step
        transcription, translation = transcribe_and_translate_with_whisper(temp_audio_path)
        
        # If transcription succeeded but translation failed, use GPT as fallback
        if transcription and (not translation or translation.startswith("Translation API Error")):
            translation = translate_with_gpt(transcription)
        
        # Return both transcription and translation
        return jsonify({
            "transcription": transcription or "No speech detected. Please try speaking louder or longer.",
            "translation": translation or "No translation available. Please try recording again."
        })
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@app.route('/translate_text', methods=['POST'])
def translate_text():
    """Translate text directly without audio processing"""
    try:
        data = request.json
        if not data or 'mandarin_text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        mandarin_text = data['mandarin_text'].strip()
        if not mandarin_text:
            return jsonify({"error": "Empty text provided"}), 400
            
        translation = translate_with_gpt(mandarin_text)
        return jsonify({"translation": translation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(port=8080, host='0.0.0.0')
    else:
        app.run(debug=True, port=8080, host='0.0.0.0')
