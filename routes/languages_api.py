from flask import Blueprint, jsonify, request
from database import get_db
from util import normalize_strings

languages_api = Blueprint('languages_api', __name__, url_prefix='/api/languages')

@languages_api.route('/', methods=['GET'])
def get_languages():
    """Fetch languages from the database with pagination."""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Build WHERE clause for search
                where_clause = ""
                search_params = []
                if search:
                    where_clause = "WHERE languages.name ILIKE %s"
                    search_params = [f"%{search}%"]
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM languages " + where_clause
                cursor.execute(count_query, search_params)
                total_count = cursor.fetchone()['count']
                
                # Get languages with pagination and book count
                languages_base_query = """
                    SELECT 
                        languages.id, 
                        languages.name,
                        COALESCE(book_counts.book_count, 0) as book_count
                    FROM languages
                    LEFT JOIN (
                        SELECT language_id, COUNT(*) as book_count
                        FROM book_languages
                        GROUP BY language_id
                    ) book_counts ON languages.id = book_counts.language_id
                """
                languages_query = languages_base_query + where_clause + """
                    ORDER BY languages.name
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(languages_query, search_params + [per_page, offset])
                languages = cursor.fetchall()
                
                # Calculate pagination info
                total_pages = (total_count + per_page - 1) // per_page
                
                return jsonify({
                    'data': languages,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total_count,
                        'pages': total_pages,
                        'has_prev': page > 1,
                        'has_next': page < total_pages
                    }
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@languages_api.route('/<int:language_id>', methods=['GET'])
def get_language(language_id):
    """Fetch a single language by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM languages WHERE id = %s", (language_id,))
                language = cursor.fetchone()
                if language:
                    return jsonify(language)
                else:
                    return jsonify({"error": "Language not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@languages_api.route('/', methods=['POST'])
def add_language():
    """Add a new language to the database."""
    try:
        data = request.get_json()
        name = normalize_strings(data.get('name'))

        if not name:
            return jsonify({"error": "Language name is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO languages (name) VALUES (%s) RETURNING id", (name,))
                new_language_id = cursor.fetchone()["id"]
                return jsonify({"message": "Language added", "language_id": new_language_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@languages_api.route('/<int:language_id>', methods=['PUT'])
def update_language(language_id):
    """Update an existing language."""
    try:
        data = request.get_json()
        name = normalize_strings(data.get('name'))

        if not name:
            return jsonify({"error": "Language name is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE languages SET name = %s WHERE id = %s", (name, language_id))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Language not found"}), 404
                return jsonify({"message": "Language updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@languages_api.route('/<int:language_id>', methods=['DELETE'])
def delete_language(language_id):
    """Delete a language by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM languages WHERE id = %s", (language_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Language not found"}), 404
                return jsonify({"message": "Language deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
