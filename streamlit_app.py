import streamlit as st
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

from src.components.nlu import understand_the_user
from src.components.agent import retriever

st.set_page_config(
    page_title="Inventory Management Assistant",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
</style>
""", unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'current_status' not in st.session_state:
    st.session_state.current_status = ""

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
    """Display the chat history"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for chat in st.session_state.chat_history:
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
            st.rerun()
        
        st.markdown("### 📋 System Info")
        st.info(f"**Chat Messages:** {int(len(st.session_state.chat_history)/2)}")
        
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
        st.info("👋 Welcome! Ask me anything about your inventory data.")
    
    st.markdown("---")
    
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "💭 Ask me about your inventory:",
            placeholder="e.g., Where is Bonderite 6278 located?",
            height=80,
            key="user_input",
            disabled=st.session_state.is_processing
        )
        
        submit_button = st.form_submit_button(
            "📤 Send Message", 
            use_container_width=True,
            disabled=st.session_state.is_processing
        )
    
    if submit_button and user_input.strip() and not st.session_state.is_processing:
        add_to_chat_history(user_input, "user")
        st.session_state.is_processing = True
        st.rerun()
    
    if st.session_state.is_processing:
        latest_message = st.session_state.chat_history[-1]['message']
        
        result = process_user_query(latest_message)
        
        if result['success']:
            add_to_chat_history(result['final_answer'], "assistant")
        else:
            error_msg = result['error'] or "Something went wrong. Please try again."
            add_to_chat_history(f"❌ Error: {error_msg}", "assistant")
        
        st.session_state.is_processing = False
        st.session_state.current_status = ""
        
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
        "Inventory Management Assistant • Powered by Google Gemini AI"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()