from flask import Blueprint, jsonify, request
from database import get_db
from util import normalize_strings
from services.open_library_service import OpenLibraryService
from models import handle_database_error, handle_validation_error, handle_not_found_error, handle_conflict_error

authors_api = Blueprint('authors_api', __name__, url_prefix='/api/authors')

@authors_api.route('/', methods=['GET'])
def get_authors():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        authors.id, 
                        authors.name, 
                        COUNT(books.id) as book_count,
                        COALESCE(
                            ARRAY_AGG(books.title) FILTER (WHERE books.title IS NOT NULL), 
                            ARRAY[]::text[]
                        ) as book_titles
                    FROM authors
                    LEFT JOIN book_authors ON authors.id = book_authors.author_id
                    LEFT JOIN books ON book_authors.book_id = books.id
                    GROUP BY authors.id, authors.name
                    ORDER BY authors.id;
                """)
                authors = cursor.fetchall()
                return jsonify(authors)
    except Exception as e:
        return handle_database_error(e, "fetching authors")

@authors_api.route('/', methods=['POST'])
def create_author():
    data = request.get_json()
    name = data.get('name', '').strip()
    image = data.get('image')
    
    # Handle image field properly - it can be None, empty string, or a valid URL
    if image is not None:
        image = image.strip()
        if not image:  # Empty string after stripping
            image = None
    
    if not name:
        return handle_validation_error('name is required')
    
    name = normalize_strings(name)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM authors WHERE LOWER(name) = LOWER(%s);", (name,))
                existing_author = cursor.fetchone()
                if existing_author:
                    return handle_conflict_error('Author with this name already exists', existing_author['id'])
                
                cursor.execute("INSERT INTO authors (name, image_url) VALUES (%s, %s) RETURNING id;", (name, image))
                new_id = cursor.fetchone()['id']
                return jsonify({'id': new_id, 'name': name, 'image_url': image, 'message': 'Author added successfully'}), 201
    except Exception as e:
        return handle_database_error(e, "adding new author")

@authors_api.route('/<int:author_id>', methods=['GET'])
def get_author(author_id):
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        authors.id, 
                        authors.name, 
                        COUNT(books.id) as book_count,
                        COALESCE(
                            ARRAY_AGG(books.title) FILTER (WHERE books.title IS NOT NULL), 
                            ARRAY[]::text[]
                        ) as book_titles
                    FROM authors
                    LEFT JOIN book_authors ON authors.id = book_authors.author_id
                    LEFT JOIN books ON book_authors.book_id = books.id
                    WHERE authors.id = %s
                    GROUP BY authors.id, authors.name;
                """, (author_id,))
                author = cursor.fetchone()
                if author:
                    return jsonify(author)
                else:
                    return handle_not_found_error("Author")
    except Exception as e:
        return handle_database_error(e, "fetching author by ID")

@authors_api.route('/search', methods=['GET'])
def search_authors():
    name = request.args.get('name', '')
    if not name:
        return handle_validation_error('Name parameter is required')
        
    name = normalize_strings(name)
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        authors.id, 
                        authors.name, 
                        COUNT(books.id) as book_count,
                        COALESCE(
                            ARRAY_AGG(books.title) FILTER (WHERE books.title IS NOT NULL), 
                            ARRAY[]::text[]
                        ) as book_titles
                    FROM authors
                    LEFT JOIN book_authors ON authors.id = book_authors.author_id
                    LEFT JOIN books ON book_authors.book_id = books.id
                    WHERE LOWER(authors.name) LIKE LOWER(%s)
                    GROUP BY authors.id, authors.name
                    ORDER BY authors.id;
                """, (f'%{name}%',))
                authors = cursor.fetchall()
                return jsonify(authors)
    except Exception as e:
        return handle_database_error(e, "searching authors")

@authors_api.route('/update/<int:author_id>', methods=['PUT'])
def update_author(author_id):
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not author_id or not name:
        return handle_validation_error('Both id and name are required')
    
    name = normalize_strings(name)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM authors WHERE id = %s;", (author_id,))
                existing_author = cursor.fetchone()
                if not existing_author:
                    return handle_not_found_error("Author")
                
                cursor.execute("SELECT id FROM authors WHERE LOWER(name) = LOWER(%s) AND id != %s;", (name, author_id))
                conflict_author = cursor.fetchone()
                if conflict_author:
                    return handle_conflict_error('Another author with this name already exists', conflict_author['id'])
                
                cursor.execute("UPDATE authors SET name = %s WHERE id = %s;", (name, author_id))
                return jsonify({'id': author_id, 'name': name, 'message': 'Author updated successfully'})
    except Exception as e:
        return handle_database_error(e, "updating author")

@authors_api.route('/add', methods=['POST'])
def add_author():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return handle_validation_error('name is required')
    
    name = normalize_strings(name)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM authors WHERE LOWER(name) = LOWER(%s);", (name,))
                existing_author = cursor.fetchone()
                if existing_author:
                    return handle_conflict_error('Author with this name already exists', existing_author['id'])
                
                cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id;", (name,))
                new_id = cursor.fetchone()['id']
                return jsonify({'id': new_id, 'name': name, 'message': 'Author added successfully'}), 201
    except Exception as e:
        return handle_database_error(e, "adding new author")

    
@authors_api.route('/delete/<int:author_id>', methods=['DELETE'])
def delete_author(author_id):
    if not author_id:
        return handle_validation_error('Author ID is required')
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM authors WHERE id = %s;", (author_id,))
                existing_author = cursor.fetchone()
                if not existing_author:
                    return handle_not_found_error("Author")
                
                cursor.execute("DELETE FROM book_authors WHERE author_id = %s;", (author_id,))
                cursor.execute("DELETE FROM authors WHERE id = %s;", (author_id,))
                return jsonify({'message': 'Author deleted successfully'})
    except Exception as e:
        return handle_database_error(e, "deleting author")
    
@authors_api.route('/add_book', methods=['POST'])
def add_book_to_author():
    data = request.get_json()
    author_id = data.get('author_id')
    book_id = data.get('book_id')

    if not author_id or not book_id:
        return handle_validation_error('Both author_id and book_id are required')

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM authors WHERE id = %s;", (author_id,))
                existing_author = cursor.fetchone()
                if not existing_author:
                    return handle_not_found_error("Author")

                cursor.execute("SELECT id FROM books WHERE id = %s;", (book_id,))
                existing_book = cursor.fetchone()
                if not existing_book:
                    return handle_not_found_error("Book")

                cursor.execute("INSERT INTO book_authors (author_id, book_id) VALUES (%s, %s);", (author_id, book_id))
                return jsonify({'message': 'Book added to author successfully'}), 201
    except Exception as e:
        return handle_database_error(e, "adding book to author")

@authors_api.route('/remove_book', methods=['POST'])
def remove_book_from_author():
    data = request.get_json()
    author_id = data.get('author_id')
    book_id = data.get('book_id')

    if not author_id or not book_id:
        return handle_validation_error('Both author_id and book_id are required')

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM authors WHERE id = %s;", (author_id,))
                existing_author = cursor.fetchone()
                if not existing_author:
                    return handle_not_found_error("Author")

                cursor.execute("SELECT id FROM books WHERE id = %s;", (book_id,))
                existing_book = cursor.fetchone()
                if not existing_book:
                    return handle_not_found_error("Book")

                cursor.execute("DELETE FROM book_authors WHERE author_id = %s AND book_id = %s;", (author_id, book_id))
                return jsonify({'message': 'Book removed from author successfully'}), 200
    except Exception as e:
        return handle_database_error(e, "removing book from author")
