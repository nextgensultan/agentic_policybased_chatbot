from flask import Flask, render_template, request, jsonify, session
import os
import tempfile
import base64
from ASR import SpeechToText
from LLM import setup_llm, setup_agent
from knowledege_base import get_return_policy_kb

app = Flask(__name__)
app.secret_key = os.urandom(24)  

llm = setup_llm()
kb = get_return_policy_kb()
agent_executor = setup_agent(llm)
speech_to_text = SpeechToText()

@app.before_request
def before_request():
    if 'messages' not in session:
        session['messages'] = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        audio_data = request.json.get('audio')
        if not audio_data:
            return jsonify({'error': 'No audio data received'}), 400
        
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
            tmp_audio.write(audio_bytes)
            audio_file_path = tmp_audio.name
        transcription = speech_to_text.speech_to_text(audio_file_path)
        
        os.unlink(audio_file_path)
        
        if isinstance(transcription, dict) and 'error' in transcription:
            return jsonify({'error': str(transcription['error'])}), 500
        
        messages = session.get('messages', [])
        messages.append({"role": "user", "content": transcription})
        
        response = agent_executor.invoke({"input": transcription})
        answer = response.get("output", "I'm sorry, I couldn't process that.")
        
        messages.append({"role": "assistant", "content": answer})
        
        session['messages'] = messages
        
        return jsonify({
            'transcription': transcription,
            'response': answer,
            'messages': messages
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        text_input = request.json.get('message')
        if not text_input:
            return jsonify({'error': 'No message received'}), 400
        
        messages = session.get('messages', [])
        messages.append({"role": "user", "content": text_input})
        
        response = agent_executor.invoke({"input": text_input})
        answer = response.get("output", "I'm sorry, I couldn't process that.")
        
        messages.append({"role": "assistant", "content": answer})
        
        session['messages'] = messages
        
        return jsonify({
            'response': answer,
            'messages': messages
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_messages', methods=['GET'])
def get_messages():
    return jsonify({'messages': session.get('messages', [])})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['messages'] = []
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 