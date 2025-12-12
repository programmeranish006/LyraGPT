from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        # Import here to avoid circular imports
        from index import users_collection
        from models import User
        
        # Validation
        if not email or not username or not password:
            return jsonify({'error': 'All fields required'}), 400
        
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 400
        
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create user
        user_data = {
            'email': email,
            'username': username,
            'password': generate_password_hash(password),
            'created_at': datetime.now(),
            'is_online': False,
            'last_seen': datetime.now(),
            'is_typing': False
        }
        
        result = users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        user = User(user_data)
        login_user(user)
        
        return jsonify({
            'success': True,
            'redirect': url_for('chat')
        })
    
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        # Import here to avoid circular imports
        from index import users_collection
        from models import User
        
        user_data = users_collection.find_one({'email': email})
        
        if not user_data:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user = User(user_data)
        
        if not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Update online status
        users_collection.update_one(
            {'_id': user_data['_id']},
            {'$set': {'is_online': True, 'last_seen': datetime.now()}}
        )
        
        login_user(user, remember=remember)
        
        return jsonify({
            'success': True,
            'redirect': url_for('chat')
        })
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    from index import users_collection
    
    # Update offline status
    users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'is_online': False, 'last_seen': datetime.now()}}
    )
    
    logout_user()
    return redirect(url_for('auth.login'))
