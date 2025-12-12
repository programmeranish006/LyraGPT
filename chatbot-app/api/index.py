from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import google.generativeai as genai
import pytz

# Load environment variables
load_dotenv()

# Configure Flask
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# MongoDB Setup
MONGO_URI = os.environ.get('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['chatbot_db']
users_collection = db['users']
conversations_collection = db['conversations']

# Configure Google Gemini with LATEST models
try:
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
    
    # Try Gemini 2.5 Flash first (latest and best)
    try:
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini AI Model Loaded: gemini-2.5-flash (LATEST)")
    except:
        # Fallback to Gemini 2.0 Flash if 2.5 not available
        try:
            gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Gemini AI Model Loaded: gemini-2.0-flash-exp")
        except:
            # Final fallback to stable version
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini AI Model Loaded: gemini-1.5-flash (STABLE)")
            
except Exception as e:
    print(f"⚠️ Gemini initialization error: {e}")
    gemini_model = None

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# SocketIO Setup
socketio = SocketIO(app, cors_allowed_origins="*")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Register blueprints
from auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('auth.login'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=current_user)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_message():
    data = request.json
    message = data.get('message')
    
    # Get conversation history for context
    history = list(conversations_collection.find(
        {'user_id': current_user.id}
    ).sort('timestamp', -1).limit(10))
    
    # Get AI response using Gemini
    bot_response = get_gemini_response(message, history)
    
    # Save messages to database
    conversations_collection.insert_one({
        'user_id': current_user.id,
        'role': 'user',
        'content': message,
        'timestamp': datetime.now()
    })
    
    conversations_collection.insert_one({
        'user_id': current_user.id,
        'role': 'assistant',
        'content': bot_response,
        'timestamp': datetime.now()
    })
    
    return jsonify({
        'response': bot_response,
        'timestamp': datetime.now().isoformat()
    })

def get_gemini_response(message, history):
    """Get intelligent AI response from Google Gemini 2.5 Flash"""
    
    # Check if Gemini is available
    if not gemini_model:
        return get_smart_fallback(message)
    
    try:
        # Build conversation context
        context = build_conversation_context(history)
        
        # Get current time for time-aware responses
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        time_info = f"Current date and time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p IST')}"
        
        # Create comprehensive system instruction
        system_instruction = f"""You are "AI Companion", a helpful, intelligent, and friendly AI assistant powered by Google Gemini 2.5 Flash.

{time_info}

Your capabilities:
- Answer questions with accurate, up-to-date information
- Explain complex topics in simple terms
- Create content (notes, summaries, essays, code, etc.)
- Solve problems and provide solutions
- Have natural, engaging conversations
- Remember context from our conversation

Guidelines:
- Be conversational, warm, and encouraging
- Provide accurate information; if unsure, say so
- For simple questions: 2-4 sentences
- For complex topics: detailed, structured responses with examples
- Use markdown formatting (bold, lists, code blocks) when helpful
- If asked about current time/date, use the information above
- Be creative and helpful

{context}"""
        
        # Build full prompt
        full_prompt = f"{system_instruction}\n\nUser: {message}\n\nAssistant:"
        
        # Generate response with Gemini 2.5 Flash
        print(f"🤖 Gemini 2.5 Flash generating response for: '{message[:60]}...'")
        
        response = gemini_model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
                candidate_count=1,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )
        
        bot_response = response.text.strip()
        print(f"✅ Gemini responded ({len(bot_response)} chars): {bot_response[:80]}...")
        
        return bot_response
        
    except Exception as e:
        print(f"❌ Gemini AI Error: {str(e)}")
        # Fallback to smart responses
        return get_smart_fallback(message)

def build_conversation_context(history):
    """Build context from conversation history"""
    if not history or len(history) == 0:
        return ""
    
    context = "Conversation history:\n"
    for msg in reversed(list(history)[:8]):  # Last 8 messages for better context
        role = "User" if msg['role'] == 'user' else "Assistant"
        content = msg['content'][:250]  # Limit length
        context += f"{role}: {content}\n"
    
    return context + "\n"

