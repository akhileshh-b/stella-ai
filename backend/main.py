import os
import json
import requests
from datetime import datetime, timedelta
import logging
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pyttsx3
import tempfile

app = Flask(__name__)
CORS(app)

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Set Stella's voice to female
voices = engine.getProperty('voices')
female_voice_found = False

for voice in voices:
    if "female" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        female_voice_found = True
        break

if not female_voice_found and len(voices) > 1:
    engine.setProperty('voice', voices[1].id)

# --- Configuration Constants ---
NGROK_URL = "http://localhost:12347/"
OLLAMA_API_ENDPOINT = f"{NGROK_URL}/api/generate"
GROQ_API_KEY = os.getenv("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")

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='stella_ai.log'
)

# --- File Paths ---
CHAT_HISTORY_FILE = "chat_history.json"
USER_PROFILE_FILE = "user_profile.json"
CONTEXT_FILE = "conversation_context.txt"
REFER_CHAT_FILE = "refer_chat.txt"
STELLA_INFO_FILE = "stella_ai_info.txt"

class UserProfileManager:
    def __init__(self):
        """
        Manage user profile and persistent information
        """
        self.profile = self.load_profile()
    
    def load_profile(self):
        """
        Load existing user profile or create new
        
        Returns:
            dict: User profile information
        """
        try:
            if os.path.exists(USER_PROFILE_FILE):
                with open(USER_PROFILE_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading user profile: {e}")
            return {}
    
    def update_profile(self, key, value):
        """
        Update user profile with new information
        
        Args:
            key (str): Profile attribute to update
            value (str): Value for the attribute
        """
        try:
            self.profile[key] = value
            with open(USER_PROFILE_FILE, 'w') as f:
                json.dump(self.profile, f, indent=2)
        except Exception as e:
            logging.error(f"Error updating user profile: {e}")
    
    def get_profile_context(self):
        """
        Generate a context string from user profile
        
        Returns:
            str: Formatted profile context
        """
        context_parts = []
        if 'name' in self.profile:
            context_parts.append(f"User's name is {self.profile['name']}")
        
        return "\n".join(context_parts) if context_parts else "No additional user context available."

class ContextManager:
    @staticmethod
    def save_context(context):
        """
        Save conversation context to file
        
        Args:
            context (str): Context to save
        """
        try:
            with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
                f.write(context)
        except Exception as e:
            logging.error(f"Error saving context: {e}")
    
    @staticmethod
    def load_context():
        """
        Load conversation context from file
        
        Returns:
            str: Saved context
        """
        try:
            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "No previous context available."
        except Exception as e:
            logging.error(f"Error loading context: {e}")
            return "Error accessing context."

class MemoryManager:
    def __init__(self, max_history_days=30):
        """
        Initialize memory management system
        
        Args:
            max_history_days (int): Number of days to keep chat history
        """
        self.max_history_days = max_history_days
        self.chat_history = self.load_chat_history()
        self.user_profile_manager = UserProfileManager()
        self.context_manager = ContextManager()
    
    def load_chat_history(self):
        """
        Load existing chat history or create new if not exists
        
        Returns:
            dict: Chat history with timestamp and conversations
        """
        try:
            if os.path.exists(CHAT_HISTORY_FILE):
                with open(CHAT_HISTORY_FILE, 'r') as f:
                    history = json.load(f)
                
                # Clean up old history
                current_time = datetime.now()
                history = {
                    k: v for k, v in history.items() 
                    if (current_time - datetime.fromisoformat(k)).days <= self.max_history_days
                }
                return history
            return {}
        except Exception as e:
            logging.error(f"Error loading chat history: {e}")
            return {}
    
    def save_chat_history(self, conversation):
        """
        Save conversation to chat history
        
        Args:
            conversation (list): Conversation details to save
        """
        try:
            current_time = datetime.now().isoformat()
            self.chat_history[current_time] = conversation
            
            # Prune old history
            self.prune_history()
            
            with open(CHAT_HISTORY_FILE, 'w') as f:
                json.dump(self.chat_history, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving chat history: {e}")
    
    def prune_history(self):
        """
        Remove chat history older than max_history_days
        """
        current_time = datetime.now()
        self.chat_history = {
            k: v for k, v in self.chat_history.items() 
            if (current_time - datetime.fromisoformat(k)).days <= self.max_history_days
        }
    
    def extract_personal_info(self, user_input):
        """
        Attempt to extract and remember personal information
        
        Args:
            user_input (str): User's message
        """
        # Name extraction
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"im (\w+)",
            r"call me (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                name = match.group(1).capitalize()
                self.user_profile_manager.update_profile('name', name)
                return f"Great! I'll remember that your name is {name}."
        
        return None
    
    def prepare_conversation_context(self, user_input):
        """
        Prepare comprehensive context for conversation
        
        Args:
            user_input (str): User's current input
        
        Returns:
            str: Comprehensive context
        """
        # Check for personal info extraction
        personal_info_response = self.extract_personal_info(user_input)
        
        # Combine contexts
        context_parts = [
            "CONVERSATION CONTEXT:",
            self.context_manager.load_context(),
            "\nUSER PROFILE:",
            self.user_profile_manager.get_profile_context(),
            "\nCURRENT INPUT CONTEXT:",
            f"User said: {user_input}"
        ]
        
        full_context = "\n".join(context_parts)
        
        # Save updated context
        self.context_manager.save_context(full_context)
        
        return full_context
    
    def summarize_with_groq(self, conversation):
        """
        Use Groq API to generate an ultra-concise, keyword-focused summary
        
        Args:
            conversation (list): Conversation entries to summarize
        
        Returns:
            str: Extremely condensed summary
        """
        if not GROQ_API_KEY:
            logging.warning("Groq API key not found")
            return ""
        
        # Prepare conversation text
        conversation_text = "\n".join([
            f"User: {entry['user']}\nStella: {entry['stella']}" 
            for entry in conversation
        ])
        
        # Hyper-concise summarization prompt
        summarization_prompt = f"""
        Extract ONLY the most critical, condensed information from this conversation.
        
        RULES:
        - Extreme brevity is crucial
        - Capture names, key relationships, critical facts
        - Use shortest possible phrases
        - Remove all unnecessary words
        - Focus on unique, important information
        

        Conversation to summarize:
        {conversation_text}

        Provide the summary in a compact, keyword-driven format:
        """
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-70b-8192",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an expert at creating ultra-concise, keyword-based summaries."
                        },
                        {
                            "role": "user", 
                            "content": summarization_prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 150,
                    "top_p": 0.3
                }
            )
            
            if response.status_code == 200:
                summary = response.json()['choices'][0]['message']['content'].strip()
                
                # Clean and format summary
                cleaned_summary = self.clean_summary(summary)
                
                # Append to refer_chat.txt
                with open(REFER_CHAT_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"\n--- Condensed Summary ({datetime.now().isoformat()}) ---\n")
                    f.write(cleaned_summary)
                    f.write("\n")
                
                return cleaned_summary
            else:
                logging.error(f"Groq API error: {response.text}")
                return ""
        
        except Exception as e:
            logging.error(f"Error in Groq summarization: {e}")
            return ""
    
    def clean_summary(self, summary):
        """
        Additional cleaning method to ensure extreme conciseness
        
        Args:
            summary (str): Raw summary from Groq
        
        Returns:
            str: Hyper-condensed summary
        """
        # Remove any unnecessary punctuation or words
        summary = summary.replace('"', '').replace("'", '')
        
        # Split into key-value pairs
        cleaned_pairs = []
        for pair in summary.split(','):
            pair = pair.strip()
            if ':' in pair:
                key, value = pair.split(':', 1)
                cleaned_pairs.append(f"{key.strip().lower()}:{value.strip()}")
        
        # Rejoin with comma, prioritize most important information
        final_summary = ','.join(cleaned_pairs)
        
        # Truncate if still too long
        return final_summary[:300]
    
    def prepare_context_for_chat(self):
        """
        Prepare context by reading refer_chat.txt
        
        Returns:
            str: Context from previous conversations
        """
        try:
            if os.path.exists(REFER_CHAT_FILE):
                with open(REFER_CHAT_FILE, 'r', encoding='utf-8') as f:
                    return f.read()
            return "No previous conversation context available."
        except Exception as e:
            logging.error(f"Error reading refer_chat.txt: {e}")
            return "Error accessing conversation history."

