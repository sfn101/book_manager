from flask import Blueprint, jsonify, request
from database import get_db
from util import normalize_strings
import bcrypt

users_api = Blueprint('users_api', __name__, url_prefix='/api/users')

@users_api.route('/', methods=['GET'])
def get_users():
    """Fetch users from the database with their collection count."""
    try:
        search = request.args.get('search', '').strip()
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                where_clause = ""
                search_params = []
                if search:
                    where_clause = "WHERE u.username ILIKE %s OR u.email ILIKE %s"
                    search_term = f"%{search}%"
                    search_params = [search_term, search_term]
                
                query = f"""
                    SELECT 
                        u.id, 
                        u.username,
                        u.email,
                        u.created_at,
                        COUNT(c.id) AS collection_count
                    FROM users u
                    LEFT JOIN collections c ON u.id = c.user_id
                    {where_clause}
                    GROUP BY u.id
                    ORDER BY u.username;
                """
                
                cursor.execute(query, search_params)
                users = cursor.fetchall()
                
                return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_api.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Fetch a single user by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if user:
                    return jsonify(user)
                else:
                    return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_api.route('/', methods=['POST'])
def add_user():
    """Add a new user to the database."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user').strip().lower()
        if role not in ['admin', 'user']:
            role = 'user'

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        # Normalize strings
        username = normalize_strings(username)
        email = normalize_strings(email)
        
        # Hash the password using bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check if username or email already exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cursor.fetchone()
                if existing_user:
                    return jsonify({"error": "Username or email already exists"}), 409
                
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
                    (username, email, password_hash, role)
                )
                new_user_id = cursor.fetchone()["id"]
                return jsonify({"message": "User added successfully", "user_id": new_user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_api.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user."""
    try:
        data = request.get_json()
        username = normalize_strings(data.get('username')) if data.get('username') else None
        email = normalize_strings(data.get('email')) if data.get('email') else None
        password = data.get('password') if data.get('password') else None
        role = data.get('role', None)
        # Normalize and validate role if provided
        if role is not None:
            role = role.strip().lower()
            if role not in ('admin', 'user'):
                return jsonify({"error": "Invalid role. Allowed values are 'admin' or 'user'."}), 400

        # Hash password if provided using bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') if password else None

        if not username and not email and not password_hash and role is None:
            return jsonify({"error": "At least one field (username, email, password, or role) is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                update_fields = []
                update_values = []

                # Only allow hardcoded, safe field names
                if username is not None:
                    update_fields.append("username = %s")
                    update_values.append(username)
                if email is not None:
                    update_fields.append("email = %s")
                    update_values.append(email)
                if password_hash is not None:
                    update_fields.append("password_hash = %s")
                    update_values.append(password_hash)
                if role is not None:
                    update_fields.append("role = %s")
                    update_values.append(role)

                if not update_fields:
                    return jsonify({"error": "No valid fields to update"}), 400

                update_query = "UPDATE users SET " + ", ".join(update_fields) + " WHERE id = %s"
                cursor.execute(update_query, (*update_values, user_id))
                conn.commit()

                if cursor.rowcount == 0:
                    return jsonify({"error": "User not found"}), 404

                return jsonify({"message": "User updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_api.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "User not found"}), 404
                return jsonify({"message": "User deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
