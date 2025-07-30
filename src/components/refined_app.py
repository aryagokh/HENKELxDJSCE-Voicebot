import streamlit as st
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
import base64
import io

# Voice-related imports
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

from nlu import understand_the_user
from agent import retriever

st.set_page_config(
    page_title="Inventory Management Assistant",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Voice Configuration
VOICE_OPTIONS = {
    "gtts": "Zira (Fast and handled online, gtts library)" if GTTS_AVAILABLE else "Google TTS (Not Available)",
    "pyttsx3": "David (Privacy focused but slow, pyttsx library)" if PYTTSX3_AVAILABLE else "Offline TTS (Not Available)",
    # "disabled": "Voice Disabled"
}

VOICE_INPUT_OPTIONS = {
    "microphone": "Microphone (Speech Recognition Library)" if SPEECH_RECOGNITION_AVAILABLE else "Microphone (Not Available)",
    # "disabled": "Voice Input Disabled"
}

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem 1.5rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        max-width: 70%;
        word-wrap: break-word;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        position: relative;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        margin-right: 0;
    }
    
    .assistant-message {
        background-color: #f8f9fa;
        color: #333;
        border: 1px solid #e9ecef;
        margin-left: 0;
        margin-right: auto;
    }
    
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .message-row {
        display: flex;
        align-items: flex-end;
        gap: 0.5rem;
    }
    
    .message-row.user {
        justify-content: flex-end;
    }
    
    .message-row.assistant {
        justify-content: flex-start;
    }
    
    .chat-icon {
        font-size: 1.2rem;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    .user-icon {
        background-color: #007bff;
        color: white;
    }
    
    .assistant-icon {
        background-color: #6c757d;
        color: white;
    }
    
    .chat-text {
        font-size: 1rem;
        line-height: 1.4;
        margin: 0;
    }
    
    .chat-timestamp {
        font-size: 0.75rem;
        color: #6c757d;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .error-message {
        background-color: #dc3545;
        color: white;
        border: none;
    }
    
    .typing-indicator {
        background-color: #f8f9fa;
        color: #333;
        border: 1px solid #e9ecef;
        margin-left: 0;
        margin-right: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 45px;
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #6c757d;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.4;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }
    
    .voice-controls {
        display: flex;
        gap: 10px;
        align-items: center;
        margin-top: 10px;
    }
    
    .voice-button {
        background: #28a745;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .voice-button:hover {
        background: #218838;
    }
    
    .voice-button:disabled {
        background: #6c757d;
        cursor: not-allowed;
    }
    
    .voice-input-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .voice-input-button {
        background: #fff;
        color: #667eea;
        border: none;
        padding: 15px 25px;
        border-radius: 25px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .voice-input-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .voice-input-button:active {
        transform: translateY(0);
    }
    
    .voice-input-button.recording {
        background: #ff4757;
        color: white;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 2px 10px rgba(255, 71, 87, 0.3); }
        50% { box-shadow: 0 2px 30px rgba(255, 71, 87, 0.6); }
        100% { box-shadow: 0 2px 10px rgba(255, 71, 87, 0.3); }
    }
    
    .voice-status {
        text-align: center;
        color: white;
        margin-top: 10px;
        font-size: 0.9rem;
    }
    
    .listening-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        color: white;
        margin-top: 10px;
    }
    
    .listening-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #ff4757;
        animation: listening 1.2s infinite ease-in-out;
    }
    
    .listening-dot:nth-child(1) { animation-delay: 0s; }
    .listening-dot:nth-child(2) { animation-delay: 0.2s; }
    .listening-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes listening {
        0%, 60%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        30% {
            transform: scale(1.2);
            opacity: 1;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'current_status' not in st.session_state:
    st.session_state.current_status = ""
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True
if 'voice_method' not in st.session_state:
    st.session_state.voice_method = "gtts"
if 'auto_play_voice' not in st.session_state:
    st.session_state.auto_play_voice = True
if 'voice_input_enabled' not in st.session_state:
    st.session_state.voice_input_enabled = True
if 'voice_input_method' not in st.session_state:
    st.session_state.voice_input_method = "microphone"
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'recognized_text' not in st.session_state:
    st.session_state.recognized_text = ""
if 'auto_send_voice' not in st.session_state:
    st.session_state.auto_send_voice = False

def text_to_speech_gtts(text: str) -> str:
    """Generate audio using Google Text-to-Speech"""
    if not GTTS_AVAILABLE:
        return "<p style='color: red;'>gTTS not available. Install with: pip install gtts</p>"
    
    try:
        # Clean text for speech
        clean_text = text.replace("❌", "Error:").replace("✅", "Success:").replace("📦", "").replace("🤖", "")
        
        # Generate speech
        tts = gTTS(text=clean_text, lang='en', slow=False)
        
        # Save to BytesIO buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Encode to base64 for embedding
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        
        # Create HTML audio player
        audio_html = f"""
        <audio {'autoplay' if st.session_state.auto_play_voice else ''} controls style="width: 100%; max-width: 300px;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        
        return audio_html
        
    except Exception as e:
        return f"<p style='color: red;'>Error generating speech: {str(e)}</p>"

def text_to_speech_pyttsx3(text: str) -> str:
    """Generate audio using pyttsx3 (offline)"""
    if not PYTTSX3_AVAILABLE:
        return "<p style='color: red;'>pyttsx3 not available. Install with: pip install pyttsx3</p>"
    
    try:
        # Clean text for speech
        clean_text = text.replace("❌", "Error:").replace("✅", "Success:").replace("📦", "").replace("🤖", "")
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Configure voice settings
        engine.setProperty('rate', 150)    # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        # Try to set a good voice
        voices = engine.getProperty('voices')
        if voices:
            # Prefer female voice if available
            for voice in voices:
                if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
        
        # Save to temporary file
        temp_audio_path = "temp_speech.wav"
        engine.save_to_file(clean_text, temp_audio_path)
        engine.runAndWait()
        
        # Read and encode the audio file
        if os.path.exists(temp_audio_path):
            with open(temp_audio_path, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode()
            
            # Clean up temp file
            os.remove(temp_audio_path)
            
            # Create HTML audio player
            audio_html = f"""
            <audio {'autoplay' if st.session_state.auto_play_voice else ''} controls style="width: 100%; max-width: 300px;">
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
            """
            
            return audio_html
        else:
            return "<p style='color: red;'>Failed to generate audio file</p>"
            
    except Exception as e:
        return f"<p style='color: red;'>Error with offline TTS: {str(e)}</p>"

def generate_voice_output(text: str) -> str:
    """Generate voice output based on selected method"""
    if not st.session_state.voice_enabled or st.session_state.voice_method == "disabled":
        return ""
    
    if st.session_state.voice_method == "gtts":
        return text_to_speech_gtts(text)
    elif st.session_state.voice_method == "pyttsx3":
        return text_to_speech_pyttsx3(text)
    
    return ""

def speech_to_text_microphone() -> str:
    """Generate speech recognition using microphone and speech_recognition library"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        return "<p style='color: red;'>speech_recognition not available. Install with: pip install SpeechRecognition pyaudio</p>"
    
    try:
        # Initialize recognizer and microphone
        r = sr.Recognizer()
        
        # Use default microphone
        with sr.Microphone() as source:
            st.info("🎤 Adjusting for ambient noise... Please wait.")
            r.adjust_for_ambient_noise(source, duration=1)
            
            st.success("🎤 Ready! Please speak your query...")
            
            # Listen for audio
            audio = r.listen(source, timeout=10, phrase_time_limit=15)
            
            st.info("🔄 Processing speech...")
            
            # Recognize speech using Google Web Speech API
            try:
                text = r.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return "Could not understand the audio. Please try again."
            except sr.RequestError as e:
                return f"Error with speech recognition service: {e}"
                
    except Exception as e:
        return f"Error with microphone input: {str(e)}"

def add_to_chat_history(message: str, sender: str, timestamp: str = None):
    """Add a message to the chat history"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M:%S")
    
    st.session_state.chat_history.append({
        'message': message,
        'sender': sender,
        'timestamp': timestamp
    })

def display_typing_indicator():
    """Display typing indicator animation with current status"""
    status_text = st.session_state.current_status if st.session_state.current_status else "Processing..."
    return f"""
    <div class="message-row assistant">
        <div class="chat-icon assistant-icon">🤖</div>
        <div class="chat-message typing-indicator">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                <span style="font-size: 0.9rem; color: #666;">{status_text}</span>
            </div>
        </div>
    </div>
    <div class="chat-timestamp">Working on it...</div>
    """

def display_chat_history():
    """Display the chat history with voice support"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for i, chat in enumerate(st.session_state.chat_history):
        if chat['sender'] == 'user':
            st.markdown(f"""
            <div class="message-row user">
                <div class="chat-message user-message">
                    <div class="chat-text">{chat['message']}</div>
                </div>
                <div class="chat-icon user-icon">👤</div>
            </div>
            <div class="chat-timestamp">{chat['timestamp']}</div>
            """, unsafe_allow_html=True)
        else:
            icon_class = "assistant-icon"
            message_class = "assistant-message"
            
            if chat['message'].startswith('❌'):
                message_class = "chat-message error-message"
            
            st.markdown(f"""
            <div class="message-row assistant">
                <div class="chat-icon {icon_class}">🤖</div>
                <div class="chat-message {message_class}">
                    <div class="chat-text">{chat['message']}</div>
                </div>
            </div>
            <div class="chat-timestamp">{chat['timestamp']}</div>
            """, unsafe_allow_html=True)
            
            # Add voice output for assistant messages
            if st.session_state.voice_enabled and chat['sender'] == 'assistant':
                voice_html = generate_voice_output(chat['message'])
                if voice_html:
                    st.markdown(f'<div style="margin-left: 40px; margin-top: 5px;">{voice_html}</div>', 
                              unsafe_allow_html=True)
    
    if st.session_state.is_processing:
        st.markdown(display_typing_indicator(), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_user_query(user_input: str) -> Dict[str, Any]:
    """Process user query through NLU and Agent pipeline"""
    result = {
        'success': False,
        'final_answer': None,
        'error': None
    }
    
    try:
        # Natural Language Understanding
        nlu_response = understand_the_user(user_input)
        
        if nlu_response is None:
            result['error'] = "Failed to understand your request. Please try again."
            return result
        
        # Agent Processing
        agent_response = retriever(nlu_response.user_intent)
        
        if agent_response is None:
            result['error'] = "Failed to retrieve data from inventory. Please try again."
            return result
        
        result['final_answer'] = agent_response.paraphrased_output
        result['success'] = True
        
    except Exception as e:
        result['error'] = f"Error in processing: {str(e)}"
    
    return result

def main():
    """Main Streamlit application"""
    
    st.markdown('<h1 class="main-header">📦 Inventory Management Assistant</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🛠️ Controls")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.is_processing = False
            st.session_state.current_status = ""
            st.session_state.recognized_text = ""
            st.rerun()
        
        with st.expander("### 🎤 Voice Input Settings"):
        
            st.session_state.voice_input_enabled = st.checkbox(
                "Enable Voice Input", 
                value=st.session_state.voice_input_enabled,
                help="Allow speaking your queries instead of typing"
            )
            
            if st.session_state.voice_input_enabled:
                st.session_state.voice_input_method = st.selectbox(
                    "Voice Input Method",
                    options=list(VOICE_INPUT_OPTIONS.keys()),
                    format_func=lambda x: VOICE_INPUT_OPTIONS[x],
                    index=list(VOICE_INPUT_OPTIONS.keys()).index(st.session_state.voice_input_method)
                )
                
                # Show installation instructions for microphone method
                if st.session_state.voice_input_method == "microphone" and not SPEECH_RECOGNITION_AVAILABLE:
                    st.warning("📦 Install required packages:\n```\npip install SpeechRecognition pyaudio\n```")

                st.session_state.auto_send_voice = st.checkbox(
                "Auto-send voice input",
                value=st.session_state.auto_send_voice,
                help="Automatically send voice input without pressing enter"
                )
            
            st.markdown("### 🔊 Voice Output Settings")
            
            st.session_state.voice_enabled = st.checkbox(
                "Enable Voice Output", 
                value=st.session_state.voice_enabled,
                help='Enable voice output along with the text, representing one to one conversion'
            )
            
            if st.session_state.voice_enabled:
                st.session_state.voice_method = st.selectbox(
                    "Voice Output Method",
                    options=list(VOICE_OPTIONS.keys()),
                    format_func=lambda x: VOICE_OPTIONS[x],
                    index=list(VOICE_OPTIONS.keys()).index(st.session_state.voice_method)
                )
                
                st.session_state.auto_play_voice = st.checkbox(
                    "Auto-play voice responses",
                    value=st.session_state.auto_play_voice,
                    help="Automatically play voice when assistant responds"
                )
                
                # Show installation instructions
                if st.session_state.voice_method == "gtts" and not GTTS_AVAILABLE:
                    st.warning("📦 Install gTTS: `pip install gtts`")
                elif st.session_state.voice_method == "pyttsx3" and not PYTTSX3_AVAILABLE:
                    st.warning("📦 Install pyttsx3: `pip install pyttsx3`")
        
        st.markdown("### 📋 System Info")
        st.info(f"**Chat Messages** (Please do not exceed 5, API limit constraints): {int(len(st.session_state.chat_history)/2) if st.session_state.chat_history else 0}")
        if st.session_state.voice_enabled:
            st.info(f"**Voice Output:** {VOICE_OPTIONS[st.session_state.voice_method]}")
        if st.session_state.voice_input_enabled:
            st.info(f"**Voice Input:** {VOICE_INPUT_OPTIONS[st.session_state.voice_input_method]}")
        
        st.markdown("### 💡 Sample Queries")
        st.markdown("""
        - "What is the total count of Bonderite 6278?"
        - "What are the top 5 products present in the R&D dept. with quantity?"
        """)

    st.markdown("### 💬 Chat")
    
    if st.session_state.chat_history or st.session_state.is_processing:
        chat_container = st.container()
        with chat_container:
            display_chat_history()
    else:
        st.info("👋 Welcome! Ask me anything about your inventory data using text or voice input.")
    
    st.markdown("---")
    
    # Voice Input Interface - Only microphone method available
    if st.session_state.voice_input_enabled and st.session_state.voice_input_method == "microphone":
        if SPEECH_RECOGNITION_AVAILABLE:
            if st.button("🎤 Record Voice Input", disabled=st.session_state.is_processing):
                with st.spinner("🎤 Listening..."):
                    recognized_text = speech_to_text_microphone()
                    if recognized_text and not recognized_text.startswith("Error") and not recognized_text.startswith("Could not"):
                        st.session_state.recognized_text = recognized_text
                        st.success(f"🎤 Recognized: '{recognized_text}'")
                        
                        # Auto-send if checkbox is enabled
                        if st.session_state.auto_send_voice:
                            st.session_state.is_processing = True
                            st.session_state.current_status = "Understanding your request..."
                            add_to_chat_history(recognized_text, 'user')
                        
                        st.rerun()
                    else:
                        st.error(f"🎤 {recognized_text}")
        else:
            st.error("🎤 Speech recognition not available. Please install required packages.")
    
    # Text Input Form
    with st.form(key="chat_form", clear_on_submit=True):
        # Use recognized text if available
        default_text = st.session_state.recognized_text if st.session_state.recognized_text else ""
        
        user_input = st.text_area(
            "Type your question or use voice input above:",
            value=default_text,
            height=100,
            key="recognized-text",
            placeholder="e.g., 'What is the total count of Bonderite 6278?' or 'Show me top 5 products in R&D department'",
            disabled=st.session_state.is_processing
        )
        
        submit_button = st.form_submit_button(
            "💬 Send Message",
            disabled=st.session_state.is_processing or not user_input.strip()
        )
        
        # Clear recognized text after form submission
        if submit_button and st.session_state.recognized_text:
            st.session_state.recognized_text = ""
    
    # Process user input
    if submit_button and user_input.strip() and not st.session_state.is_processing:
        # Set processing state
        st.session_state.is_processing = True
        st.session_state.current_status = "Understanding your request..."
        
        # Add user message to chat
        add_to_chat_history(user_input.strip(), 'user')
        
        # Rerun to show user message and typing indicator
        st.rerun()
    
    # Process the query if we're in processing state
    if st.session_state.is_processing and st.session_state.chat_history:
        # Get the last user message
        last_message = None
        for msg in reversed(st.session_state.chat_history):
            if msg['sender'] == 'user':
                last_message = msg['message']
                break
        
        if last_message:
            try:
                # Update status for NLU processing
                st.session_state.current_status = "Understanding your request..."
                
                # Process through NLU pipeline
                with st.spinner("🧠 Understanding your request..."):
                    time.sleep(0.5)  # Brief delay for UI feedback
                    nlu_response = understand_the_user(last_message)
                
                if nlu_response is None:
                    error_message = "❌ I couldn't understand your request. Please try rephrasing your question."
                    add_to_chat_history(error_message, 'assistant')
                    st.session_state.is_processing = False
                    st.session_state.current_status = ""
                    st.rerun()
                    return
                
                # Update status for agent processing
                st.session_state.current_status = "Searching inventory database..."
                
                # Process through Agent pipeline
                with st.spinner("🔍 Searching inventory database..."):
                    time.sleep(0.5)  # Brief delay for UI feedback
                    agent_response = retriever(nlu_response.user_intent)
                
                if agent_response is None:
                    error_message = "❌ I couldn't retrieve the requested data from the inventory system. Please try again."
                    add_to_chat_history(error_message, 'assistant')
                    st.session_state.is_processing = False
                    st.session_state.current_status = ""
                    st.rerun()
                    return
                
                # Update status for final processing
                st.session_state.current_status = "Preparing response..."
                time.sleep(0.3)  # Brief delay for final processing
                
                # Add successful response to chat
                success_message = f"{agent_response.paraphrased_output}"
                add_to_chat_history(success_message, 'assistant')
                
            except Exception as e:
                # Handle any unexpected errors
                error_message = f"❌ An error occurred while processing your request: {str(e)}"
                add_to_chat_history(error_message, 'assistant')
            
            finally:
                # Reset processing state
                st.session_state.is_processing = False
                st.session_state.current_status = ""
                st.rerun()

    # Quick action buttons
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Inventory Summary", disabled=st.session_state.is_processing):
            if not st.session_state.is_processing:
                st.session_state.recognized_text = "Show me a summary of the current inventory"
                st.rerun()
    
    with col2:
        if st.button("🔝 Top Products", disabled=st.session_state.is_processing):
            if not st.session_state.is_processing:
                st.session_state.recognized_text = "What are the top 10 products by quantity?"
                st.rerun()
    
    with col3:
        if st.button("⚠️ Low Stock Alert", disabled=st.session_state.is_processing):
            if not st.session_state.is_processing:
                st.session_state.recognized_text = "Show me products with low stock levels"
                st.rerun()

    # Footer with usage tips
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>💡 <strong>Tips:</strong> Use voice input for hands-free operation • Ask specific questions for better results • Check sidebar for voice settings</p>
        <p>💪 <strong>Powered By Gemini API, Langchain and Google TTS</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-scroll to bottom of chat
    if st.session_state.chat_history:
        st.markdown("""
        <script>
        setTimeout(function() {
            var chatContainer = document.querySelector('.main .block-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }, 100);
        </script>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# import streamlit as st
# import time
# import json
# from datetime import datetime
# from typing import Dict, List, Any
# import sys
# import os
# import base64
# import io

# # Voice-related imports
# try:
#     import pyttsx3
#     PYTTSX3_AVAILABLE = True
# except ImportError:
#     PYTTSX3_AVAILABLE = False

# try:
#     from gtts import gTTS
#     GTTS_AVAILABLE = True
# except ImportError:
#     GTTS_AVAILABLE = False

# try:
#     import speech_recognition as sr
#     SPEECH_RECOGNITION_AVAILABLE = True
# except ImportError:
#     SPEECH_RECOGNITION_AVAILABLE = False

# from nlu import understand_the_user
# from agent import retriever

# st.set_page_config(
#     page_title="Inventory Management Assistant",
#     page_icon="📦",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Voice Configuration
# VOICE_OPTIONS = {
#     "gtts": "Zira (Fast and handled online, gtts library)" if GTTS_AVAILABLE else "Google TTS (Not Available)",
#     "pyttsx3": "David (Privacy focused but slow, pyttsx library)" if PYTTSX3_AVAILABLE else "Offline TTS (Not Available)",
#     "disabled": "Voice Disabled"
# }

# VOICE_INPUT_OPTIONS = {
#     "microphone": "Microphone (Speech Recognition Library)" if SPEECH_RECOGNITION_AVAILABLE else "Microphone (Not Available)",
#     "disabled": "Voice Input Disabled"
# }

# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: 700;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
    
#     .chat-message {
#         padding: 1rem 1.5rem;
#         border-radius: 18px;
#         margin-bottom: 1rem;
#         max-width: 70%;
#         word-wrap: break-word;
#         box-shadow: 0 1px 3px rgba(0,0,0,0.1);
#         position: relative;
#     }
    
#     .user-message {
#         background-color: #007bff;
#         color: white;
#         margin-left: auto;
#         margin-right: 0;
#     }
    
#     .assistant-message {
#         background-color: #f8f9fa;
#         color: #333;
#         border: 1px solid #e9ecef;
#         margin-left: 0;
#         margin-right: auto;
#     }
    
#     .chat-container {
#         display: flex;
#         flex-direction: column;
#         gap: 0.5rem;
#     }
    
#     .message-row {
#         display: flex;
#         align-items: flex-end;
#         gap: 0.5rem;
#     }
    
#     .message-row.user {
#         justify-content: flex-end;
#     }
    
#     .message-row.assistant {
#         justify-content: flex-start;
#     }
    
#     .chat-icon {
#         font-size: 1.2rem;
#         width: 32px;
#         height: 32px;
#         border-radius: 50%;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         flex-shrink: 0;
#     }
    
#     .user-icon {
#         background-color: #007bff;
#         color: white;
#     }
    
#     .assistant-icon {
#         background-color: #6c757d;
#         color: white;
#     }
    
#     .chat-text {
#         font-size: 1rem;
#         line-height: 1.4;
#         margin: 0;
#     }
    
#     .chat-timestamp {
#         font-size: 0.75rem;
#         color: #6c757d;
#         text-align: center;
#         margin: 0.5rem 0;
#     }
    
#     .error-message {
#         background-color: #dc3545;
#         color: white;
#         border: none;
#     }
    
#     .typing-indicator {
#         background-color: #f8f9fa;
#         color: #333;
#         border: 1px solid #e9ecef;
#         margin-left: 0;
#         margin-right: auto;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         min-height: 45px;
#     }
    
#     .typing-dots {
#         display: flex;
#         gap: 4px;
#         align-items: center;
#     }
    
#     .typing-dot {
#         width: 8px;
#         height: 8px;
#         border-radius: 50%;
#         background-color: #6c757d;
#         animation: typing 1.4s infinite ease-in-out;
#     }
    
#     .typing-dot:nth-child(1) { animation-delay: 0s; }
#     .typing-dot:nth-child(2) { animation-delay: 0.2s; }
#     .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
#     @keyframes typing {
#         0%, 60%, 100% {
#             transform: translateY(0);
#             opacity: 0.4;
#         }
#         30% {
#             transform: translateY(-10px);
#             opacity: 1;
#         }
#     }
    
#     .voice-controls {
#         display: flex;
#         gap: 10px;
#         align-items: center;
#         margin-top: 10px;
#     }
    
#     .voice-button {
#         background: #28a745;
#         color: white;
#         border: none;
#         padding: 5px 10px;
#         border-radius: 15px;
#         font-size: 0.8rem;
#         cursor: pointer;
#         display: flex;
#         align-items: center;
#         gap: 5px;
#     }
    
#     .voice-button:hover {
#         background: #218838;
#     }
    
#     .voice-button:disabled {
#         background: #6c757d;
#         cursor: not-allowed;
#     }
    
#     .voice-input-container {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 20px;
#         border-radius: 15px;
#         margin: 20px 0;
#         box-shadow: 0 4px 15px rgba(0,0,0,0.1);
#     }
    
#     .voice-input-button {
#         background: #fff;
#         color: #667eea;
#         border: none;
#         padding: 15px 25px;
#         border-radius: 25px;
#         font-size: 1.1rem;
#         font-weight: 600;
#         cursor: pointer;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         gap: 10px;
#         width: 100%;
#         transition: all 0.3s ease;
#         box-shadow: 0 2px 10px rgba(0,0,0,0.1);
#     }
    
#     .voice-input-button:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 4px 15px rgba(0,0,0,0.2);
#     }
    
#     .voice-input-button:active {
#         transform: translateY(0);
#     }
    
#     .voice-input-button.recording {
#         background: #ff4757;
#         color: white;
#         animation: pulse 1.5s infinite;
#     }
    
#     @keyframes pulse {
#         0% { box-shadow: 0 2px 10px rgba(255, 71, 87, 0.3); }
#         50% { box-shadow: 0 2px 30px rgba(255, 71, 87, 0.6); }
#         100% { box-shadow: 0 2px 10px rgba(255, 71, 87, 0.3); }
#     }
    
#     .voice-status {
#         text-align: center;
#         color: white;
#         margin-top: 10px;
#         font-size: 0.9rem;
#     }
    
#     .listening-indicator {
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         gap: 5px;
#         color: white;
#         margin-top: 10px;
#     }
    
#     .listening-dot {
#         width: 6px;
#         height: 6px;
#         border-radius: 50%;
#         background-color: #ff4757;
#         animation: listening 1.2s infinite ease-in-out;
#     }
    
#     .listening-dot:nth-child(1) { animation-delay: 0s; }
#     .listening-dot:nth-child(2) { animation-delay: 0.2s; }
#     .listening-dot:nth-child(3) { animation-delay: 0.4s; }
    
#     @keyframes listening {
#         0%, 60%, 100% {
#             transform: scale(0.8);
#             opacity: 0.5;
#         }
#         30% {
#             transform: scale(1.2);
#             opacity: 1;
#         }
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize session state
# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []
# if 'is_processing' not in st.session_state:
#     st.session_state.is_processing = False
# if 'current_status' not in st.session_state:
#     st.session_state.current_status = ""
# if 'voice_enabled' not in st.session_state:
#     st.session_state.voice_enabled = True
# if 'voice_method' not in st.session_state:
#     st.session_state.voice_method = "gtts"
# if 'auto_play_voice' not in st.session_state:
#     st.session_state.auto_play_voice = True
# if 'voice_input_enabled' not in st.session_state:
#     st.session_state.voice_input_enabled = True
# if 'voice_input_method' not in st.session_state:
#     st.session_state.voice_input_method = "microphone"
# if 'is_listening' not in st.session_state:
#     st.session_state.is_listening = False
# if 'recognized_text' not in st.session_state:
#     st.session_state.recognized_text = ""
# if 'auto_send_voice' not in st.session_state:
#     st.session_state.auto_send_voice = False

# def text_to_speech_gtts(text: str) -> str:
#     """Generate audio using Google Text-to-Speech"""
#     if not GTTS_AVAILABLE:
#         return "<p style='color: red;'>gTTS not available. Install with: pip install gtts</p>"
    
#     try:
#         # Clean text for speech
#         clean_text = text.replace("❌", "Error:").replace("✅", "Success:").replace("📦", "").replace("🤖", "")
        
#         # Generate speech
#         tts = gTTS(text=clean_text, lang='en', slow=False)
        
#         # Save to BytesIO buffer
#         audio_buffer = io.BytesIO()
#         tts.write_to_fp(audio_buffer)
#         audio_buffer.seek(0)
        
#         # Encode to base64 for embedding
#         audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        
#         # Create HTML audio player
#         audio_html = f"""
#         <audio {'autoplay' if st.session_state.auto_play_voice else ''} controls style="width: 100%; max-width: 300px;">
#             <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
#             Your browser does not support the audio element.
#         </audio>
#         """
        
#         return audio_html
        
#     except Exception as e:
#         return f"<p style='color: red;'>Error generating speech: {str(e)}</p>"

# def text_to_speech_pyttsx3(text: str) -> str:
#     """Generate audio using pyttsx3 (offline)"""
#     if not PYTTSX3_AVAILABLE:
#         return "<p style='color: red;'>pyttsx3 not available. Install with: pip install pyttsx3</p>"
    
#     try:
#         # Clean text for speech
#         clean_text = text.replace("❌", "Error:").replace("✅", "Success:").replace("📦", "").replace("🤖", "")
        
#         # Initialize TTS engine
#         engine = pyttsx3.init()
        
#         # Configure voice settings
#         engine.setProperty('rate', 150)    # Speed of speech
#         engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
#         # Try to set a good voice
#         voices = engine.getProperty('voices')
#         if voices:
#             # Prefer female voice if available
#             for voice in voices:
#                 if 'male' in voice.name.lower() or 'david' in voice.name.lower():
#                     engine.setProperty('voice', voice.id)
#                     break
        
#         # Save to temporary file
#         temp_audio_path = "temp_speech.wav"
#         engine.save_to_file(clean_text, temp_audio_path)
#         engine.runAndWait()
        
#         # Read and encode the audio file
#         if os.path.exists(temp_audio_path):
#             with open(temp_audio_path, "rb") as audio_file:
#                 audio_base64 = base64.b64encode(audio_file.read()).decode()
            
#             # Clean up temp file
#             os.remove(temp_audio_path)
            
#             # Create HTML audio player
#             audio_html = f"""
#             <audio {'autoplay' if st.session_state.auto_play_voice else ''} controls style="width: 100%; max-width: 300px;">
#                 <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
#                 Your browser does not support the audio element.
#             </audio>
#             """
            
#             return audio_html
#         else:
#             return "<p style='color: red;'>Failed to generate audio file</p>"
            
#     except Exception as e:
#         return f"<p style='color: red;'>Error with offline TTS: {str(e)}</p>"

# def generate_voice_output(text: str) -> str:
#     """Generate voice output based on selected method"""
#     if not st.session_state.voice_enabled or st.session_state.voice_method == "disabled":
#         return ""
    
#     if st.session_state.voice_method == "gtts":
#         return text_to_speech_gtts(text)
#     elif st.session_state.voice_method == "pyttsx3":
#         return text_to_speech_pyttsx3(text)
    
#     return ""

# def speech_to_text_microphone() -> str:
#     """Generate speech recognition using microphone and speech_recognition library"""
#     if not SPEECH_RECOGNITION_AVAILABLE:
#         return "<p style='color: red;'>speech_recognition not available. Install with: pip install SpeechRecognition pyaudio</p>"
    
#     try:
#         # Initialize recognizer and microphone
#         r = sr.Recognizer()
        
#         # Use default microphone
#         with sr.Microphone() as source:
#             st.info("🎤 Adjusting for ambient noise... Please wait.")
#             r.adjust_for_ambient_noise(source, duration=1)
            
#             st.success("🎤 Ready! Please speak your query...")
            
#             # Listen for audio
#             audio = r.listen(source, timeout=10, phrase_time_limit=15)
            
#             st.info("🔄 Processing speech...")
            
#             # Recognize speech using Google Web Speech API
#             try:
#                 text = r.recognize_google(audio)
#                 return text
#             except sr.UnknownValueError:
#                 return "Could not understand the audio. Please try again."
#             except sr.RequestError as e:
#                 return f"Error with speech recognition service: {e}"
                
#     except Exception as e:
#         return f"Error with microphone input: {str(e)}"

# def add_to_chat_history(message: str, sender: str, timestamp: str = None):
#     """Add a message to the chat history"""
#     if timestamp is None:
#         timestamp = datetime.now().strftime("%H:%M:%S")
    
#     st.session_state.chat_history.append({
#         'message': message,
#         'sender': sender,
#         'timestamp': timestamp
#     })

# def display_typing_indicator():
#     """Display typing indicator animation with current status"""
#     status_text = st.session_state.current_status if st.session_state.current_status else "Processing..."
#     return f"""
#     <div class="message-row assistant">
#         <div class="chat-icon assistant-icon">🤖</div>
#         <div class="chat-message typing-indicator">
#             <div style="display: flex; align-items: center; gap: 10px;">
#                 <div class="typing-dots">
#                     <div class="typing-dot"></div>
#                     <div class="typing-dot"></div>
#                     <div class="typing-dot"></div>
#                 </div>
#                 <span style="font-size: 0.9rem; color: #666;">{status_text}</span>
#             </div>
#         </div>
#     </div>
#     <div class="chat-timestamp">Working on it...</div>
#     """

# def display_chat_history():
#     """Display the chat history with voice support"""
#     st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
#     for i, chat in enumerate(st.session_state.chat_history):
#         if chat['sender'] == 'user':
#             st.markdown(f"""
#             <div class="message-row user">
#                 <div class="chat-message user-message">
#                     <div class="chat-text">{chat['message']}</div>
#                 </div>
#                 <div class="chat-icon user-icon">👤</div>
#             </div>
#             <div class="chat-timestamp">{chat['timestamp']}</div>
#             """, unsafe_allow_html=True)
#         else:
#             icon_class = "assistant-icon"
#             message_class = "assistant-message"
            
#             if chat['message'].startswith('❌'):
#                 message_class = "chat-message error-message"
            
#             st.markdown(f"""
#             <div class="message-row assistant">
#                 <div class="chat-icon {icon_class}">🤖</div>
#                 <div class="chat-message {message_class}">
#                     <div class="chat-text">{chat['message']}</div>
#                 </div>
#             </div>
#             <div class="chat-timestamp">{chat['timestamp']}</div>
#             """, unsafe_allow_html=True)
            
#             # Add voice output for assistant messages
#             if st.session_state.voice_enabled and chat['sender'] == 'assistant':
#                 voice_html = generate_voice_output(chat['message'])
#                 if voice_html:
#                     st.markdown(f'<div style="margin-left: 40px; margin-top: 5px;">{voice_html}</div>', 
#                               unsafe_allow_html=True)
    
#     if st.session_state.is_processing:
#         st.markdown(display_typing_indicator(), unsafe_allow_html=True)
    
#     st.markdown('</div>', unsafe_allow_html=True)

# def process_user_query(user_input: str) -> Dict[str, Any]:
#     """Process user query through NLU and Agent pipeline"""
#     result = {
#         'success': False,
#         'final_answer': None,
#         'error': None
#     }
    
#     try:
#         # Natural Language Understanding
#         nlu_response = understand_the_user(user_input)
        
#         if nlu_response is None:
#             result['error'] = "Failed to understand your request. Please try again."
#             return result
        
#         # Agent Processing
#         agent_response = retriever(nlu_response.user_intent)
        
#         if agent_response is None:
#             result['error'] = "Failed to retrieve data from inventory. Please try again."
#             return result
        
#         result['final_answer'] = agent_response.paraphrased_output
#         result['success'] = True
        
#     except Exception as e:
#         result['error'] = f"Error in processing: {str(e)}"
    
#     return result

# def main():
#     """Main Streamlit application"""
    
#     st.markdown('<h1 class="main-header">📦 Inventory Management Assistant</h1>', unsafe_allow_html=True)
    
#     with st.sidebar:
#         st.markdown("### 🛠️ Controls")
        
#         if st.button("🗑️ Clear Chat History"):
#             st.session_state.chat_history = []
#             st.session_state.is_processing = False
#             st.session_state.current_status = ""
#             st.session_state.recognized_text = ""
#             st.rerun()
        
#         st.markdown("### 🎤 Voice Input Settings")
        
#         st.session_state.voice_input_enabled = st.checkbox(
#             "Enable Voice Input", 
#             value=st.session_state.voice_input_enabled,
#             help="Allow speaking your queries instead of typing"
#         )
        
#         if st.session_state.voice_input_enabled:
#             st.session_state.voice_input_method = st.selectbox(
#                 "Voice Input Method",
#                 options=list(VOICE_INPUT_OPTIONS.keys()),
#                 format_func=lambda x: VOICE_INPUT_OPTIONS[x],
#                 index=list(VOICE_INPUT_OPTIONS.keys()).index(st.session_state.voice_input_method)
#             )
            
#             # Show installation instructions for microphone method
#             if st.session_state.voice_input_method == "microphone" and not SPEECH_RECOGNITION_AVAILABLE:
#                 st.warning("📦 Install required packages:\n```\npip install SpeechRecognition pyaudio\n```")

#             st.session_state.auto_send_voice = st.checkbox(
#             "Auto-send voice input",
#             value=st.session_state.auto_send_voice,
#             help="Automatically send voice input without pressing enter"
#             )
        
#         st.markdown("### 🔊 Voice Output Settings")
        
#         st.session_state.voice_enabled = st.checkbox(
#             "Enable Voice Output", 
#             value=st.session_state.voice_enabled
#         )
        
#         if st.session_state.voice_enabled:
#             st.session_state.voice_method = st.selectbox(
#                 "Voice Output Method",
#                 options=list(VOICE_OPTIONS.keys()),
#                 format_func=lambda x: VOICE_OPTIONS[x],
#                 index=list(VOICE_OPTIONS.keys()).index(st.session_state.voice_method)
#             )
            
#             st.session_state.auto_play_voice = st.checkbox(
#                 "Auto-play voice responses",
#                 value=st.session_state.auto_play_voice,
#                 help="Automatically play voice when assistant responds"
#             )
            
#             # Show installation instructions
#             if st.session_state.voice_method == "gtts" and not GTTS_AVAILABLE:
#                 st.warning("📦 Install gTTS: `pip install gtts`")
#             elif st.session_state.voice_method == "pyttsx3" and not PYTTSX3_AVAILABLE:
#                 st.warning("📦 Install pyttsx3: `pip install pyttsx3`")
        
#         st.markdown("### 📋 System Info")
#         st.info(f"**Chat Messages:** {int(len(st.session_state.chat_history)/2) if st.session_state.chat_history else 0}")
#         if st.session_state.voice_enabled:
#             st.info(f"**Voice Output:** {VOICE_OPTIONS[st.session_state.voice_method]}")
#         if st.session_state.voice_input_enabled:
#             st.info(f"**Voice Input:** {VOICE_INPUT_OPTIONS[st.session_state.voice_input_method]}")
        
#         st.markdown("### 💡 Sample Queries")
#         st.markdown("""
#         - "What is the total count of Bonderite 6278?"
#         - "What are the top 5 products present in the R&D dept. with quantity?"
#         """)

#     st.markdown("### 💬 Chat")
    
#     if st.session_state.chat_history or st.session_state.is_processing:
#         chat_container = st.container()
#         with chat_container:
#             display_chat_history()
#     else:
#         st.info("👋 Welcome! Ask me anything about your inventory data using text or voice input.")
    
#     st.markdown("---")
    
#     # Voice Input Interface - Only microphone method available
#     if st.session_state.voice_input_enabled and st.session_state.voice_input_method == "microphone":
#         if SPEECH_RECOGNITION_AVAILABLE:
#             if st.button("🎤 Record Voice Input", disabled=st.session_state.is_processing):
#                 with st.spinner("🎤 Listening..."):
#                     recognized_text = speech_to_text_microphone()
#                     if recognized_text and not recognized_text.startswith("Error") and not recognized_text.startswith("Could not"):
#                         st.session_state.recognized_text = recognized_text
#                         st.success(f"🎤 Recognized: '{recognized_text}'")
                        
#                         # Auto-send if checkbox is enabled
#                         if st.session_state.auto_send_voice:
#                             st.session_state.is_processing = True
#                             st.session_state.current_status = "Understanding your request..."
#                             add_to_chat_history(recognized_text, 'user')
                        
#                         st.rerun()
#                     else:
#                         st.error(f"🎤 {recognized_text}")
#         else:
#             st.error("🎤 Speech recognition not available. Please install required packages.")
    
#     # Text Input Form
#     with st.form(key="chat_form", clear_on_submit=True):
#         # Use recognized text if available
#         default_text = st.session_state.recognized_text if st.session_state.recognized_text else ""
        
#         user_input = st.text_area(
#             "Type your question or use voice input above:",
#             value=default_text,
#             height=100,
#             key="recognized-text",
#             placeholder="e.g., 'What is the total count of Bonderite 6278?' or 'Show me top 5 products in R&D department'",
#             disabled=st.session_state.is_processing
#         )
        
#         submit_button = st.form_submit_button(
#             "💬 Send Message",
#             disabled=st.session_state.is_processing or not user_input.strip()
#         )
        
#         # Clear recognized text after form submission
#         if submit_button and st.session_state.recognized_text:
#             st.session_state.recognized_text = ""
    
#     # Process user input
#     if submit_button and user_input.strip() and not st.session_state.is_processing:
#         # Set processing state
#         st.session_state.is_processing = True
#         st.session_state.current_status = "Understanding your request..."
        
#         # Add user message to chat
#         add_to_chat_history(user_input.strip(), 'user')
        
#         # Rerun to show user message and typing indicator
#         st.rerun()
    
#     # Process the query if we're in processing state
#     if st.session_state.is_processing and st.session_state.chat_history:
#         # Get the last user message
#         last_message = None
#         for msg in reversed(st.session_state.chat_history):
#             if msg['sender'] == 'user':
#                 last_message = msg['message']
#                 break
        
#         if last_message:
#             try:
#                 # Update status for NLU processing
#                 st.session_state.current_status = "Understanding your request..."
                
#                 # Process through NLU pipeline
#                 with st.spinner("🧠 Understanding your request..."):
#                     time.sleep(0.5)  # Brief delay for UI feedback
#                     nlu_response = understand_the_user(last_message)
                
#                 if nlu_response is None:
#                     error_message = "❌ I couldn't understand your request. Please try rephrasing your question."
#                     add_to_chat_history(error_message, 'assistant')
#                     st.session_state.is_processing = False
#                     st.session_state.current_status = ""
#                     st.rerun()
#                     return
                
#                 # Update status for agent processing
#                 st.session_state.current_status = "Searching inventory database..."
                
#                 # Process through Agent pipeline
#                 with st.spinner("🔍 Searching inventory database..."):
#                     time.sleep(0.5)  # Brief delay for UI feedback
#                     agent_response = retriever(nlu_response.user_intent)
                
#                 if agent_response is None:
#                     error_message = "❌ I couldn't retrieve the requested data from the inventory system. Please try again."
#                     add_to_chat_history(error_message, 'assistant')
#                     st.session_state.is_processing = False
#                     st.session_state.current_status = ""
#                     st.rerun()
#                     return
                
#                 # Update status for final processing
#                 st.session_state.current_status = "Preparing response..."
#                 time.sleep(0.3)  # Brief delay for final processing
                
#                 # Add successful response to chat
#                 success_message = f"{agent_response.paraphrased_output}"
#                 add_to_chat_history(success_message, 'assistant')
                
#             except Exception as e:
#                 # Handle any unexpected errors
#                 error_message = f"❌ An error occurred while processing your request: {str(e)}"
#                 add_to_chat_history(error_message, 'assistant')
            
#             finally:
#                 # Reset processing state
#                 st.session_state.is_processing = False
#                 st.session_state.current_status = ""
#                 st.rerun()

#     # Quick action buttons
#     st.markdown("### 🚀 Quick Actions")
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         if st.button("📊 Inventory Summary", disabled=st.session_state.is_processing):
#             if not st.session_state.is_processing:
#                 st.session_state.recognized_text = "Show me a summary of the current inventory"
#                 st.rerun()
    
#     with col2:
#         if st.button("🔝 Top Products", disabled=st.session_state.is_processing):
#             if not st.session_state.is_processing:
#                 st.session_state.recognized_text = "What are the top 10 products by quantity?"
#                 st.rerun()
    
#     with col3:
#         if st.button("⚠️ Low Stock Alert", disabled=st.session_state.is_processing):
#             if not st.session_state.is_processing:
#                 st.session_state.recognized_text = "Show me products with low stock levels"
#                 st.rerun()

#     # Footer with usage tips
#     st.markdown("---")
#     st.markdown("""
#     <div style="text-align: center; color: #666; font-size: 0.9rem;">
#         <p>💡 <strong>Tips:</strong> Use voice input for hands-free operation • Ask specific questions for better results • Check sidebar for voice settings</p>
#         <p>💪 <strong>Powered By Gemini API, Langchain and Google TTS</strong></p>
#     </div>
#     """, unsafe_allow_html=True)

#     # Auto-scroll to bottom of chat
#     if st.session_state.chat_history:
#         st.markdown("""
#         <script>
#         setTimeout(function() {
#             var chatContainer = document.querySelector('.main .block-container');
#             if (chatContainer) {
#                 chatContainer.scrollTop = chatContainer.scrollHeight;
#             }
#         }, 100);
#         </script>
#         """, unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()