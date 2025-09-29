from flask import Blueprint, jsonify, request
from database import get_db
from util import normalize_strings
from services.open_library_service import OpenLibraryService

categories_api = Blueprint('categories_api', __name__, url_prefix='/api/categories')

@categories_api.route('/', methods=['GET'])
def get_categories():
    """Fetch categories from the database with pagination."""
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
                    where_clause = "WHERE categories.name ILIKE %s"
                    search_params = [f"%{search}%"]
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM categories " + where_clause
                cursor.execute(count_query, search_params)
                total_count = cursor.fetchone()['count']
                
                # Get categories with pagination and book count
                categories_base_query = """
                    SELECT 
                        categories.id, 
                        categories.name,
                        COALESCE(book_counts.book_count, 0) as book_count
                    FROM categories
                    LEFT JOIN (
                        SELECT category_id, COUNT(*) as book_count
                        FROM book_categories
                        GROUP BY category_id
                    ) book_counts ON categories.id = book_counts.category_id
                """
                categories_query = categories_base_query + where_clause + """
                    ORDER BY categories.name
                    LIMIT %s OFFSET %s
                """
                
                cursor.execute(categories_query, search_params + [per_page, offset])
                categories = cursor.fetchall()
                
                # Calculate pagination info
                total_pages = (total_count + per_page - 1) // per_page
                
                return jsonify({
                    'data': categories,
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

@categories_api.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Fetch a single category by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
                category = cursor.fetchone()
                if category:
                    return jsonify(category)
                else:
                    return jsonify({"error": "Category not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @categories_api.route('/name/<string:category_name>', methods=['GET'])
# def get_category_by_name(category_name):
#     """Fetch a single category by its name."""
#     try:
#         with get_db() as conn:
#             with conn.cursor() as cursor:
#                 cursor.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(%s)", (category_name,))
#                 category = cursor.fetchone()
#                 if category:
#                     return jsonify(category)
#                 else:
#                     return jsonify({"error": "Category not found"}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@categories_api.route('/', methods=['POST'])
def add_category():
    """Add a new category to the database."""
    try:
        data = request.get_json()
        name = normalize_strings(data.get('name'))

        if not name:
            return jsonify({"error": "Category name is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (name,))
                new_category_id = cursor.fetchone()["id"]
                return jsonify({"message": "Category added", "category_id": new_category_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@categories_api.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update an existing category."""
    try:
        data = request.get_json()
        name = normalize_strings(data.get('name'))

        if not name:
            return jsonify({"error": "Category name is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE categories SET name = %s WHERE id = %s", (name, category_id))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Category not found"}), 404
                return jsonify({"message": "Category updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@categories_api.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Category not found"}), 404
                return jsonify({"message": "Category deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@categories_api.route('/<int:category_id>/books', methods=['GET'])
def get_books_by_category(category_id):
    """Fetch all books for a specific category."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT b.* 
                    FROM books b
                    JOIN book_categories bc ON b.id = bc.book_id
                    WHERE bc.category_id = %s
                """, (category_id,))
                books = cursor.fetchall()
                if books:
                    return jsonify(books)
                else:
                    return jsonify({"error": "No books found for this category"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500