def load_stella_info():
    """
    Load Stella AI information from file
    
    Returns:
        str: Stella AI information
    """
    try:
        with open(STELLA_INFO_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning("Stella AI information file not found.")
        return """STELLA AI: Supportive Therapeutic Emotional Learning Language Assistant - 
An AI designed to provide empathetic, context-aware emotional support through conversational interaction."""
    except Exception as e:
        logging.error(f"Error loading Stella AI info: {e}")
        return "Core Stella AI information temporarily unavailable."

def chat_with_stella(user_input, memory_manager):
    """
    Chat function using both Ngrok (Ollama) and Groq APIs

    Args:
        user_input (str): User's message
        memory_manager (MemoryManager): Memory management instance

    Returns:
        str: Stella's response
    """
    # Retrieve previous context
    previous_context = memory_manager.prepare_conversation_context(user_input)

    # Prepare system prompt with context
    system_prompt = f"""You are STELLA (Supportive Therapeutic Emotional Learning Language Assistant), an AI designed to provide empathetic support.

Identity:
- Name: Stella
- Purpose: Emotional support and compassionate interaction
- Personality: Supportive, understanding, and attentive friend

Communication Principles:
- Respond briefly and clearly
- Match user's emotional tone
- Provide therapeutic guidance
- Remember personal details shared
- Facilitate meaningful, short conversations
- if the person is worried about something, ask 3 questions with relevance to the topic one by one and on the basis of answers, give suggestions.
- Give suggestions to tackle the stress and anxiety for health first then move ahead.

Core Boundaries:
- NO engagement with illegal activities
- Prioritize user's emotional well-being
- Maintain professional yet warm approach
- DO not mention my name in the start of response.

Speak as a caring, intelligent companion ready to listen and support.
CONVERSATION CONTEXT:
{previous_context}

CORE COMMUNICATION GUIDELINES:

- Provide concise, empathetic responses
- Reference past context when relevant
- Stay focused on user's current needs
- Do not give reference of past context if its not relevant in the current need
- Maintain conversational tone
"""

    try:
        # Primary API: Ollama via Ngrok
        ollama_response = requests.post(
            OLLAMA_API_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={
                "model": "llama3.2",
                "prompt": user_input,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "repeat_penalty": 1.2
                }
            },
            timeout=10
        )

        if ollama_response.status_code == 200:
            response_data = ollama_response.json()
            stella_response = response_data['response'].strip()

            # Personalize response if name is known
            user_profile = memory_manager.user_profile_manager.profile
            if 'name' in user_profile:
                stella_response = f"{user_profile['name']}, {stella_response}"
        else:
            # Fallback to Groq if Ollama fails
            logging.warning("Ollama API failed, falling back to Groq")
            groq_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300
                }
            )

            if groq_response.status_code == 200:
                stella_response = groq_response.json()['choices'][0]['message']['content'].strip()
            else:
                raise Exception("Both Ollama and Groq APIs failed")

        # Save conversation to memory
        conversation_entry = {
            "user": user_input,
            "stella": stella_response,
            "timestamp": datetime.now().isoformat()
        }
        memory_manager.save_chat_history([conversation_entry])

        return stella_response

    except Exception as e:
        logging.error(f"Chat error: {e}")
        return "I'm having trouble responding right now. Could you try again?"

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_input = data.get('message', '')
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        memory_manager = MemoryManager()
        response = chat_with_stella(user_input, memory_manager)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        # Generate audio file
        engine.save_to_file(text, temp_path)
        engine.runAndWait()

        # Send the audio file
        return send_file(
            temp_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='response.wav'
        )

    except Exception as e:
        logging.error(f"Synthesis error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass

if __name__ == "__main__":
    app.run(debug=True, port=5000)