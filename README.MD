# Tulizo AI Backend

This is the backend of the Tulizo AI productivity assistant. It is built with **FastAPI** and uses **Google Firestore** for data storage, **Gemini API** for AI responses, and **ElevenLabs** for text-to-speech functionality.

## Features

- Chat endpoint with AI-generated responses.
- Task management (create, update, list tasks).
- Mood logging.
- Voice preference management.
- Firestore integration for user data and conversations.

## Tech Stack

- Python 3.11+
- FastAPI
- Google Cloud Firestore
- Gemini API (Google AI)
- ElevenLabs Text-to-Speech
- dotenv for environment variables

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/megkl/tulizo-backend.git
   cd tulizo-backend

2. **Create a virtual environment**
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

3. **Install dependencies**
pip install -r requirements.txt

4. **Environment variables**
Create a .env file in the root directory:

FIRESTORE_PROJECT_ID=project_id
GOOGLE_APPLICATION_CREDENTIALS=serviceAccountKey.json
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=elevenlabs_api_key
VOICE_ID=elevenlabs_voice_id

5. **Run the server**
uvicorn main:app --reload


API Endpoints
POST /chat - Send a user message and get an AI response.
GET /history - Retrieve recent conversations.
GET /tasks - List user tasks.
POST /tasks - Add a new task.
POST /tasks/update - Update an existing task.