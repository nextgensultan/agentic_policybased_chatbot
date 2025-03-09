# Voice-Enabled Customer Service Chatbot
Readme generated using Claude
## Project Overview
This project implements an intelligent customer service chatbot for a retail platform, capable of handling order inquiries, returns, and policy questions. The system integrates automatic speech recognition (ASR), large language models (LLM), and vector search to create a seamless, conversational user experience.

## Features
- **Voice Recognition**: Converts spoken customer inquiries to text using AssemblyAI
- **Text Chat Interface**: Alternative text-based interaction for users who prefer typing
- **Order Management**: Lookup, tracking, and return processing for customer orders
- **Return Policy Assistant**: Answers questions about return policies using semantic search
- **Conversation Memory**: Maintains context throughout the conversation
- **Responsive Web Interface**: Clean, user-friendly interface for interactions

## Technical Components

### Speech-to-Text (ASR.py)
Integrates with AssemblyAI to convert customer voice recordings into text, enabling voice-based interactions with the chatbot.

### Language Model (LLM.py)
Utilizes Mistral 7B to power natural language understanding and generation. Implements several tools for the LLM agent:
- Order lookup by ID or email
- Return eligibility checking
- Return request processing
- Order tracking

### Knowledge Base (knowledege_base.py)
Implements a vector database using FAISS to enable semantic search of return policies:
- Splits policy documents into chunks
- Creates embeddings using Sentence Transformers
- Performs similarity search when users ask policy questions

### Web Application (flask_app.py)
Flask-based web server that provides:
- REST API endpoints for speech processing and text messaging
- Session management for conversation history
- HTML/CSS/JS frontend for user interaction

### Data (orders.csv)
Sample order data used to simulate a real order database with:
- Order IDs and customer information
- Order dates and status
- Item details and shipping locations

## Getting Started

### Prerequisites
- Python 3.8+
- Required packages listed in requirements.txt

### Installation
1. Clone this repository
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (optional):
   - ASSEMBLYAI_API_KEY: Your AssemblyAI API key
   - HUGGINGFACEHUB_API_TOKEN: Your HuggingFace API token

### Running the Application
```
python flask_app.py
```
The application will be available at http://localhost:5000

## Usage Scenarios
1. **Order Lookup**: "What's the status of my order #5?"
2. **Return Request**: "I'd like to return order #12, it doesn't fit."
3. **Policy Questions**: "What's your return policy for unworn items?"
4. **Order Tracking**: "Where is my order #7 right now?"

## Project Structure
- `flask_app.py`: Main web application
- `LLM.py`: Language model setup and tools
- `ASR.py`: Speech-to-text processing
- `knowledege_base.py`: Vector search for return policies
- `orders.csv`: Sample order database
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and other static assets

## Future Improvements
- Integration with actual order management systems
- Support for multiple languages
- More sophisticated policy understanding
- Enhanced voice processing capabilities
