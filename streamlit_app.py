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

# Try to load logo (car-related logo)
logo_base64 = ""
try:
    with open("car_logo.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Logo file 'car_logo.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"An error occurred while loading the logo: {e}")

# Try to load header image (car-related header)
header_image_base64 = ""
try:
    with open("car_header.png", "rb") as img_file:
        header_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Header image 'car_header.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading header image: {e}")

# Try to load car engine background image
engine_image_base64 = ""
try:
    with open("car_engine.png", "rb") as img_file:
        engine_image_base64 = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    st.warning("Engine image 'car_engine.png' not found. Please ensure it's in the same directory.")
except Exception as e:
    st.error(f"Error loading engine image: {e}")

st.markdown(f"""
    <style>
        /* Main app styling with transparent car engine background */
        .stApp {{
            background: linear-gradient(135deg, rgba(20, 20, 30, 0.8) 0%, rgba(40, 40, 50, 0.8) 50%, rgba(30, 30, 40, 0.8) 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            position: relative;
        }}

        .stApp::before {{
            content: "";
            background-image: url('data:image/png;base64,{engine_image_base64}');
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.3;
            z-index: -1;
        }}

        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        .chat-container {{
            max-width: 950px;
            margin: auto;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 90%;
            height: 80vh;
            display: flex;
            flex-direction: column;
            background: rgba(20, 20, 30, 0.9);
            border: 2px solid rgba(255, 140, 0, 0.4);
            border-radius: 25px;
            box-shadow: 0 0 50px rgba(255, 140, 0, 0.3),
                        inset 0 0 25px rgba(255, 140, 0, 0.15);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}

        .chat-header {{
            background: linear-gradient(90deg, rgba(255, 140, 0, 0.4) 0%, rgba(220, 100, 0, 0.4) 100%);
            padding: 25px;
            text-align: center;
            border-bottom: 2px solid rgba(255, 140, 0, 0.5);
            position: relative;
        }}

        .header-image {{
            max-width: 80%;
            height: auto;
            display: block;
            margin: 0 auto;
            filter: drop-shadow(0 0 10px rgba(255, 140, 0, 0.7));
        }}

        /* Messages area */
        .messages-area {{
            flex: 1;
            overflow-y: auto;
            padding: 25px 35px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            background: rgba(20, 20, 30, 0.8);
            min-height: 0;
        }}

        /* Message bubbles */
        .message {{
            max-width: 75%;
            padding: 18px 25px;
            border-radius: 20px;
            position: relative;
            animation: fadeIn 0.6s ease-out;
            font-size: 18px; /* Increased for better readability */
            line-height: 1.8; /* Improved spacing */
            color: #E0E7E9;
        }}

        .user-message {{
            align-self: flex-start;
            background: linear-gradient(135deg, rgba(60, 60, 80, 0.6) 0%, rgba(40, 40, 60, 0.6) 100%);
            border: 1px solid rgba(60, 60, 80, 0.7);
            box-shadow: 0 6px 20px rgba(60, 60, 80, 0.5);
            margin-right: auto;
            margin-left: 0;
        }}

        .bot-message {{
            align-self: flex-end;
            background: linear-gradient(135deg, rgba(255, 140, 0, 0.6) 0%, rgba(220, 100, 0, 0.6) 100%);
            border: 1px solid rgba(255, 140, 0, 0.7);
            box-shadow: 0 6px 20px rgba(255, 140, 0, 0.5);
            margin-left: auto;
            margin-right: 0;
            color: #FFFFFF; /* High contrast text color */
        }}

        .message-time {{
            font-size: 11px;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 10px;
        }}

        .user-message .message-time {{
            text-align: right;
        }}

        .bot-message .message-time {{
            text-align: left;
        }}

        /* Welcome message */
        .welcome-message {{
            text-align: center;
            margin: auto;
            color: #E0E7E9;
            padding: 30px;
        }}

        .welcome-message h2 {{
            font-size: 30px;
            margin-bottom: 15px;
            color: #FF8C00;
            font-weight: 700;
            letter-spacing: 1.5px;
        }}

        .welcome-message p {{
            font-size: 20px;
            color: #C0C8CA;
            font-weight: 500;
            line-height: 1.7;
        }}

        /* Input area - now a flex container for input and button */
        .input-container {{
            padding: 25px 30px;
            background: rgba(20, 20, 30, 0.95);
            border-top: 2px solid rgba(255, 140, 0, 0.5);
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        /* Target Streamlit's div wrappers for flex behavior */
        .stTextInput {{
            flex-grow: 1;
            min-width: 150px;
        }}

        .stButton {{
            flex-shrink: 0;
        }}

        /* Custom input styling with 3D effect */
        .stTextInput > div > div > input {{
            background: rgba(40, 40, 50, 0.9) !important;
            border: 2px solid rgba(255, 140, 0, 0.6) !important;
            color: #E0E7E9 !important;
            border-radius: 25px !important;
            padding: 18px 25px !important;
            font-size: 17px !important;
            transition: all 0.4s ease !important;
            box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.4),
                        inset -2px -2px 5px rgba(255, 255, 255, 0.1);
            caret-color: white !important;
        }}

        /* Fix for red border and enhanced 3D/glow on focus */
        .stTextInput > div > div > input:focus,
        .stTextInput > div > div > input:focus-visible,
        .stTextInput > div > div > input:active {{
            border-color: rgba(255, 140, 0, 0.9) !important;
            box-shadow: 0 0 30px rgba(255, 140, 0, 0.8),
                        inset 2px 2px 8px rgba(0, 0, 0, 0.6),
                        inset -2px -2px 8px rgba(255, 255, 255, 0.15) !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: rgba(255, 255, 255, 0.4) !important;
        }}

        /* Button styling */
        .stButton > button {{
            background: linear-gradient(90deg, #FF8C00 0%, #DC6400 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 18px 35px !important;
            font-size: 17px !important;
            font-weight: 700 !important;
            letter-spacing: 1.2px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 5px 25px rgba(255, 140, 0, 0.5) !important;
            cursor: pointer;
        }}

        .stButton > button:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 30px rgba(255, 140, 0, 0.7) !important;
            filter: brightness(1.1);
        }}

        /* Scrollbar styling */
        .messages-area::-webkit-scrollbar {{
            width: 12px;
        }}

        .messages-area::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
        }}

        .messages-area::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, #FF8C00 0%, #DC6400 100%);
            border-radius: 10px;
            border: 2px solid rgba(0,0,0,0.1);
        }}

        /* Animation */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Logo styling - Fixed at top-left */
        .logo-container {{
            position: fixed;
            top: 25px;
            left: 25px;
            z-index: 1000;
            opacity: 0.95;
        }}

        /* Glow effect for logo */
        .logo-glow {{
            filter: drop-shadow(0 0 20px rgba(255, 140, 0, 0.8));
        }}

        /* Typing indicator for "..." */
        .message.bot-message .typing-dots {{
            display: inline-flex;
            align-items: center;
        }}

        .message.bot-message .typing-dots span {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #C0C8CA;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite ease-in-out;
        }}

        .message.bot-message .typing-dots span:nth-child(1) {{
            animation-delay: 0s;
        }}
        .message.bot-message .typing-dots span:nth-child(2) {{
            animation-delay: 0.2s;
        }}
        .message.bot-message .typing-dots span:nth-child(3) {{
            animation-delay: 0.4s;
        }}

        @keyframes typing {{
            0%, 80%, 100% {{
                transform: translateY(0);
                opacity: 0.6;
            }}
            40% {{
                transform: translateY(-5px);
                opacity: 1;
            }}
        }}
    </style>
""", unsafe_allow_html=True)

# Display logo if available
if logo_base64:
    st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" width="80" class="logo-glow">
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Header section
st.markdown(f"""
    <div class="chat-header">
        {'<img src="data:image/png;base64,' + header_image_base64 + '" class="header-image">' if header_image_base64 else '<h1 class="chat-title">AutoDiag AI - Car Expert</h1><p class="chat-subtitle">Engine • Transmission • Electrical • Diagnostics</p>'}
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