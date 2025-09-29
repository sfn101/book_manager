"""
Authentication Module
====================

This module handles user authentication and authorization for the Books Manager application.
It provides secure user registration, login, logout, and session management.

Key Features:
- Secure password hashing with bcrypt
- Session-based authentication
- Role-based access control (admin/user)
- User profile management
- Permission decorators for route protection

Security Features:
- bcrypt password hashing with salt
- Session security configuration
- Input validation and sanitization
- SQL injection prevention with parameterized queries

Author: Books Manager Team
Version: 1.0.0
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import get_db
from util import normalize_strings
import bcrypt

auth = Blueprint('auth', __name__)

# =============================================================================
# PASSWORD SECURITY FUNCTIONS
# =============================================================================

def hash_password(password):
    """
    Hash password using bcrypt with proper salt.
    
    Args:
        password (str): Plain text password to hash
        
    Returns:
        str: Hashed password string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """
    Verify password against bcrypt hash.
    
    Args:
        password (str): Plain text password to verify
        hashed_password (str): Stored hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')
        
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    # Find user by username or email
                    cursor.execute("""
                        SELECT id, username, email, password_hash, role 
                        FROM users 
                        WHERE username = %s OR email = %s
                    """, (username, username))
                    
                    user = cursor.fetchone()
                    
                    if user and verify_password(password, user['password_hash']):
                        # Login successful
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['email'] = user['email']
                        session['role'] = user['role']
                        
                        flash(f'Welcome back, {user["username"]}!', 'success')
                        
                        # Redirect to next page or home
                        next_page = request.args.get('next')
                        return redirect(next_page) if next_page else redirect(url_for('home'))
                    else:
                        flash('Invalid username/email or password', 'error')
        
        except Exception as e:
            flash('An error occurred during login', 'error')
    
    return render_template('auth/login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        
        # Validation
        if not username or not email or not password or not password_confirm:
            flash('All fields are required', 'error')
            return render_template('auth/signup.html')
        
        if '@' not in email:
            flash('Please enter a valid email address', 'error')
            return render_template('auth/signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/signup.html')
        
        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return render_template('auth/signup.html')
        
        try:
            # Normalize strings
            username = normalize_strings(username)
            email = normalize_strings(email)
            
            with get_db() as conn:
                with conn.cursor() as cursor:
                    # Check if username or email already exists
                    cursor.execute("""
                        SELECT id FROM users 
                        WHERE username = %s OR email = %s
                    """, (username, email))
                    
                    existing_user = cursor.fetchone()
                    
                    if existing_user:
                        flash('Username or email already exists', 'error')
                        return render_template('auth/signup.html')
                    
                    # Create new user (default role is 'user')
                    password_hash = hash_password(password)
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, role) 
                        VALUES (%s, %s, %s, %s) 
                        RETURNING id
                    """, (username, email, password_hash, 'user'))
                    
                    user_id = cursor.fetchone()['id']
                    
                    # Auto-login after successful registration
                    session['user_id'] = user_id
                    session['username'] = username
                    session['email'] = email
                    session['role'] = 'user'
                    
                    flash(f'Account created successfully! Welcome, {username}!', 'success')
                    return redirect(url_for('home'))
        
        except Exception as e:
            flash('An error occurred during registration', 'error')
    
    return render_template('auth/signup.html')

@auth.route('/logout')
def logout():
    """Handle user logout"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

@auth.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Get user info with optimized statistics
                cursor.execute("""
                    SELECT 
                        u.id, u.username, u.email, u.created_at, u.role,
                        COUNT(DISTINCT c.id) as collection_count,
                        COUNT(DISTINCT cb.book_id) as total_books_in_collections,
                        COUNT(DISTINCT cat.id) as unique_categories,
                        STRING_AGG(DISTINCT cat.name, ', ') as favorite_categories
                    FROM users u
                    LEFT JOIN collections c ON u.id = c.user_id
                    LEFT JOIN collection_books cb ON c.id = cb.collection_id
                    LEFT JOIN books b ON cb.book_id = b.id
                    LEFT JOIN book_categories bc ON b.id = bc.book_id
                    LEFT JOIN categories cat ON bc.category_id = cat.id
                    WHERE u.id = %s
                    GROUP BY u.id, u.username, u.email, u.created_at, u.role
                """, (session['user_id'],))
                
                user_info = cursor.fetchone()
                
                if not user_info:
                    flash('User not found', 'error')
                    return redirect(url_for('auth.logout'))
                
                return render_template('auth/profile.html', user=user_info)
    
    except Exception as e:
        flash('Error loading profile', 'error')
        return redirect(url_for('home'))

# Helper functions for template context
def login_required(f):
    """Decorator for routes that require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for routes that require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('role') != 'admin':
            flash('Admin access required for this page', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def is_admin():
    """Check if current user is admin"""
    return session.get('role') == 'admin'

def is_user_or_admin():
    """Check if user is logged in (either user or admin)"""
    return 'user_id' in session

def can_edit_collection(collection_user_id):
    """Check if current user can edit a specific collection"""
    if not is_logged_in():
        return False
    if is_admin():
        return True  # Admins can edit any collection
    return session.get('user_id') == collection_user_id  # Users can only edit their own collections

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def get_current_user():
    """Get current user info"""
    if is_logged_in():
        return {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'email': session.get('email'),
            'role': session.get('role', 'user')
        }
    return None