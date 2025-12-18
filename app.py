from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '421200909892a61e9e71893b57e3bf201a61d4099de0d4d449fa016fb9e43cc3')

# File paths for JSON data storage
IDEAS_FILE = 'ideas.json'
USERS_FILE = 'users.json'
CHATS_FILE = 'chats.json'

# Initialize JSON files if they don't exist
def init_files():
    if not os.path.exists(IDEAS_FILE):
        with open(IDEAS_FILE, 'w') as f:
            json.dump({"ideas": []}, f, indent=2)
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": []}, f, indent=2)
    
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'w') as f:
            json.dump({"chats": {}}, f, indent=2)

init_files()

# Helper functions to read/write JSON files
def read_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Raw content from {filename}: {content[:200]}...")  # Debug print
            data = json.loads(content)
            print(f"Parsed data from {filename}: {data}")  # Debug print
            return data
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {"ideas": []} if filename == IDEAS_FILE else {"users": []} if filename == USERS_FILE else {"chats": {}}

def write_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing {filename}: {e}")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Login page"""
    if 'user_email' in session:
        return redirect(url_for('explore'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle Firebase Google Authentication"""
    try:
        data = request.json
        email = data.get('email')
        uid = data.get('uid')
        display_name = data.get('displayName')
        photo_url = data.get('photoURL')
        
        if not email or not uid:
            return jsonify({"success": False, "message": "Email and UID are required"}), 400
        
        # Store user in session
        session['user_email'] = email
        session['user_uid'] = uid
        session['display_name'] = display_name or email.split('@')[0]
        session['photo_url'] = photo_url
        
        # Add or update user in users.json
        users_data = read_json(USERS_FILE)
        existing_user = next((u for u in users_data['users'] if u['email'] == email), None)
        
        if existing_user:
            # Update last login
            existing_user['last_login'] = datetime.now().isoformat()
            existing_user['display_name'] = display_name
            existing_user['photo_url'] = photo_url
        else:
            # Add new user
            users_data['users'].append({
                "uid": uid,
                "email": email,
                "display_name": display_name,
                "photo_url": photo_url,
                "joined_date": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat()
            })
        
        write_json(USERS_FILE, users_data)
        
        return jsonify({"success": True, "redirect": "/explore"})
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/explore')
@login_required
def explore():
    """Explore page - displays all project ideas"""
    return render_template('explore.html', 
                         user_email=session.get('user_email'),
                         display_name=session.get('display_name'),
                         photo_url=session.get('photo_url'))

@app.route('/api/ideas')
@login_required
def get_ideas():
    """Get all project ideas from ideas.json"""
    try:
        print("=== GET IDEAS ENDPOINT CALLED ===")
        ideas_data = read_json(IDEAS_FILE)
        print(f"Ideas data retrieved: {ideas_data}")
        print(f"Number of ideas: {len(ideas_data.get('ideas', []))}")
        return jsonify({"success": True, "ideas": ideas_data.get('ideas', [])})
    except Exception as e:
        print(f"Error getting ideas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/like', methods=['POST'])
@login_required
def toggle_like():
    """Toggle like on a project idea"""
    try:
        data = request.json
        idea_id = data.get('idea_id')
        user_email = session['user_email']
        
        ideas_data = read_json(IDEAS_FILE)
        
        # Find the idea
        idea = next((i for i in ideas_data['ideas'] if i['id'] == idea_id), None)
        if not idea:
            return jsonify({"success": False, "message": "Idea not found"}), 404
        
        # Initialize liked_by if not exists
        if 'liked_by' not in idea:
            idea['liked_by'] = []
        if 'likes' not in idea:
            idea['likes'] = 0
        
        # Toggle like
        if user_email in idea['liked_by']:
            idea['liked_by'].remove(user_email)
            idea['likes'] = max(0, idea['likes'] - 1)
            liked = False
        else:
            idea['liked_by'].append(user_email)
            idea['likes'] += 1
            liked = True
        
        write_json(IDEAS_FILE, ideas_data)
        
        return jsonify({
            "success": True,
            "liked": liked,
            "likes": idea['likes']
        })
    
    except Exception as e:
        print(f"Error toggling like: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/chat/<int:idea_id>')
@login_required
def chat(idea_id):
    """Chat page for AI assistant"""
    try:
        # Get the idea details from ideas.json
        ideas_data = read_json(IDEAS_FILE)
        idea = next((i for i in ideas_data['ideas'] if i['id'] == idea_id), None)
        
        if not idea:
            return redirect(url_for('explore'))
        
        return render_template('chat.html', 
                             idea=idea, 
                             user_email=session.get('user_email'),
                             display_name=session.get('display_name'),
                             photo_url=session.get('photo_url'))
    
    except Exception as e:
        print(f"Error loading chat: {e}")
        return redirect(url_for('explore'))

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_message():
    """Handle chat messages with AI assistant"""
    try:
        data = request.json
        idea_id = data.get('idea_id')
        message = data.get('message')
        user_email = session['user_email']
        
        if not message or not idea_id:
            return jsonify({"success": False, "message": "Message and idea_id are required"}), 400
        
        # Load chats
        chats_data = read_json(CHATS_FILE)
        chat_key = f"{user_email}_{idea_id}"
        
        if chat_key not in chats_data['chats']:
            chats_data['chats'][chat_key] = []
        
        # Add user message to history
        chats_data['chats'][chat_key].append({
            "role": "user",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate AI response
        ai_response = generate_ai_response(message, idea_id)
        
        # Add AI response to history
        chats_data['chats'][chat_key].append({
            "role": "assistant",
            "message": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        write_json(CHATS_FILE, chats_data)
        
        return jsonify({
            "success": True,
            "response": ai_response
        })
    
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/chat/history/<int:idea_id>')
@login_required
def get_chat_history(idea_id):
    """Get chat history for a specific idea"""
    try:
        user_email = session['user_email']
        chats_data = read_json(CHATS_FILE)
        chat_key = f"{user_email}_{idea_id}"
        
        history = chats_data['chats'].get(chat_key, [])
        
        return jsonify({
            "success": True,
            "history": history
        })
    
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

def generate_ai_response(message, idea_id):
    """Generate AI response based on message content"""
    message_lower = message.lower()
    
    # Check if user is asking for code
    code_keywords = ['code', 'source code', 'implementation', 'write', 'program', 'script', 'function', 'class']
    if any(keyword in message_lower for keyword in code_keywords):
        return ("I appreciate your interest, but I'm designed to guide you through understanding the project architecture "
                "rather than providing source code. I can help you understand:\n\n"
                "• Project folder structure\n"
                "• System architecture and design patterns\n"
                "• Module responsibilities\n"
                "• Relevant interview/viva questions\n\n"
                "What specific aspect would you like to explore?")
    
    # Get the idea details from ideas.json
    ideas_data = read_json(IDEAS_FILE)
    idea = next((i for i in ideas_data['ideas'] if i['id'] == idea_id), None)
    
    if not idea:
        return "Sorry, I couldn't find the project details. Please try again."
    
    # Respond based on keywords
    if 'folder' in message_lower or 'structure' in message_lower:
        return (f"For the {idea['summary']}, here's a recommended folder structure:\n\n"
                f"```\n"
                f"project/\n"
                f"├── backend/\n"
                f"│   ├── models/          # Data models\n"
                f"│   ├── controllers/     # Business logic\n"
                f"│   ├── routes/          # API endpoints\n"
                f"│   ├── middleware/      # Auth, validation\n"
                f"│   └── config/          # Configuration files\n"
                f"├── frontend/\n"
                f"│   ├── components/      # Reusable UI components\n"
                f"│   ├── pages/           # Main pages\n"
                f"│   ├── services/        # API calls\n"
                f"│   └── assets/          # Images, styles\n"
                f"├── tests/               # Unit and integration tests\n"
                f"└── docs/                # Documentation\n"
                f"```")
    
    elif 'architecture' in message_lower or 'design' in message_lower:
        return (f"The architecture for this project follows a layered approach:\n\n"
                f"**1. Presentation Layer:** User interface and user experience\n"
                f"**2. Application Layer:** Business logic and workflows\n"
                f"**3. Data Layer:** Database and data management\n\n"
                f"Key architectural patterns to consider:\n"
                f"• MVC (Model-View-Controller) for organization\n"
                f"• RESTful API design for backend communication\n"
                f"• Component-based architecture for frontend\n"
                f"• Service-oriented design for modularity")
    
    elif 'module' in message_lower or 'responsibility' in message_lower or 'responsibilities' in message_lower:
        return (f"Here are the main modules and their responsibilities:\n\n"
                f"**Authentication Module:**\n"
                f"• User registration and login\n"
                f"• Session management\n"
                f"• Password encryption\n\n"
                f"**Core Business Logic Module:**\n"
                f"• Main feature implementation\n"
                f"• Data processing and validation\n"
                f"• Business rules enforcement\n\n"
                f"**Database Module:**\n"
                f"• CRUD operations\n"
                f"• Data integrity\n"
                f"• Query optimization\n\n"
                f"**API Module:**\n"
                f"• Request handling\n"
                f"• Response formatting\n"
                f"• Error handling")
    
    elif 'interview' in message_lower or 'viva' in message_lower or 'question' in message_lower:
        tech_stack_first = idea.get('tech_stack', '').split(',')[0].strip() if idea.get('tech_stack') else 'your chosen technology'
        return (f"Common interview/viva questions for this project:\n\n"
                f"**Technical Questions:**\n"
                f"1. Why did you choose {tech_stack_first} for this project?\n"
                f"2. How does your system handle concurrent users?\n"
                f"3. What security measures have you implemented?\n"
                f"4. How do you ensure data consistency?\n"
                f"5. What are the scalability considerations?\n\n"
                f"**Design Questions:**\n"
                f"1. Why did you choose this particular architecture?\n"
                f"2. What trade-offs did you make in your design?\n"
                f"3. How would you handle future feature additions?\n\n"
                f"**Problem-Solving Questions:**\n"
                f"1. What challenges did you face during development?\n"
                f"2. How did you debug and test your application?\n"
                f"3. What would you improve if you had more time?")
    
    else:
        return (f"I'm here to help you understand the project: {idea['summary']}\n\n"
                f"I can assist you with:\n\n"
                f"• **Folder Structure:** Understanding how to organize your project files\n"
                f"• **Architecture:** System design and design patterns\n"
                f"• **Module Responsibilities:** What each component should do\n"
                f"• **Interview Questions:** Preparing for your viva/presentation\n\n"
                f"What would you like to know more about?")

if __name__ == '__main__':
    app.run(debug=True, port=5005)