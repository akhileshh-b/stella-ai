// API endpoint
const API_URL = 'http://localhost:5000/api';

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const micButton = document.getElementById('micButton');

// Speech Recognition setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US';

// Audio context for playing responses
let currentAudio = null;

// Initialize chat interface
document.addEventListener('DOMContentLoaded', () => {
    // Add welcome message and speak it
    const welcomeMessage = "Hi there! How can I help you today?";
    const messageDiv = addMessage(welcomeMessage);
    speakResponse(welcomeMessage, messageDiv);
});

// Speech Recognition events
recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    chatInput.value = transcript;
    sendMessage();
};

recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    alert('Error with speech recognition. Please try again.');
    stopRecording();
};

recognition.onend = () => {
    stopRecording();
};

// Functions
function addMessage(message, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'stella-message'}`;
    
    // Add speaking indicator for Stella's messages
    if (!isUser) {
        const speakingIndicator = document.createElement('div');
        speakingIndicator.className = 'speaking-indicator';
        speakingIndicator.textContent = '🔊';
        speakingIndicator.style.display = 'none';
        messageDiv.appendChild(speakingIndicator);
    }
    
    const textSpan = document.createElement('p');
    textSpan.textContent = message;
    messageDiv.appendChild(textSpan);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, true);
    chatInput.value = '';

    try {
        // Send message to backend
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }

        // Add Stella's response to chat and speak it
        const messageDiv = addMessage(data.response);
        speakResponse(data.response, messageDiv);
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.');
    }
}

function startRecording() {
    try {
        recognition.start();
        micButton.classList.add('recording');
        micButton.disabled = true;
    } catch (error) {
        console.error('Error starting speech recognition:', error);
        alert('Error starting speech recognition. Please ensure you have granted microphone permissions.');
    }
}

function stopRecording() {
    recognition.stop();
    micButton.classList.remove('recording');
    micButton.disabled = false;
}

async function speakResponse(text, messageDiv) {
    console.log('Attempting to speak:', text);
    
    try {
        // Show speaking indicator
        const indicator = messageDiv.querySelector('.speaking-indicator');
        if (indicator) {
            indicator.style.display = 'inline-block';
        }

        // Get audio from backend
        const response = await fetch(`${API_URL}/synthesize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });

        if (!response.ok) {
            throw new Error('Failed to get audio from backend');
        }

        // Get the audio data
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        // Create audio element
        const audio = new Audio(audioUrl);
        
        // Stop any currently playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }
        
        currentAudio = audio;

        // Play the audio
        audio.play();

        // Update speaking indicator
        audio.onplay = () => {
            if (indicator) {
                indicator.style.display = 'inline-block';
            }
        };

        audio.onended = () => {
            if (indicator) {
                indicator.style.display = 'none';
            }
            URL.revokeObjectURL(audioUrl);
            
            // Automatically start recording after Stella finishes speaking
            setTimeout(() => {
                startRecording();
            }, 500); // Small delay before starting recording
        };

        audio.onerror = (error) => {
            console.error('Error playing audio:', error);
            if (indicator) {
                indicator.style.display = 'none';
            }
            URL.revokeObjectURL(audioUrl);
        };

    } catch (error) {
        console.error('Error in speech synthesis:', error);
        const indicator = messageDiv.querySelector('.speaking-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
}

// Event Listeners
sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

micButton.addEventListener('click', () => {
    if (micButton.classList.contains('recording')) {
        stopRecording();
    } else {
        startRecording();
    }
}); 