# FastAPI Grammar Checking Service - Legal Domain (with WebSocket)
A high-performance Grammar and Spelling Correction API built with FastAPI, SpaCy, LanguageTool, and Symspell.
Enhanced with a custom legal dictionary (1771+ terms) and WebSocket support for real-time grammar and spelling assistance.

# Table of Contents
Overview
File Structure
Installation
Configuration
Usage
API Endpoints
Testing
Contributing
License
Contact
Overview
This service provides real-time grammar and spelling correction with special focus on legal documents. It combines multiple NLP technologies to deliver accurate corrections with sub-100ms response times. The WebSocket support enables live corrections as users type, making it ideal for document editors and legal writing tools.

# Key Features:

Real-time grammar and spelling corrections via WebSocket
Enhanced legal dictionary with 1,771+ domain-specific terms
Intelligent question restructuring (e.g., "What France is capital?" → "What is the capital of France?")
RESTful API and WebSocket endpoints
Comprehensive error handling and health monitoring
File Structure
text

grammar_spell-check/
├── main.py                 # FastAPI application with all endpoints
├── test.py                 # WebSocket testing script
├── legal_dictionary.txt    # Legal terms dictionary (1,771+ terms)
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── logs/                  # Application logs (auto-created)
Installation
Prerequisites
Python 3.8+
Java (required by LanguageTool) - Install from Adoptium
Setup Steps
Bash

# 1. Clone the repository
git clone https://github.com/yourusername/grammar_spell-check.git
cd grammar_spell-check

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download SpaCy language model
python -m spacy download en_core_web_sm
Configuration
Environment Variables (Optional)
Bash

# Create .env file
PORT=8000                    # API port (default: 8000)
LOG_LEVEL=INFO              # Logging level
MAX_EDIT_DISTANCE=2         # SymSpell edit distance
LANGUAGE_TOOL_LANG=en-US    # LanguageTool language
Legal Dictionary
The legal_dictionary.txt file contains legal terms in tab-separated format:

text

litigation	50000
plaintiff	45000
defendant	45000
To add custom terms:

Edit legal_dictionary.txt
Add terms with frequency (tab-separated)
Restart the service
Usage
Starting the Service
Bash

# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Service URLs
API Base: http://localhost:8000
API Documentation: http://localhost:8000/docs
WebSocket: ws://localhost:8000/ws/realtime
API Endpoints
1. Health Check
http

GET /health

Response:
{
    "status": "healthy",
    "version": "1.0.0",
    "services": {
        "spacy": "available",
        "languagetool": "available",
        "symspell": "available",
        "websocket": "available"
    }
}
2. Spelling Suggestions
http

POST /suggestions
Content-Type: application/json

{
    "word": "teh",
    "max_suggestions": 3,
    "verbosity": "all"
}

Response:
{
    "word": "teh",
    "suggestions": ["the", "tech", "tel"],
    "processing_time_ms": 12.34
}
3. Grammar Check (Single Sentence)
http

POST /check_sentence
Content-Type: application/json

{
    "sentence": "What France is capital?"
}

Response:
{
    "original": "What France is capital?",
    "corrected": "What is the capital of France?",
    "has_changes": true,
    "processing_time_ms": 45.67
}
4. Grammar Check (Multiple Sentences)
http

POST /check_text
Content-Type: application/json

{
    "sentence": "This are wrong. What France is capital?"
}

Response:
{
    "original": "This are wrong. What France is capital?",
    "corrected": "This is wrong. What is the capital of France?",
    "has_changes": true,
    "sentences_processed": 2,
    "processing_time_ms": 89.12
}
5. WebSocket Real-time Corrections
JavaScript

// Connect to WebSocket
ws://localhost:8000/ws/realtime

// Send message
{
    "type": "text_input",
    "text": "He dont know what to do"
}

// Receive response
{
    "type": "analysis_result",
    "grammar_check": {
        "original": "He dont know what to do",
        "corrected": "He doesn't know what to do",
        "has_changes": true
    },
    "spelling_suggestions": {
        "dont": ["don't", "font", "done"]
    },
    "processing_time_ms": 34.56
}
Testing
Testing the WebSocket Service
Test the WebSocket grammar correction endpoint using the following script:

Python

# test.py
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/realtime"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")

        # Receive welcome message
        response = await websocket.recv()
        print(f"Received welcome message: {response}")

        # Send a test message
        test_message = {
            "type": "text_input",
            "text": "He dont know what to do, so he askd his freind for advise."
        }
        await websocket.send(json.dumps(test_message))
        print(f"Sent test message: {test_message}")

        # Receive response
        response = await websocket.recv()
        print(f"Received response: {response}")

        # Send ping
        ping_message = {"type": "ping"}
        await websocket.send(json.dumps(ping_message))
        print("Sent ping")

        # Receive pong
        response = await websocket.recv()
        print(f"Received pong: {response}")

if __name__ == "__main__":
    print("Starting WebSocket test...")
    asyncio.run(test_websocket())
Run the test:
Bash

python test.py
Expected Output:
text

Starting WebSocket test...
Connected to WebSocket server
Received welcome message: {"type": "connection_established", "message": "Real-time grammar and spelling assistance connected", ...}
Sent test message: {'type': 'text_input', 'text': 'He dont know what to do, so he askd his freind for advise.'}
Received response: {"type": "analysis_result", "grammar_check": {"corrected": "He doesn't know what to do, so he asked his friend for advice.", ...}}
Sent ping
Received pong: {"type": "pong", "timestamp": ...}
