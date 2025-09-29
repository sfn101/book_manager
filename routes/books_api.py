from flask import Blueprint, jsonify, request
from database import get_db
from database.data_access import get_books_data, get_book_by_id
from util import normalize_strings
from services.open_library_service import OpenLibraryService

books_api = Blueprint('books_api', __name__, url_prefix='/api/books')

@books_api.route('/', methods=['GET'])
def get_books():
    """Fetch all books from the database."""
    try:
        books = get_books_data()
        return jsonify(books)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@books_api.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    try:
        book = get_book_by_id(book_id)
        if book:
            return jsonify(book)
        else:
            return jsonify({"error": "Book not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@books_api.route('/title/<string:book_title>', methods=['GET'])
def get_book_by_title(book_title):
    """Fetch books by title with minimum word length filtering."""
    try:
        if not book_title:
            return jsonify({"error": "Invalid book title"}), 400
        
        book_title = normalize_strings(book_title)
        
        # Split into words and filter out single characters
        words = [word for word in book_title.split() if len(word) > 1]
        
        if not words:
            return jsonify({"error": "Search term must contain words with more than 1 character"}), 400
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Build dynamic query for multiple words
                conditions = []
                params = []
                
                for word in words:
                    conditions.append("LOWER(title) LIKE %s")
                    params.append(f"%{word}%")
                
                # Join conditions with AND (all words must be present)
                query = """SELECT 
                               books.id,
                               books.title,
                               books.publication_year,
                               books.open_library_id,
                               books.cover_id,
                               languages.name AS language,
                               authors.name
                               FROM books
                               JOIN book_languages ON books.id = book_languages.book_id
                               JOIN languages ON book_languages.language_id = languages.id
                               LEFT JOIN book_authors ON books.id = book_authors.book_id
                               LEFT JOIN authors ON book_authors.author_id = authors.id WHERE """ + " AND ".join(conditions)
                cursor.execute(query, params)
                
                books = cursor.fetchall()
                if books:
                    return jsonify(books)
                else:
                    return jsonify({"error": "No books found matching the search criteria"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@books_api.route('/', methods=['POST'])
def add_book():
    """Add a new book to the database."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid or missing JSON body"}), 400

        title = normalize_strings(data.get('title'))
        
        # Handle both singular and plural keys for authors
        authors = data.get('authors', data.get('author', []))
        if isinstance(authors, str):
            authors = [authors]
        authors = [normalize_strings(author) for author in authors if author]
        
        # Handle both singular and plural keys for languages
        languages = data.get('languages', data.get('language', []))
        if isinstance(languages, str):
            languages = [languages]
        languages = [normalize_strings(lang) for lang in languages if lang]
        
        # Handle both singular and plural keys for categories
        categories = data.get('categories', data.get('category', []))
        if isinstance(categories, str):
            categories = [categories]
        categories = [normalize_strings(cat) for cat in categories if cat]
        
        open_library_id = data.get('open_library_id')
        publication_year = data.get('publication_year')
        cover_id = data.get('cover_id')

        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check if book exists
                cursor.execute("SELECT * FROM books WHERE LOWER(REGEXP_REPLACE(title, '\\s+', ' ', 'g')) = %s", (normalize_strings(title),))
                existing_book = cursor.fetchone()
                if existing_book:
                    return jsonify({"error": "Book with this title already exists"}), 409
                
                # Insert book
                cursor.execute(
                    "INSERT INTO books (title, publication_year, open_library_id, cover_id) VALUES (%s, %s, %s, %s) RETURNING id",
                    (title, publication_year, open_library_id, cover_id)
                )
                new_book_id = cursor.fetchone()["id"]
                
                # Handle languages - insert each language as a separate record
                for language in languages:
                    if language:  # Only process non-empty languages
                        # Check if language exists
                        cursor.execute("SELECT id FROM languages WHERE LOWER(name) = %s", (language.lower(),))
                        language_result = cursor.fetchone()
                        if language_result:
                            language_id = language_result["id"]
                        else:
                            # Insert new language
                            cursor.execute("INSERT INTO languages (name) VALUES (%s) RETURNING id", (language,))
                            language_id = cursor.fetchone()["id"]
                        
                        # Link book to language via junction table
                        cursor.execute("INSERT INTO book_languages (book_id, language_id) VALUES (%s, %s)", (new_book_id, language_id))
                
                # Handle categories - insert each category as a separate record
                for category in categories:
                    if category:  # Only process non-empty categories
                        # Check if category exists
                        cursor.execute("SELECT id FROM categories WHERE LOWER(name) = %s", (category.lower(),))
                        category_result = cursor.fetchone()
                        if category_result:
                            category_id = category_result["id"]
                        else:
                            # Insert new category
                            cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (category,))
                            category_id = cursor.fetchone()["id"]
                        
                        # Link book to category via junction table
                        cursor.execute("INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)", (new_book_id, category_id))
                
                # Handle authors - insert each author as a separate record
                for author in authors:
                    if author:  # Only process non-empty authors
                        # Check if author exists
                        cursor.execute("SELECT id FROM authors WHERE LOWER(name) = %s", (author.lower(),))
                        author_result = cursor.fetchone()
                        if author_result:
                            author_id = author_result["id"]
                        else:
                            # Insert new author
                            cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id", (author,))
                            author_id = cursor.fetchone()["id"]

                        # Link book to author via junction table
                        cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)", (new_book_id, author_id))

                return jsonify({"message": "Book added successfully", "book_id": new_book_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@books_api.route('/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book by its ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
                if cursor.rowcount == 0:
                    return jsonify({"error": "Book not found"}), 404
                return jsonify({"message": "Book deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@books_api.route('/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update a book's details."""
    try:
        data = request.get_json()
        title = normalize_strings(data.get('title')) if data.get('title') else None
        
        # Handle both singular author and plural authors
        authors = data.get('authors', [])
        if not authors and data.get('author'):
            authors = [data.get('author')]
        authors = [normalize_strings(auth) for auth in authors if auth]
        
        # Handle both singular and plural keys for languages
        languages = data.get('languages', data.get('language', []))
        if isinstance(languages, str):
            languages = [languages]
        languages = [normalize_strings(lang) for lang in languages if lang]
        
        # Handle both singular and plural keys for categories
        categories = data.get('categories', data.get('category', []))
        if isinstance(categories, str):
            categories = [categories]
        categories = [normalize_strings(cat) for cat in categories if cat]
        
        open_library_id = data.get('open_library_id')
        publication_year = data.get('publication_year')
        cover_id = data.get('cover_id')
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
                existing_book = cursor.fetchone()
                if not existing_book:
                    return jsonify({"error": "Book not found"}), 404
                
                update_fields = []
                update_values = []
                if title:
                    # Check if another book (not this one) has the same title
                    cursor.execute("SELECT * FROM books WHERE LOWER(REGEXP_REPLACE(title, '\\s+', ' ', 'g')) = %s AND id != %s", (normalize_strings(title), book_id))
                    title_conflict = cursor.fetchone()
                    if title_conflict:
                        return jsonify({"error": "Another book with this title already exists"}), 409
                    update_fields.append("title = %s")
                    update_values.append(title)
                if publication_year is not None:
                    update_fields.append("publication_year = %s")
                    update_values.append(publication_year)
                if cover_id is not None:
                    update_fields.append("cover_id = %s")
                    update_values.append(cover_id)
                if open_library_id is not None:
                    update_fields.append("open_library_id = %s")
                    update_values.append(open_library_id)
                
                # Handle languages update - remove old and add new
                if languages:
                    cursor.execute("DELETE FROM book_languages WHERE book_id = %s", (book_id,))
                    for language in languages:
                        if language:
                            cursor.execute("SELECT id FROM languages WHERE LOWER(name) = %s", (language.lower(),))
                            language_result = cursor.fetchone()
                            if language_result:
                                language_id = language_result["id"]
                            else:
                                cursor.execute("INSERT INTO languages (name) VALUES (%s) RETURNING id", (language,))
                                language_id = cursor.fetchone()["id"]
                            cursor.execute("INSERT INTO book_languages (book_id, language_id) VALUES (%s, %s)", (book_id, language_id))
                
                # Handle categories update - remove old and add new
                if categories:
                    cursor.execute("DELETE FROM book_categories WHERE book_id = %s", (book_id,))
                    for category in categories:
                        if category:
                            cursor.execute("SELECT id FROM categories WHERE LOWER(name) = %s", (category.lower(),))
                            category_result = cursor.fetchone()
                            if category_result:
                                category_id = category_result["id"]
                            else:
                                cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (category,))
                                category_id = cursor.fetchone()["id"]
                            cursor.execute("INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)", (book_id, category_id))
                
                # Handle authors update - remove old and add new
                if authors:
                    cursor.execute("DELETE FROM book_authors WHERE book_id = %s", (book_id,))
                    for author in authors:
                        if author:
                            cursor.execute("SELECT id FROM authors WHERE LOWER(name) = %s", (author.lower(),))
                            author_result = cursor.fetchone()
                            if author_result:
                                author_id = author_result["id"]
                            else:
                                cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id", (author,))
                                author_id = cursor.fetchone()["id"]
                            cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)", (book_id, author_id))
                
                if update_fields:
                    query = "UPDATE books SET " + ", ".join(update_fields) + " WHERE id = %s"
                    cursor.execute(query, (*update_values, book_id))
                    
                return jsonify({"message": "Book updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@books_api.route('/search/<string:title>', methods=['GET'])
def search_book_from_open_library(title):
    # Get limit from query parameter, default to 1
    limit_param = request.args.get('limit', 1)
    try:
        limit = int(limit_param)
    except (ValueError, TypeError):
        return jsonify({"error": "Limit parameter must be an integer"}), 400

    try:
        book_data = OpenLibraryService.search_book_by_title(title, limit=limit)
        if book_data:
            return jsonify(book_data)
        else:
            return jsonify({"error": f"No books found in Open Library for title '{title}'"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _add_book_to_db(book_data):
    """Helper function to add book data to database."""
    title = normalize_strings(book_data.get('title'))
    
    # Handle authors array (fallback to single author for backward compatibility)
    authors = book_data.get('authors', [])
    if not authors and book_data.get('author'):
        authors = [book_data.get('author')]
    authors = [normalize_strings(author) for author in authors if author]
    
    # Handle languages array (fallback to single language for backward compatibility)
    languages = book_data.get('languages', [])
    if not languages and book_data.get('language'):
        languages = [book_data.get('language')]
    languages = [normalize_strings(lang) for lang in languages if lang]
    
    # Handle categories array
    categories = book_data.get('categories', [])
    categories = [normalize_strings(cat) for cat in categories if cat]
    
    open_library_id = normalize_strings(book_data.get('open_library_id'))
    publication_year = book_data.get('publication_year')
    cover_id = book_data.get('cover_id')

    if not title:
        raise ValueError("Title is required")
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # Check if book exists
            cursor.execute("SELECT * FROM books WHERE LOWER(REGEXP_REPLACE(title, '\\s+', ' ', 'g')) = %s", (normalize_strings(title),))
            existing_book = cursor.fetchone()
            if existing_book:
                raise ValueError("Book already exists")
            
            # Insert book
            cursor.execute(
                "INSERT INTO books (title, publication_year, open_library_id, cover_id) VALUES (%s, %s, %s, %s) RETURNING id",
                (title, publication_year, open_library_id, cover_id)
            )
            new_book_id = cursor.fetchone()["id"]
            
            # Handle languages array
            for language in languages:
                if language:
                    cursor.execute("SELECT id FROM languages WHERE LOWER(name) = %s", (language.lower(),))
                    language_result = cursor.fetchone()
                    if language_result:
                        language_id = language_result["id"]
                    else:
                        cursor.execute("INSERT INTO languages (name) VALUES (%s) RETURNING id", (language,))
                        language_id = cursor.fetchone()["id"]
                    
                    cursor.execute("INSERT INTO book_languages (book_id, language_id) VALUES (%s, %s)", (new_book_id, language_id))
            
            # Handle authors array
            for author in authors:
                if author:
                    cursor.execute("SELECT id FROM authors WHERE LOWER(name) = %s", (author.lower(),))
                    author_result = cursor.fetchone()
                    if author_result:
                        author_id = author_result["id"]
                    else:
                        cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id", (author,))
                        author_id = cursor.fetchone()["id"]
                    
                    cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)", (new_book_id, author_id))
            
            # Handle categories array
            for category in categories:
                if category:
                    cursor.execute("SELECT id FROM categories WHERE LOWER(name) = %s", (category.lower(),))
                    category_result = cursor.fetchone()
                    if category_result:
                        category_id = category_result["id"]
                    else:
                        cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (category,))
                        category_id = cursor.fetchone()["id"]
                    
                    cursor.execute("INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s)", (new_book_id, category_id))

            return new_book_id

@books_api.route('/import/<string:title>', methods=['POST'])
def import_book_from_open_library(title):
    """Import a book from Open Library API directly to database."""
    try:
        book_data = OpenLibraryService.search_book_by_title(title)
        if not book_data:
            return jsonify({"error": "Book not found in Open Library"}), 404
        
        book_id = _add_book_to_db(book_data)
        return jsonify({"message": "Book imported successfully", "book_id": book_id, "source": "Open Library"}), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
