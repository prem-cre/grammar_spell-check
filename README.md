FastAPI Grammar Checking Service - Legal Domain (with WebSocket)
A high-performance Grammar and Spelling Correction API built with FastAPI, SpaCy, LanguageTool, and Symspell.
Enhanced with a custom legal dictionary (1771+ terms) and WebSocket support for real-time grammar and spelling assistance.

Features
Real-Time Assistance: WebSocket endpoint for instant grammar and spelling feedback as you type
Enhanced Legal Dictionary Support: 1,771+ legal terms for comprehensive legal document processing
Grammar Correction: Powered by LanguageTool with custom question restructuring rules
Advanced Spell-Check: Using SymSpell algorithm with configurable edit distance
Intelligent Sentence Segmentation: Handles legal abbreviations (U.S.C., C.F.R., etc.)
Performance Optimized: Sub-100ms response times for most operations
Health Monitoring: Detailed service status and diagnostics
Requirements
Python 3.8+
Java (required by LanguageTool) - Install from Adoptium
Installation
Bash

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn websockets symspellpy language-tool-python spacy

# Download SpaCy language model
python -m spacy download en_core_web_sm
Running the Service
Bash

# Start the server
uvicorn main:app --reload --port 8000
Service endpoints:

API: http://localhost:8000
Documentation: http://localhost:8000/docs
WebSocket: ws://localhost:8000/ws/realtime
API Endpoints
1. Health Check
http

GET /health
2. Spelling Suggestions
http

POST /suggestions
{
    "word": "teh",
    "max_suggestions": 3
}
3. Grammar Check
http

POST /check_sentence
{
    "sentence": "What France is capital?"
}
4. WebSocket Real-time
JavaScript

ws://localhost:8000/ws/realtime

// Send:
{
    "type": "text_input",
    "text": "This are wrong."
}

// Receive:
{
    "type": "analysis_result",
    "grammar_check": {
        "original": "This are wrong.",
        "corrected": "This is wrong.",
        "has_changes": true
    },
    "spelling_suggestions": {},
    "processing_time_ms": 45.23
}
Testing the WebSocket Service
WebSocket Test Script (test.py)
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
Received response: {"type": "analysis_result", "grammar_check": {"original": "He dont know...", "corrected": "He doesn't know what to do, so he asked his friend for advice.", "has_changes": true}, ...}
Sent ping
Received pong: {"type": "pong", "timestamp": ...}
Legal Dictionary
The legal_dictionary.txt contains 1,771+ legal terms. Format:

text

litigation  50000
plaintiff   45000
defendant   45000
To add new terms:

Add to legal_dictionary.txt (word and frequency, tab-separated)
Restart the service
Example Corrections
text

Input:  "What France is capital?"
Output: "What is the capital of France?"

Input:  "This are wrong."
Output: "This is wrong."

Input:  "He dont know what to do"
Output: "He doesn't know what to do"

Input:  "teh quik brown fox"
Output: "The quick brown fox"
Performance
Simple corrections: 60-100ms
Complex sentences: 100-150ms
First request: 3-4 seconds (model loading)
WebSocket latency: <10ms overhead
