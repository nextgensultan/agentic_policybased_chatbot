document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const recordButton = document.getElementById('recordButton');
    const recordButtonText = document.getElementById('recordButtonText');
    const recordingStatus = document.getElementById('recordingStatus');
    const transcriptionDiv = document.getElementById('transcription');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const chatContainer = document.getElementById('chatContainer');
    const clearChatButton = document.getElementById('clearChatButton');

    // State variables
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // Initialize chat history from the session
    fetchMessages();

    // Audio recording setup
    recordButton.addEventListener('click', toggleRecording);

    // Send message setup
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Clear chat
    clearChatButton.addEventListener('click', clearChat);

    // Functions
    async function toggleRecording() {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', processRecording);
            
            mediaRecorder.start();
            isRecording = true;
            
            // Update UI
            recordButton.classList.add('recording');
            recordButtonText.textContent = 'Stop Recording';
            recordingStatus.textContent = 'Recording...';
            
            // Auto-stop after 30 seconds
            setTimeout(() => {
                if (isRecording) {
                    stopRecording();
                }
            }, 30000);
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            recordingStatus.textContent = 'Error: Could not access microphone';
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            
            // Update UI
            recordButton.classList.remove('recording');
            recordButtonText.textContent = 'Start Recording';
            recordingStatus.textContent = 'Processing audio...';
            
            // Stop all audio tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    async function processRecording() {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        
        // Convert to base64
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        
        reader.onloadend = async function() {
            const base64Audio = reader.result;
            
            try {
                recordingStatus.textContent = 'Sending audio for processing...';
                
                const response = await fetch('/process_audio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ audio: base64Audio })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    recordingStatus.textContent = `Error: ${data.error}`;
                    return;
                }
                
                // Show transcription
                transcriptionDiv.style.display = 'block';
                transcriptionDiv.textContent = `"${data.transcription}"`;
                recordingStatus.textContent = 'Audio processed successfully!';
                
                // Update chat
                updateChatMessages(data.messages);
                
                // Clear after 5 seconds
                setTimeout(() => {
                    transcriptionDiv.style.display = 'none';
                    recordingStatus.textContent = '';
                }, 5000);
                
            } catch (error) {
                console.error('Error processing audio:', error);
                recordingStatus.textContent = 'Error processing audio';
            }
        };
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Clear input
        messageInput.value = '';
        
        try {
            // Optimistically add message to UI
            addMessageToChat('user', message);
            
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error('Error sending message:', data.error);
                return;
            }
            
            // Add response to chat
            updateChatMessages(data.messages);
            
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }

    function addMessageToChat(role, content) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(role === 'user' ? 'user-message' : 'assistant-message');
        
        const prefix = role === 'user' ? 'You: ' : 'Assistant: ';
        messageElement.textContent = `${prefix}${content}`;
        
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function updateChatMessages(messages) {
        // Clear chat container
        chatContainer.innerHTML = '';
        
        // Add all messages
        if (messages && messages.length) {
            messages.forEach(msg => {
                addMessageToChat(msg.role, msg.content);
            });
        }
    }

    async function fetchMessages() {
        try {
            const response = await fetch('/get_messages');
            const data = await response.json();
            
            updateChatMessages(data.messages);
            
        } catch (error) {
            console.error('Error fetching messages:', error);
        }
    }

    async function clearChat() {
        try {
            await fetch('/clear_chat', { method: 'POST' });
            chatContainer.innerHTML = '';
        } catch (error) {
            console.error('Error clearing chat:', error);
        }
    }
}); 