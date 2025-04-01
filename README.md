# Stella AI - Emotional Support Assistant

A web-based emotional support assistant with voice capabilities.

## Setup Instructions

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Open the `frontend` folder in your browser or use a local server to serve the files.

2. You can use Python's built-in HTTP server:
```bash
cd frontend
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

## Features

- Voice input using browser's microphone
- Text-to-speech output
- Chat interface with message history
- Emotional support and therapeutic guidance
- Context-aware responses

## Usage

1. Click "Start Recording" to begin voice input
2. Speak your message
3. Click "Stop Recording" to end voice input
4. The transcribed text will appear in the input field
5. Click "Send" or press Enter to send the message
6. Stella will respond both in text and voice

You can also type messages directly in the input field and press Enter or click "Send".

## Requirements

- Python 3.7+
- Modern web browser with microphone support
- Internet connection for speech recognition and API calls 