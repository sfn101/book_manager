from flask import Blueprint, jsonify, request
from database import get_db
from util import normalize_strings
from routes.auth import can_edit_collection, is_admin

collections_api = Blueprint('collections_api', __name__, url_prefix='/api/collections')

@collections_api.route('/', methods=['GET'])
def get_collections():
    """Fetch all collections from the database."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM collections")
                collections = cursor.fetchall()
                return jsonify(collections)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@collections_api.route('/<int:collection_id>', methods=['GET'])
def get_collection(collection_id):
    """Fetch a single collection by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                if collection:
                    return jsonify(collection)
                else:
                    return jsonify({"error": "Collection not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@collections_api.route('/', methods=['POST'])
def add_collection():
    """Add a new collection to the database."""
    try:
        data = request.get_json()
        name = normalize_strings(data.get('name'))
        description = data.get('description')
        user_id = data.get('user_id')

        if not name or not user_id:
            return jsonify({"error": "Name and user_id are required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO collections (name, description, user_id) VALUES (%s, %s, %s) RETURNING id",
                    (name, description, user_id)
                )
                new_collection_id = cursor.fetchone()["id"]
                return jsonify({"message": "Collection added", "collection_id": new_collection_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@collections_api.route('/<int:collection_id>', methods=['PUT'])
def update_collection(collection_id):
    """Update an existing collection."""
    try:
        data = request.get_json()
        name = normalize_strings(data.get('name')) if data.get('name') else None
        description = data.get('description') if data.get('description') else None

        if not name and not description:
            return jsonify({"error": "At least one field (name or description) is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                update_fields = []
                update_values = []

                if name:
                    update_fields.append("name = %s")
                    update_values.append(name)
                if description:
                    update_fields.append("description = %s")
                    update_values.append(description)

                update_query = "UPDATE collections SET " + ", ".join(update_fields) + " WHERE id = %s"
                cursor.execute(update_query, (*update_values, collection_id))

                if cursor.rowcount == 0:
                    return jsonify({"error": "Collection not found"}), 404

                return jsonify({"message": "Collection updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@collections_api.route('/<int:collection_id>', methods=['DELETE'])
def delete_collection(collection_id):
    """Delete a collection by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM collections WHERE id = %s", (collection_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Collection not found"}), 404
                return jsonify({"message": "Collection deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@collections_api.route('/<int:collection_id>/books', methods=['GET'])
def get_books_in_collection(collection_id):
    """Fetch all books in a specific collection."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT b.id, b.title, b.publication_year, b.cover_id,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors
                    FROM books b
                    JOIN collection_books cb ON b.id = cb.book_id
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    WHERE cb.collection_id = %s
                    GROUP BY b.id, b.title, b.publication_year, b.cover_id
                    ORDER BY b.title
                """, (collection_id,))
                books = cursor.fetchall()
                return jsonify(books)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@collections_api.route('/<int:collection_id>/books/available', methods=['GET'])
def get_available_books_for_collection(collection_id: int):
    """Return books not in this collection, optionally filtered and paginated."""
    try:
        search = (request.args.get('search') or '').strip()
        offset = request.args.get('offset', default=0, type=int)
        limit = request.args.get('limit', default=20, type=int)

        with get_db() as conn:
            with conn.cursor() as cursor:
                # Ensure collection exists
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                if not collection:
                    return jsonify({"error": "Collection not found"}), 404

                # Base query for books not in collection
                params = [collection_id]
                where_extra = ""
                if search:
                    params.extend([f"%{search}%", f"%{search}%"]) 
                    where_extra = (
                        " AND (LOWER(b.title) LIKE LOWER(%s) OR EXISTS ("
                        " SELECT 1 FROM book_authors ba2 JOIN authors a2 ON ba2.author_id = a2.id"
                        " WHERE ba2.book_id = b.id AND LOWER(a2.name) LIKE LOWER(%s)))"
                    )

                query = (
                    "SELECT b.id, b.title, b.publication_year, b.cover_id,"
                    "       COALESCE(ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), ARRAY[]::text[]) as authors "
                    "FROM books b "
                    "LEFT JOIN book_authors ba ON b.id = ba.book_id "
                    "LEFT JOIN authors a ON ba.author_id = a.id "
                    "WHERE b.id NOT IN (SELECT book_id FROM collection_books WHERE collection_id = %s)"
                    + where_extra +
                    " GROUP BY b.id, b.title, b.publication_year, b.cover_id "
                    " ORDER BY b.title OFFSET %s LIMIT %s"
                )
                params.extend([offset, limit])

                cursor.execute(query, params)
                items = cursor.fetchall()

                # Determine if more items exist
                has_more = False
                if len(items) == limit:
                    cursor.execute(
                        query.replace("OFFSET %s LIMIT %s", "OFFSET %s LIMIT %s"),
                        params[:-2] + [offset + limit, 1],
                    )
                    more = cursor.fetchall()
                    has_more = len(more) > 0

                return jsonify({
                    "items": items,
                    "pagination": {"offset": offset, "limit": limit, "has_more": has_more}
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@collections_api.route('/<int:collection_id>/books/add', methods=['POST'])
def add_books_to_collection(collection_id):
    """Add books to a collection."""
    try:
        data = request.get_json()
        book_ids = data.get('book_ids', [])
        
        if not book_ids:
            return jsonify({"error": "No book IDs provided"}), 400
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Permission: owner or admin
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                if not collection:
                    return jsonify({"error": "Collection not found"}), 404
                if not (can_edit_collection(collection['user_id']) or is_admin()):
                    return jsonify({"error": "Permission denied"}), 403
                # Check if collection exists
                cursor.execute("SELECT id FROM collections WHERE id = %s", (collection_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Collection not found"}), 404
                
                # Add books to collection (ignore duplicates)
                for book_id in book_ids:
                    cursor.execute("""
                        INSERT INTO collection_books (collection_id, book_id)
                        VALUES (%s, %s)
                        ON CONFLICT (collection_id, book_id) DO NOTHING
                    """, (collection_id, book_id))
                
                return jsonify({"success": True, "message": f"Added {len(book_ids)} books to collection"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@collections_api.route('/<int:collection_id>/books', methods=['POST'])
def add_single_book_to_collection(collection_id: int):
    """Add a single book to a collection: body {"book_id": number}."""
    try:
        data = request.get_json() or {}
        book_id = data.get('book_id')
        if not book_id:
            return jsonify({"error": "book_id is required"}), 400

        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                if not collection:
                    return jsonify({"error": "Collection not found"}), 404
                if not (can_edit_collection(collection['user_id']) or is_admin()):
                    return jsonify({"error": "Permission denied"}), 403

                cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Book not found"}), 404

                cursor.execute(
                    """
                    INSERT INTO collection_books (collection_id, book_id)
                    VALUES (%s, %s)
                    ON CONFLICT (collection_id, book_id) DO NOTHING
                    """,
                    (collection_id, book_id),
                )
                return jsonify({"success": True, "message": "Book added to collection"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@collections_api.route('/<int:collection_id>/books/<int:book_id>/remove', methods=['DELETE'])
def remove_book_from_collection(collection_id, book_id):
    """Remove a book from a collection."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM collection_books 
                    WHERE collection_id = %s AND book_id = %s
                """, (collection_id, book_id))
                
                if cursor.rowcount == 0:
                    return jsonify({"error": "Book not found in collection"}), 404
                
                return jsonify({"success": True, "message": "Book removed from collection"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500