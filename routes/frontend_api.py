from flask import Blueprint, jsonify, request
from database import get_db
from services.open_library_service import OpenLibraryService

frontend_api = Blueprint('frontend_api', __name__, url_prefix='/api/frontend')

@frontend_api.route('/authors/update-image/<int:author_id>', methods=['POST'])
def update_author_image_url(author_id):
    """Manually update author image URL"""
    try:
        data = request.get_json()
        image_url = data.get('image_url', '').strip()
        
        if not image_url:
            return jsonify({'success': False, 'error': 'Image URL is required'}), 400
        
        # Basic URL validation
        if not (image_url.startswith('http://') or image_url.startswith('https://')):
            return jsonify({'success': False, 'error': 'Image URL must start with http:// or https://'}), 400
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check if author exists
                cursor.execute("SELECT name FROM authors WHERE id = %s", (author_id,))
                author = cursor.fetchone()
                
                if not author:
                    return jsonify({'success': False, 'error': 'Author not found'}), 404
                
                author_name = author['name']
                
                # Update the image URL
                cursor.execute(
                    "UPDATE authors SET image_url = %s WHERE id = %s",
                    (image_url, author_id)
                )
                
                if cursor.rowcount > 0:
                    return jsonify({
                        'success': True,
                        'message': f'Updated image URL for {author_name}',
                        'image_url': image_url
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to update database'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@frontend_api.route('/authors/image-by-name', methods=['GET'])
def get_author_image_by_name():
    """Get Open Library author image URL by author name."""
    try:
        name = (request.args.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'name is required'}), 400

        ol_author = OpenLibraryService.search_author_by_name(name)
        if ol_author and ol_author.get('open_library_key'):
            url = OpenLibraryService.get_author_image_url(ol_author['open_library_key'], 'M')
            return jsonify({'image_url': url})
        return jsonify({'image_url': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@frontend_api.route('/books/by-author', methods=['GET'])
def get_books_by_author():
    """Get books by a specific author"""
    try:
        author_name = request.args.get('author')
        if not author_name:
            return jsonify({'error': 'Author name is required'}), 400
            
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT
                        books.id,
                        books.title,
                        books.publication_year,
                        books.cover_id,
                        books.open_library_id
                    FROM books
                    INNER JOIN book_authors ON books.id = book_authors.book_id
                    INNER JOIN authors ON book_authors.author_id = authors.id
                    WHERE LOWER(authors.name) = LOWER(%s)
                    ORDER BY books.publication_year DESC NULLS LAST, books.title
                """, (author_name,))
                
                books = cursor.fetchall()
                return jsonify(books)
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@frontend_api.route('/books/update-cover/<int:book_id>', methods=['POST'])
def update_book_cover(book_id):
    """Update cover for a specific book"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Get book details
                cursor.execute("""
                    SELECT title, publication_year, isbn,
                           ARRAY_AGG(authors.name) as author_names
                    FROM books
                    LEFT JOIN book_authors ON books.id = book_authors.book_id
                    LEFT JOIN authors ON book_authors.author_id = authors.id
                    WHERE books.id = %s
                    GROUP BY books.id, books.title, books.publication_year, books.isbn
                """, (book_id,))
                
                book = cursor.fetchone()
                if not book:
                    return jsonify({'success': False, 'message': 'Book not found'}), 404
                
                # Try to get cover from Open Library
                ol_service = OpenLibraryService()
                cover_url = None
                
                # Try with ISBN first if available
                if book['isbn']:
                    cover_url = ol_service.get_book_cover_by_isbn(book['isbn'])
                
                # If no cover found with ISBN, try with title and author
                if not cover_url and book['title'] and book['author_names']:
                    author_names = [name for name in book['author_names'] if name]
                    if author_names:
                        cover_url = ol_service.get_book_cover_by_title_author(
                            book['title'], 
                            author_names[0]  # Use first author
                        )
                
                if cover_url:
                    # Update the book's cover URL
                    cursor.execute(
                        "UPDATE books SET cover_url = %s WHERE id = %s",
                        (cover_url, book_id)
                    )
                    
                    return jsonify({
                        'success': True, 
                        'message': 'Cover updated successfully',
                        'cover_url': cover_url
                    })
                else:
                    return jsonify({
                        'success': False, 
                        'message': 'No cover found for this book'
                    })
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@frontend_api.route('/covers/update-missing', methods=['POST'])
def update_missing_covers():
    """Update covers for all books that don't have covers"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Get all books without covers
                cursor.execute("""
                    SELECT books.id, books.title, books.publication_year, books.isbn,
                           ARRAY_AGG(authors.name) as author_names
                    FROM books
                    LEFT JOIN book_authors ON books.id = book_authors.book_id
                    LEFT JOIN authors ON book_authors.author_id = authors.id
                    WHERE books.cover_url IS NULL OR books.cover_url = ''
                    GROUP BY books.id, books.title, books.publication_year, books.isbn
                    ORDER BY books.id
                """)
                
                books_without_covers = cursor.fetchall()
                total_count = len(books_without_covers)
                updated_count = 0
                
                ol_service = OpenLibraryService()
                
                for book in books_without_covers:
                    cover_url = None
                    
                    # Try with ISBN first if available
                    if book['isbn']:
                        cover_url = ol_service.get_book_cover_by_isbn(book['isbn'])
                    
                    # If no cover found with ISBN, try with title and author
                    if not cover_url and book['title'] and book['author_names']:
                        author_names = [name for name in book['author_names'] if name]
                        if author_names:
                            cover_url = ol_service.get_book_cover_by_title_author(
                                book['title'], 
                                author_names[0]  # Use first author
                            )
                    
                    if cover_url:
                        # Update the book's cover URL
                        cursor.execute(
                            "UPDATE books SET cover_url = %s WHERE id = %s",
                            (cover_url, book['id'])
                        )
                        updated_count += 1
                
                return jsonify({
                    'success': True,
                    'message': f'Updated {updated_count} covers out of {total_count} books',
                    'total_count': total_count,
                    'updated_count': updated_count
                })
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
