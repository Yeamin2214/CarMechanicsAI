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

# Try to load car background image
car_image_base64 = ""
try:
    with open("car_background.png", "rb") as img_file:
        car_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Car background image 'car_background.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading car background image: {e}")

st.markdown(f"""
    <style>
        /* Simple chat interface with car background */
        .stApp {{
            background: #f0f0f0;
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            position: relative;
        }}

        .stApp::before {{
            content: "";
            background-image: url('data:image/png;base64,{car_image_base64}');
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.1;
            z-index: -1;
        }}

        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .chat-header {{
            background: #fff;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .chat-title {{
            font-size: 24px;
            color: #333;
            margin: 0;
        }}

        .chat-subtitle {{
            font-size: 14px;
            color: #666;
            margin: 5px 0 0 0;
        }}

        /* Messages area */
        .messages-area {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        /* Message bubbles */
        .message {{
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            margin-bottom: 15px;
            font-size: 16px;
            line-height: 1.4;
        }}

        .user-message {{
            background: #007bff;
            color: white;
            margin-left: auto;
            margin-right: 0;
        }}

        .bot-message {{
            background: #f1f1f1;
            color: #333;
            margin-right: auto;
            margin-left: 0;
        }}

        .message-time {{
            font-size: 10px;
            color: rgba(0,0,0,0.5);
            margin-top: 5px;
            text-align: right;
        }}

        .bot-message .message-time {{
            text-align: left;
        }}

        /* Welcome message */
        .welcome-message {{
            text-align: center;
            color: #666;
            padding: 40px 20px;
        }}

        .welcome-message h2 {{
            font-size: 24px;
            margin-bottom: 10px;
            color: #333;
        }}

        .welcome-message p {{
            font-size: 16px;
            color: #666;
        }}

        /* Input area */
        .input-container {{
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 10px;
        }}

        .stTextInput {{
            flex-grow: 1;
        }}

        .stTextInput > div > div > input {{
            background: #f8f9fa !important;
            border: 1px solid #ddd !important;
            color: #333 !important;
            border-radius: 25px !important;
            padding: 12px 20px !important;
            font-size: 16px !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: #007bff !important;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.25) !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: #999 !important;
        }}

        .stButton > button {{
            background: #007bff !important;
            color: white !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 12px 24px !important;
            font-size: 16px !important;
            cursor: pointer !important;
        }}

        .stButton > button:hover {{
            background: #0056b3 !important;
        }}

        /* Typing indicator */
        .typing-dots {{
            display: inline-flex;
            align-items: center;
        }}

        .typing-dots span {{
            display: inline-block;
            width: 6px;
            height: 6px;
            background-color: #999;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out;
        }}

        .typing-dots span:nth-child(1) {{
            animation-delay: 0s;
        }}
        .typing-dots span:nth-child(2) {{
            animation-delay: 0.2s;
        }}
        .typing-dots span:nth-child(3) {{
            animation-delay: 0.4s;
        }}

        @keyframes typing {{
            0%, 80%, 100% {{
                transform: translateY(0);
                opacity: 0.6;
            }}
            40% {{
                transform: translateY(-3px);
                opacity: 1;
            }}
        }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Header section
st.markdown(f"""
    <div class="chat-header">
        <h1 class="chat-title">AutoDiag AI - Car Expert</h1>
        <p class="chat-subtitle">Engine • Transmission • Electrical • Diagnostics</p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="messages-area">', unsafe_allow_html=True)

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
        st.markdown(f"""
            <div class="message {message_class}">
                <div>{message["content"]}</div>
                <div class="message-time">{message["timestamp"]}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input section
st.markdown('<div class="input-container">', unsafe_allow_html=True)

user_input = st.text_input(
    "Type your message",
    placeholder="Describe your car problem (engine noise, warning lights, performance issues...)",
    key=st.session_state.input_key,
    label_visibility="collapsed"
)

send_button = st.button("Send", key="send_button_fixed")

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
