import os
import speech_recognition as sr
import pyttsx3
from groq import Groq

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

def speak(text):
    engine.say(text)
    engine.runAndWait()

# Initialize speech recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return "I couldn't understand. Could you repeat?"
    except sr.RequestError:
        return "I am having trouble connecting. Please check your internet."

# Set up Groq API key
api_key = os.getenv("GROQ_API_KEY", "api key")
client = Groq(api_key=api_key)

MODEL_NAME = "llama3-70b-8192"

def chatbot_response(user_input):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response.choices[0].message.content  
        return reply.strip()  # Ensure full response is spoken
    except Exception as e:
        return "I'm having some trouble. Please try again later."

# Main chatbot loop
def chat():
    introduction = "Hello! I'm Stella, your emotional support chatbot. How are you feeling today?"
    print("Stella:", introduction)
    speak(introduction)

    while True:
        user_input = recognize_speech()
        if user_input.lower() == "exit":
            speak("Goodbye! Take care.")
            break
        elif user_input:
            response = chatbot_response(user_input)
            print("Stella:", response)
            speak(response)

if __name__ == "__main__":
    chat()