def get_smart_fallback(message):
    """Smart fallback responses when Gemini fails"""
    message_lower = message.lower()
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    hour = current_time.hour
    
    # Time-based greeting
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    # Time questions
    if any(word in message_lower for word in ['time', 'what time', "what's the time", 'clock']):
        return f"The current time is **{current_time.strftime('%I:%M %p')}** IST on {current_time.strftime('%B %d, %Y')} ({current_time.strftime('%A')}). How else can I help you?"
    
    # Date questions
    if any(word in message_lower for word in ['date', 'what date', 'today', "what's today", 'day']):
        return f"Today is **{current_time.strftime('%A, %B %d, %Y')}**. What would you like to know?"
    
    # Greetings
    if any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good evening', 'good afternoon', 'sup', 'yo']):
        return f"{greeting}! I'm your AI Companion powered by Google Gemini 2.5 Flash. I can help you with:\n\n• Answering questions\n• Explaining concepts\n• Creating content\n• Having conversations\n• Problem-solving\n\nWhat would you like to explore?"
    
    # Identity
    if any(phrase in message_lower for phrase in ['who are you', 'what are you', 'your name', "what's your name"]):
        return "I'm **AI Companion, powered by Google's latest **Gemini 2.5 Flash model! I can:\n\n✨ Answer your questions with accurate information\n💡 Explain complex topics simply\n📝 Create content (notes, essays, code)\n🎯 Help solve problems\n💬 Have natural conversations\n\nWhat can I help you with today?"
    
    # Capabilities
    if any(phrase in message_lower for phrase in ['what can you do', 'help me', 'capabilities', 'features']):
        return """I'm powered by Google Gemini 2.5 Flash and can help you with:

**📚 Knowledge & Learning:**
• Answer factual questions
• Explain complex concepts
• Provide information on any topic

**✍️ Content Creation:**
• Write essays, notes, summaries
• Generate code in multiple languages
• Create lists, outlines, plans

**🧮 Problem Solving:**
• Math calculations
• Logic problems
• Step-by-step solutions

**💬 Conversation:**
• Natural dialogue
• Context awareness
• Creative discussions

What would you like to try?"""
    
    # Math calculations
    if any(char in message for char in ['+', '-', '*', '/', '=']):
        try:
            import re
            expr = re.sub(r'[^0-9+\-*/().]', '', message)
            if expr and len(expr) > 1:
                result = eval(expr)
                return f"Calculation Result: {result} 🎯\n\nNeed any other calculations or math help?"
        except:
            pass
        return "I can help with math! Try:\n• 'What is 25 × 48?'\n• 'Calculate 156 ÷ 12'\n• '(5 + 3) × 2'\n\n🧮"
    
    # Thank you
    if any(word in message_lower for word in ['thank', 'thanks', 'thx', 'ty', 'appreciate']):
        import random
        responses = [
            "You're very welcome! Anything else I can help with? 😊",
            "Happy to help! Feel free to ask me anything else!",
            "My pleasure! What else would you like to know?",
            "Anytime! I'm here whenever you need assistance! 🎉"
        ]
        return random.choice(responses)
    
    # Goodbye
    if any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'good night', 'gtg', 'gotta go']):
        import random
        responses = [
            "Goodbye! It was great chatting with you. Come back anytime! 👋😊",
            "See you later! Feel free to return whenever you need help! 🌟",
            "Take care! I'll be here when you need me! 💫",
            "Bye! Have a wonderful day/night! Come back soon! 🎊"
        ]
        return random.choice(responses)
    
    # Questions ending with ?
    if message.strip().endswith('?'):
        return f"Great question! You asked: \"{message}\"**\n\nI'm powered by Gemini 2.5 Flash and I'd love to help answer this! Could you provide a bit more context or rephrase it? I can assist with topics like:\n• General knowledge\n• Explanations\n• How-to guides\n• Problem-solving\n• And much more!"
    
    # Default intelligent response
    return f"I hear you: \"{message}\"**\n\nI'm your AI Companion powered by Gemini 2.5 Flash! I can help with:\n\n🔍 Answering questions\n💡 Explaining topics\n📝 Creating content\n🧮 Calculations\n💬 Conversations\n\nWhat specific help do you need? Feel free to ask anything!"

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    messages = list(conversations_collection.find(
        {'user_id': current_user.id}
    ).sort('timestamp', 1).limit(50))
    
    for msg in messages:
        msg['_id'] = str(msg['_id'])
    
    return jsonify({'messages': messages})

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        users_collection.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {'is_online': True}}
        )
        join_room(current_user.id)
        emit('user_online', {
            'user_id': current_user.id,
            'username': current_user.username
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        users_collection.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {
                'is_online': False,
                'last_seen': datetime.now()
            }}
        )
        emit('user_offline', {
            'user_id': current_user.id,
            'last_seen': datetime.now().isoformat()
        }, broadcast=True)

@socketio.on('typing_start')
def handle_typing_start():
    if current_user.is_authenticated:
        emit('bot_typing', {'typing': True}, room=current_user.id)

@socketio.on('typing_stop')
def handle_typing_stop():
    if current_user.is_authenticated:
        emit('bot_typing', {'typing': False}, room=current_user.id)


if __name__ == '__main__':
    
    print("🚀 Starting AI Chatbot locally...")
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    
    app.debug = False


app = app