import asyncio
import platform
import subprocess
import streamlit as st
import base64
from datetime import datetime
import os
from openai import OpenAI
import uuid

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(
    page_title="AutoDiag AI - Car Diagnostic Expert",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'input_key' not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())
if 'last_user_input_content' not in st.session_state:
    st.session_state.last_user_input_content = ""

# Try to load logo
logo_base64 = ""
try:
    with open("logo.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Logo file 'logo.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"An error occurred while loading the logo: {e}")

st.markdown("""
    <style>
        /* Aggressive removal of all default margins and padding */
        html, body, #root, [data-testid="stAppViewContainer"], .main, .block-container {
            margin: 0 !important;
            padding: 0 !important;
            min-height: 100vh !important;
        }
        
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            display: none !important;
            height: 0 !important;
        }
        
        .main .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            max-width: none !important;
        }
        
        .main > .block-container > div {
            padding: 0 !important;
            margin: 0 !important;
        }
        
        [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        .element-container {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* ChatGPT-like simple interface */
        .stApp {
            background: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}

        .main-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            position: fixed;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
        }

        .chat-header {
            background: #fff;
            padding: 10px 20px;
            text-align: center;
            border-bottom: 1px solid #e5e5e5;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            width: 40px;
            height: 40px;
            margin: 0 auto 10px auto;
            display: block;
        }

        .chat-title {
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin: 0;
        }

        .messages-container {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        .message {
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }

        .user-message {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
        }

        .user-avatar {
            background: #10a37f;
            color: white;
        }

        .bot-avatar {
            background: #f7f7f8;
            color: #333;
        }

        .message-content {
            max-width: calc(100% - 44px);
            font-size: 16px;
            line-height: 1.5;
            color: #333;
        }

        .user-message .message-content {
            background: #f7f7f8;
            padding: 12px 16px;
            border-radius: 18px;
            border-bottom-right-radius: 4px;
        }

        .bot-message .message-content {
            padding: 12px 0;
        }

        .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }

        .welcome-message {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .welcome-message h2 {
            font-size: 28px;
            margin-bottom: 12px;
            color: #333;
            font-weight: 600;
        }

        .welcome-message p {
            font-size: 16px;
            color: #666;
        }

        .input-area {
            background: #fff;
            padding: 20px;
            border-top: 1px solid #e5e5e5;
            position: sticky;
            bottom: 0;
        }

        .input-container {
            max-width: 800px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .stTextInput {
            flex: 1;
        }

        .stTextInput > div > div > input {
            background: #f7f7f8 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
            color: #333 !important;
            resize: none !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #10a37f !important;
            box-shadow: 0 0 0 2px rgba(16, 163, 127, 0.1) !important;
            outline: none !important;
        }

        .stTextInput > div > div > input::placeholder {
            color: #9ca3af !important;
        }

        .stButton > button {
            background: #10a37f !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: background 0.2s !important;
        }

        .stButton > button:hover {
            background: #0d8a6b !important;
        }

        .stButton > button:disabled {
            background: #d1d5db !important;
            cursor: not-allowed !important;
        }

        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            color: #666;
            font-style: italic;
        }

        .typing-dots {
            display: flex;
            gap: 2px;
        }

        .typing-dots span {
            width: 4px;
            height: 4px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dots span:nth-child(1) { animation-delay: 0s; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 80%, 100% { opacity: 0.3; }
            40% { opacity: 1; }
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header with logo
st.markdown(f"""
    <div class="chat-header">
        {f'<img src="data:image/png;base64,{logo_base64}" class="logo">' if logo_base64 else ''}
        <h1 class="chat-title">AutoDiag AI</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="messages-container">', unsafe_allow_html=True)

# Welcome message or conversation display
if not st.session_state.conversation:
    st.markdown("""
        <div class="welcome-message">
            <h2>Welcome to AutoDiag AI</h2>
            <p>Describe your car problems and get expert diagnostic solutions</p>
        </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.conversation:
        message_class = "user-message" if message["role"] == "user" else "bot-message"
        avatar_class = "user-avatar" if message["role"] == "user" else "bot-avatar"
        avatar_text = "U" if message["role"] == "user" else "AI"
        
        st.markdown(f"""
            <div class="message {message_class}">
                <div class="message-avatar {avatar_class}">{avatar_text}</div>
                <div class="message-content">
                    <div>{message["content"]}</div>
                    <div class="message-time">{message["timestamp"]}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input section
st.markdown('<div class="input-area">', unsafe_allow_html=True)
st.markdown('<div class="input-container">', unsafe_allow_html=True)

user_input = st.text_input(
    "Type your message",
    placeholder="Describe your car problem...",
    key=st.session_state.input_key,
    label_visibility="collapsed"
)

send_button = st.button("Send", key="send_button_fixed")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Handle user input
if send_button or (user_input and user_input.strip() != "" and user_input != st.session_state.last_user_input_content):
    if user_input.strip() != "":
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.conversation.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        st.session_state.conversation.append({
            "role": "bot",
            "content": '<div class="typing-dots"><span></span><span></span><span></span></div>',
            "timestamp": datetime.now().strftime("%I:%M %p")
        })
        st.session_state.input_key = str(uuid.uuid4())
        st.session_state.last_user_input_content = user_input
        st.rerun()

# Process bot response
if st.session_state.conversation and st.session_state.conversation[-1]["role"] == "bot" and '<div class="typing-dots">' in st.session_state.conversation[-1]["content"]:
    current_user_question = st.session_state.conversation[-2]["content"] if len(st.session_state.conversation) >= 2 and st.session_state.conversation[-2]["role"] == "user" else "Tell me about car diagnostics."
    
    try:
        system_instruction = """
You are AutoDiag AI, a highly skilled automotive diagnostic expert with decades of experience in car repair and maintenance. You specialize in diagnosing car problems and providing comprehensive solutions.

Your expertise covers:
- Engine problems (misfires, overheating, oil leaks, performance issues)
- Transmission issues (shifting problems, fluid leaks, clutch problems)
- Electrical systems (battery, alternator, starter, sensors, warning lights)
- Brake systems (squeaking, grinding, pedal problems, fluid leaks)
- Suspension and steering (vibrations, alignment, shocks, struts)
- Air conditioning and heating systems
- Exhaust systems and emissions
- Fuel system problems
- Cooling system issues

When responding:
- **Ask relevant follow-up questions** to better understand the problem (car make/model/year, mileage, when the problem occurs, any recent maintenance)
- **Provide step-by-step diagnostic procedures** the user can follow
- **List possible causes** from most likely to least likely
- **Suggest immediate actions** (safe to drive? need immediate attention?)
- **Estimate repair costs** when possible (provide ranges)
- **Recommend preventive maintenance** to avoid similar issues
- **Always prioritize safety** - warn about dangerous conditions

If the user greets you (Hi, Hello), warmly welcome them and ask about their car troubles.

For diagnostic requests:
1. Gather symptom details
2. Ask clarifying questions if needed
3. Provide possible diagnoses ranked by likelihood
4. Suggest diagnostic steps or tests
5. Recommend next actions
6. Always end by asking if they need more help or have other questions (vary your phrasing)

Maintain a professional, helpful tone like an experienced mechanic who genuinely wants to help solve car problems.
        """
        
        # Build conversation history for the LLM
        messages_for_llm = [{"role": "system", "content": system_instruction}]
        
        # Add conversation history
        for msg in st.session_state.conversation[:-1]:
            if '<div class="typing-dots">' not in msg["content"]:
                role = "assistant" if msg["role"] == "bot" else msg["role"]
                messages_for_llm.append({"role": role, "content": msg["content"]})
        
        # Add current question
        messages_for_llm.append({"role": "user", "content": current_user_question})

        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_llm,
            max_tokens=2000,
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()

    except Exception as e:
        answer = f"I'm having trouble accessing my diagnostic systems right now: {str(e)}. Please try again or describe your car problem in more detail."
        print(f"OpenAI API Error: {e}")

    # Remove typing indicator and add actual response
    if st.session_state.conversation and st.session_state.conversation[-1]["role"] == "bot" and '<div class="typing-dots">' in st.session_state.conversation[-1]["content"]:
        st.session_state.conversation.pop()

    st.session_state.conversation.append({
        "role": "bot",
        "content": answer,
        "timestamp": datetime.now().strftime("%I:%M %p")
    })
    st.rerun()

# Auto-scroll to bottom
st.markdown("""
    <script>
        const messagesArea = document.querySelector('.messages-area');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    </script>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
