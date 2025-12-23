import os
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import firestore_v1 as firestore
from google.oauth2 import service_account

# Load environment variables
load_dotenv()

project_id = os.getenv("FIRESTORE_PROJECT_ID")
creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not creds_path or not os.path.exists(creds_path):
    raise FileNotFoundError(f"Firestore credentials file not found at {creds_path}")

# Load credentials and initialize client
try:
    credentials = service_account.Credentials.from_service_account_file(creds_path)
    # Note: If your database is the default one, change "tulizo" to "(default)"
    db = firestore.Client(
        project=project_id,
        credentials=credentials,
        # database="tulizo"  
    )
except Exception as e:
    print(f"CRITICAL: Failed to initialize Firestore Client: {e}")
    db = None

# ---- Conversations ----

def save_conversation(user_id, user_message, ai_response, mood=None):
    """Save a conversation turn for a user"""
    if db is None: return
    try:
        doc_ref = db.collection("users").document(user_id).collection("conversations").document()
        doc_ref.set({
            "user_message": user_message,
            "ai_response": ai_response,
            "mood": mood,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        print(f"Error saving conversation: {e}")

def get_recent_conversations(user_id, limit=5):
    """Fetch recent conversations, handling ISO conversion and API errors"""
    if db is None: return []
    try:
        docs = db.collection("users").document(user_id).collection("conversations")\
            .order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        conversations = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if "timestamp" in data and data["timestamp"]:
                # Convert Firestore timestamp to ISO string for JSON compatibility
                data["timestamp"] = data["timestamp"].isoformat()
            conversations.append(data)
        return conversations
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        return []

# ---- Tasks ----

def create_task(user_id, task_text, due_date=None):
    """Create a new task for a user"""
    if due_date is not None and not isinstance(due_date, str):
        # Convert datetime to ISO string if needed
        due_date = due_date.isoformat()
    
    doc_ref = db.collection("users").document(user_id).collection("tasks").document()
    doc_ref.set({
        "task_text": task_text,
        "due_date": due_date,  # safe now, can be None
        "status": "pending",
        "created_at": datetime.utcnow()
    })
    return doc_ref.id

def get_tasks(user_id):
    """Fetch all tasks for a user with safety checks"""
    if db is None: return []
    try:
        docs = db.collection("users").document(user_id).collection("tasks").stream()
        tasks = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Ensure dates are JSON serializable
            if "due_date" in data and data["due_date"]:
                data["due_date"] = data["due_date"].isoformat() if isinstance(data["due_date"], datetime) else data["due_date"]
            if "created_at" in data and data["created_at"]:
                data["created_at"] = data["created_at"].isoformat() if isinstance(data["created_at"], datetime) else data["created_at"]
            tasks.append(data)
        return tasks
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

def update_task(user_id, task_id, task_text=None, due_date=None, status=None):
    """Update a Firestore task"""
    doc_ref = db.collection("users").document(user_id).collection("tasks").document(task_id)
    
    updates = {}
    if task_text is not None:
        updates["task_text"] = task_text
    if due_date is not None:
        updates["due_date"] = due_date
    if status is not None:
        updates["status"] = status

    if updates:
        doc_ref.update(updates)
    
    return doc_ref.get().to_dict()

def delete_task(user_id, task_id):
    """Delete a specific task for a user"""
    if db is None: return False
    try:
        doc_ref = db.collection("users").document(user_id).collection("tasks").document(task_id)
        
        # Check if exists before deleting (optional but recommended for debugging)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        else:
            print(f"Task {task_id} not found for user {user_id}")
            return False
    except Exception as e:
        print(f"Error deleting task: {e}")
        return False


# ---- Settings ----
# ---- Voice Settings ----

def update_user_voice(user_id, voice_id, voice_name):
    """Save preferred voice ID and name to user settings"""
    if db is None: return
    try:
        doc_ref = db.collection("users").document(user_id).collection("settings").document("voice")
        doc_ref.set({
            "voice_id": voice_id,
            "voice_name": voice_name,
            "updated_at": datetime.utcnow()
        }, merge=True)
        return True
    except Exception as e:
        print(f"Error saving voice preference: {e}")
        return False

def get_user_voice(user_id):
    """Retrieve the preferred voice for the user"""
    if db is None: return None
    try:
        doc = db.collection("users").document(user_id).collection("settings").document("voice").get()
        if doc.exists:
            return doc.to_dict()
        return {"voice_id": os.getenv("VOICE_ID"), "voice_name": "Default"}
    except Exception as e:
        print(f"Error fetching voice preference: {e}")
        return None