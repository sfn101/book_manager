"""
Books Manager Application - Main Flask Application
=================================================

A comprehensive Flask-based web application for managing books, authors, categories,
and user collections. Features include:

- User authentication and authorization
- Book management with Open Library integration
- Author and category management
- User collections and book organization
- Admin dashboard with CRUD operations
- Search and filtering capabilities
- Responsive web interface

Author: Books Manager Team
Version: 1.0.0
"""

from flask import Flask, render_template, url_for, redirect, jsonify, request, session, flash
from routes import books_api, categories_api, authors_api, users_api, collections_api, languages_api
from routes.frontend_api import frontend_api
from routes.search_api import search_api
from routes.statistics_api import statistics_api
from routes.auth import auth, get_current_user, is_logged_in, login_required, admin_required, is_admin, can_edit_collection
from database import get_db
from services.home_service import HomeService
from services.books_service import BooksService
from util.pagination import Pagination
import requests
from datetime import datetime
import random
import os

# Initialize Flask application
app = Flask(__name__)

# =============================================================================
# CONFIGURATION SETUP
# =============================================================================
# Load configuration based on environment (development/production)
from config import config
config_class = config.get(os.getenv('FLASK_ENV', 'development'), config['default'])
app.config.from_object(config_class)

# Validate configuration settings
try:
    config_class.validate_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    if os.getenv('FLASK_ENV') == 'production':
        raise

# =============================================================================
# BLUEPRINT REGISTRATION
# =============================================================================
# Register all API blueprints for modular routing
app.register_blueprint(books_api)          # Book management endpoints
app.register_blueprint(categories_api)     # Category management endpoints
app.register_blueprint(languages_api)      # Language management endpoints
app.register_blueprint(collections_api)    # Collection management endpoints
app.register_blueprint(users_api)          # User management endpoints
app.register_blueprint(authors_api)        # Author management endpoints
app.register_blueprint(frontend_api)       # Frontend-specific endpoints
app.register_blueprint(auth)               # Authentication endpoints
app.register_blueprint(search_api)         # Search functionality endpoints
app.register_blueprint(statistics_api)     # Statistics endpoints

# =============================================================================
# TEMPLATE CONTEXT PROCESSORS
# =============================================================================
# Make authentication functions available to all templates
@app.context_processor
def inject_auth():
    """
    Inject authentication context into all templates.
    
    Returns:
        dict: Authentication context including current user info and permissions
    """
    return {
        'current_user': get_current_user(),
        'is_logged_in': is_logged_in(),
        'is_admin': is_admin(),
        'can_edit_collection': can_edit_collection
    }



# =============================================================================
# ROUTE DEFINITIONS
# =============================================================================

@app.route('/')
def home():
    """
    Home page route displaying featured books and application statistics.
    
    Returns:
        str: Rendered home page template with book data and statistics
    """
    home_data = HomeService.get_home_data()
    return render_template('home.html', **home_data)

@app.route('/author/<string:author_name>')
def author_detail_page(author_name):
    """Server-rendered author page with Open Library info and local books grid."""
    try:
        from services.open_library_service import OpenLibraryService

        # Fetch Open Library author info (best-effort)
        ol_author = OpenLibraryService.search_author_by_name(author_name) or {}
        author_image_url = None
        if ol_author.get('open_library_key'):
            author_image_url = OpenLibraryService.get_author_image_url(ol_author['open_library_key'], 'L')

        # Fetch books by this author from local DB
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT b.id, b.title, b.publication_year, b.cover_id,
                           COALESCE(ARRAY_AGG(DISTINCT a2.name) FILTER (WHERE a2.name IS NOT NULL), ARRAY[]::text[]) AS authors,
                           COALESCE(ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), ARRAY[]::text[]) AS categories
                    FROM books b
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    LEFT JOIN book_categories bc ON b.id = bc.book_id
                    LEFT JOIN categories c ON bc.category_id = c.id
                    LEFT JOIN book_authors ba2 ON b.id = ba2.book_id
                    LEFT JOIN authors a2 ON ba2.author_id = a2.id
                    WHERE LOWER(a.name) = LOWER(%s)
                    GROUP BY b.id, b.title, b.publication_year, b.cover_id
                    ORDER BY b.title
                    """,
                    (author_name,)
                )
                books = cursor.fetchall() or []

        return render_template(
            'author_detail.html',
            author_name=author_name,
            author_image_url=author_image_url,
            ol_author=ol_author,
            books=books,
        )
    except Exception as e:
        return render_template('author_detail.html', author_name=author_name, author_image_url=None, ol_author={}, books=[], error=str(e))

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    """Individual book detail page"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT 
                               books.id,
                               books.title,
                               books.publication_year,
                               books.open_library_id,
                               books.cover_id,
                               COALESCE(
                                   ARRAY_AGG(DISTINCT categories.name) FILTER (WHERE categories.name IS NOT NULL), 
                                   ARRAY[]::text[]
                               ) AS categories,
                               COALESCE(
                                   ARRAY_AGG(DISTINCT languages.name) FILTER (WHERE languages.name IS NOT NULL), 
                                   ARRAY[]::text[]
                               ) AS languages,
                               COALESCE(
                                   ARRAY_AGG(DISTINCT authors.name) FILTER (WHERE authors.name IS NOT NULL), 
                                   ARRAY[]::text[]
                               ) AS authors
                               FROM books
                               LEFT JOIN book_languages ON books.id = book_languages.book_id
                               LEFT JOIN languages ON book_languages.language_id = languages.id
                               LEFT JOIN book_authors ON books.id = book_authors.book_id
                               LEFT JOIN authors ON book_authors.author_id = authors.id
                               LEFT JOIN book_categories ON books.id = book_categories.book_id
                               LEFT JOIN categories ON book_categories.category_id = categories.id
                               WHERE books.id = %s
                               GROUP BY books.id, books.title, books.publication_year, books.open_library_id, books.cover_id""", (book_id,))
                book = cursor.fetchone()
                if book:
                    return render_template('book_detail.html', book=book)
                else:
                    return render_template('404.html'), 404
    except Exception as e:
        return render_template('500.html'), 500

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Render the admin dashboard with data for server-side rendering."""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Fetch all data for the admin panel
                
                # Books
                cursor.execute("""
                    SELECT b.id, b.title, b.publication_year, b.cover_id,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors,
                           ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL) as categories
                    FROM books b
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    LEFT JOIN book_categories bc ON b.id = bc.book_id
                    LEFT JOIN categories c ON bc.category_id = c.id
                    GROUP BY b.id
                    ORDER BY b.title
                """)
                books = cursor.fetchall()

                # Authors
                cursor.execute("""
                    SELECT a.id, a.name, a.image_url, COUNT(ba.book_id) as book_count
                    FROM authors a
                    LEFT JOIN book_authors ba ON a.id = ba.author_id
                    GROUP BY a.id
                    ORDER BY a.name
                """)
                authors = cursor.fetchall()

                # Categories
                cursor.execute("""
                    SELECT c.id, c.name, COUNT(bc.book_id) as book_count
                    FROM categories c
                    LEFT JOIN book_categories bc ON c.id = bc.category_id
                    GROUP BY c.id
                    ORDER BY c.name
                """)
                categories = cursor.fetchall()

                # Languages
                cursor.execute("""
                    SELECT l.id, l.name, COUNT(bl.book_id) as book_count
                    FROM languages l
                    LEFT JOIN book_languages bl ON l.id = bl.language_id
                    GROUP BY l.id
                    ORDER BY l.name
                """)
                languages = cursor.fetchall()

                # Users
                cursor.execute("""
                    SELECT u.id, u.username, u.email, u.created_at, COUNT(c.id) as collection_count
                    FROM users u
                    LEFT JOIN collections c ON u.id = c.user_id
                    GROUP BY u.id
                    ORDER BY u.username
                """)
                users = cursor.fetchall()

                # Statistics
                stats = {
                    'total_books': len(books),
                    'total_authors': len(authors),
                    'total_categories': len(categories),
                    'total_languages': len(languages),
                    'total_users': len(users),
                    'books_with_covers': sum(1 for book in books if book.get('cover_id')),
                    'total_collections': sum(user['collection_count'] for user in users)
                }
                stats['missing_covers'] = stats['total_books'] - stats['books_with_covers']
                stats['cover_percentage'] = (stats['books_with_covers'] / stats['total_books'] * 100) if stats['total_books'] > 0 else 0

        return render_template('admin_enhanced.html', 
                             stats=stats,
                             books=books,
                             authors=authors,
                             categories=categories,
                             languages=languages,
                             users=users)
        
    except Exception as e:
        return render_template('admin_enhanced.html', stats={}, error=str(e))

@app.route('/books')
def all_books():
    """All books page with search, filters, and pagination"""
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'title').strip()
    per_page = 20
    
    filters = BooksService.build_filters_from_request(request.args)
    page_data = BooksService.get_books_page_data(page, per_page, filters, sort_by)
    
    return render_template('all_books.html', **page_data)

@app.route('/authors')
def all_authors():
    """All authors page with search and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        per_page = 20
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Build the query based on search
                where_clause = ""
                params = []
                
                if search:
                    where_clause = "WHERE authors.name ILIKE %s"
                    params.append(f'%{search}%')
                
                # Get total count
                count_base_query = """
                    SELECT COUNT(DISTINCT authors.id)
                    FROM authors
                """
                count_query = count_base_query + where_clause
                cursor.execute(count_query, params)
                result = cursor.fetchone()
                total = list(result.values())[0] if result else 0
                
                # Get authors for current page with book count
                offset = (page - 1) * per_page
                authors_base_query = """
                    SELECT authors.id, authors.name, authors.image_url,
                           COUNT(DISTINCT books.id) as book_count
                    FROM authors
                    LEFT JOIN book_authors ON authors.id = book_authors.author_id
                    LEFT JOIN books ON book_authors.book_id = books.id
                """
                authors_query = authors_base_query + where_clause + """
                    GROUP BY authors.id, authors.name, authors.image_url
                    ORDER BY LOWER(authors.name)
                    LIMIT %s OFFSET %s
                """
                cursor.execute(authors_query, params + [per_page, offset])
                authors = cursor.fetchall()
                
                # Simple pagination object
                class Pagination:
                    def __init__(self, page, per_page, total):
                        self.page = page
                        self.per_page = per_page
                        self.total = total
                        self.pages = (total - 1) // per_page + 1 if total > 0 else 0
                        self.has_prev = page > 1
                        self.has_next = page < self.pages
                        self.prev_num = page - 1 if self.has_prev else None
                        self.next_num = page + 1 if self.has_next else None
                    
                    def iter_pages(self):
                        start = max(1, self.page - 2)
                        end = min(self.pages + 1, self.page + 3)
                        return range(start, end)
                
                pagination = Pagination(page, per_page, total)
                
                return render_template('all_authors.html', 
                                     authors=authors, 
                                     pagination=pagination)
                
    except Exception as e:
        return render_template('all_authors.html', authors=[], error=str(e))

@app.route('/collections')
@login_required
def collections_page():
    """Collections page with role-based access"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                user_id = session['user_id']
                is_admin = session.get('role') == 'admin'
                
                if is_admin:
                    # Admin can see all users and their collections
                    cursor.execute("""
                        SELECT u.id, u.username, u.email, 
                               TO_CHAR(u.created_at, 'Month YYYY') as created_at_formatted,
                               u.created_at, u.role,
                               COUNT(DISTINCT c.id) as collection_count,
                               COALESCE(
                                   json_agg(
                                       DISTINCT jsonb_build_object(
                                           'id', c.id,
                                           'name', c.name,
                                           'description', c.description,
                                           'created_at', TO_CHAR(c.created_at, 'Mon DD, YYYY'),
                                           'book_count', (
                                               SELECT COUNT(*) 
                                               FROM collection_books cb 
                                               WHERE cb.collection_id = c.id
                                           )
                                       )
                                   ) FILTER (WHERE c.id IS NOT NULL),
                                   '[]'::json
                               ) as collections
                        FROM users u
                        LEFT JOIN collections c ON u.id = c.user_id
                        GROUP BY u.id, u.username, u.email, u.created_at, u.role
                        ORDER BY u.username
                    """)
                else:
                    # Regular user can only see their own collections
                    cursor.execute("""
                        SELECT u.id, u.username, u.email, 
                               TO_CHAR(u.created_at, 'Month YYYY') as created_at_formatted,
                               u.created_at, u.role,
                               COUNT(DISTINCT c.id) as collection_count,
                               COALESCE(
                                   json_agg(
                                       DISTINCT jsonb_build_object(
                                           'id', c.id,
                                           'name', c.name,
                                           'description', c.description,
                                           'created_at', TO_CHAR(c.created_at, 'Mon DD, YYYY'),
                                           'book_count', (
                                               SELECT COUNT(*) 
                                               FROM collection_books cb 
                                               WHERE cb.collection_id = c.id
                                           )
                                       )
                                   ) FILTER (WHERE c.id IS NOT NULL),
                                   '[]'::json
                               ) as collections
                        FROM users u
                        LEFT JOIN collections c ON u.id = c.user_id
                        WHERE u.id = %s
                        GROUP BY u.id, u.username, u.email, u.created_at, u.role
                    """, (user_id,))
                
                users = cursor.fetchall()
                
                # Get all books for adding to collections
                cursor.execute("""
                    SELECT b.id, b.title,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors
                    FROM books b
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    GROUP BY b.id
                    ORDER BY b.title
                """)
                books = cursor.fetchall()
                
        return render_template('collections.html', users=users, books=books, is_admin=is_admin)
        
    except Exception as e:
        return render_template('collections.html', users=[], books=[], error=str(e), is_admin=False)

@app.route('/collections/create', methods=['POST'])
@login_required
def create_collection():
    """Create a new collection"""
    try:
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not user_id or not name:
            return redirect('/collections?error=Missing required fields')
        
        # Check permissions: users can only create collections for themselves, admins can create for anyone
        if not is_admin() and str(session.get('user_id')) != str(user_id):
            flash('You can only create collections for yourself', 'error')
            return redirect('/collections')
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO collections (user_id, name, description) VALUES (%s, %s, %s)",
                    (user_id, name, description)
                )
                
        return redirect('/collections?success=Collection created successfully')
        
    except Exception as e:
        return redirect('/collections?error=Failed to create collection')

@app.route('/collections/edit', methods=['POST'])
@login_required
def edit_collection():
    """Edit an existing collection"""
    try:
        collection_id = request.form.get('collection_id')
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not collection_id or not name:
            return redirect('/collections?error=Missing required fields')
        
        # Check if user can edit this collection
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    flash('Collection not found', 'error')
                    return redirect('/collections')
                
                if not can_edit_collection(collection['user_id']):
                    flash('You do not have permission to edit this collection', 'error')
                    return redirect('/collections')
                
                cursor.execute(
                    "UPDATE collections SET name = %s, description = %s WHERE id = %s",
                    (name, description, collection_id)
                )
                
        return redirect('/collections?success=Collection updated successfully')
        
    except Exception as e:
        return redirect('/collections?error=Failed to update collection')

@app.route('/collections/<int:collection_id>')
@login_required
def get_collection(collection_id):
    """Get collection details as JSON"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM collections c 
                    JOIN users u ON c.user_id = u.id 
                    WHERE c.id = %s
                """, (collection_id,))
                
                collection = cursor.fetchone()
                
                if not collection:
                    return jsonify({'success': False, 'message': 'Collection not found'})
                
                # Check if user can access this collection
                if not can_edit_collection(collection['user_id']) and not is_admin():
                    return jsonify({'success': False, 'message': 'Permission denied'})
                
                return jsonify({
                    'success': True,
                    'collection': {
                        'id': collection['id'],
                        'name': collection['name'],
                        'description': collection.get('description'),
                        'user_id': collection['user_id'],
                        'username': collection['username']
                    }
                })
                
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error'})

@app.route('/collections/<int:collection_id>/edit', methods=['POST'])
@login_required
def edit_collection_by_id(collection_id):
    """Edit collection by ID"""
    try:
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Collection name is required', 'error')
            return redirect('/collections')
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check if collection exists and user has permission
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    flash('Collection not found', 'error')
                    return redirect('/collections')
                
                if not can_edit_collection(collection['user_id']):
                    flash('You do not have permission to edit this collection', 'error')
                    return redirect('/collections')
                
                cursor.execute("""
                    UPDATE collections 
                    SET name = %s, description = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (name, description, collection_id))
                
        flash('Collection updated successfully', 'success')
        return redirect('/collections')
        
    except Exception as e:
        flash('Failed to update collection', 'error')
        return redirect('/collections')

@app.route('/collections/<int:collection_id>/delete', methods=['POST'])
@login_required
def delete_collection(collection_id):
    """Delete a collection"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check if collection exists and user has permission
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    return jsonify({'success': False, 'message': 'Collection not found'})
                
                if not can_edit_collection(collection['user_id']):
                    return jsonify({'success': False, 'message': 'Permission denied'})
                
                # Delete collection (this will cascade delete collection_books due to foreign key)
                cursor.execute("DELETE FROM collections WHERE id = %s", (collection_id,))
                
        return jsonify({'success': True, 'message': 'Collection deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error'})

@app.route('/collections/<int:collection_id>/books')
@login_required  
def manage_collection_books(collection_id):
    """Get HTML for managing books in a collection"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check if collection exists and user has permission
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM collections c 
                    JOIN users u ON c.user_id = u.id 
                    WHERE c.id = %s
                """, (collection_id,))
                
                collection = cursor.fetchone()
                
                if not collection:
                    return "<div class='alert alert-danger'>Collection not found</div>"
                
                if not can_edit_collection(collection['user_id']) and not is_admin():
                    return "<div class='alert alert-danger'>Permission denied</div>"
                
                # Get books in this collection
                cursor.execute("""
                    SELECT b.id, b.title, b.publication_year, b.cover_id,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors
                    FROM collection_books cb
                    JOIN books b ON cb.book_id = b.id
                    LEFT JOIN book_authors ba ON b.id = ba.book_id  
                    LEFT JOIN authors a ON ba.author_id = a.id
                    WHERE cb.collection_id = %s
                    GROUP BY b.id, b.title, b.publication_year, b.cover_id
                    ORDER BY b.title
                """, (collection_id,))
                
                collection_books = cursor.fetchall()
                
                # Get all available books not in this collection
                cursor.execute("""
                    SELECT b.id, b.title, b.publication_year, b.cover_id,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors
                    FROM books b
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    WHERE b.id NOT IN (
                        SELECT book_id FROM collection_books WHERE collection_id = %s
                    )
                    GROUP BY b.id, b.title, b.publication_year, b.cover_id
                    ORDER BY b.title
                    LIMIT 20
                """, (collection_id,))
                
                available_books = cursor.fetchall()
                
                return render_template('components/manage_books.html', 
                                     collection=collection,
                                     collection_books=collection_books,
                                     available_books=available_books)
                
    except Exception as e:
        return "<div class='alert alert-danger'>Error loading books</div>"

@app.route('/collections/<int:collection_id>/books/add', methods=['POST'])
@login_required
def add_book_to_collection(collection_id):
    """Add a book to a collection"""
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        
        if not book_id:
            return jsonify({'success': False, 'message': 'Book ID required'})
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check collection permission
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    return jsonify({'success': False, 'message': 'Collection not found'})
                
                if not can_edit_collection(collection['user_id']):
                    return jsonify({'success': False, 'message': 'Permission denied'})
                
                # Check if book exists
                cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
                if not cursor.fetchone():
                    return jsonify({'success': False, 'message': 'Book not found'})
                
                # Check if book is already in collection
                cursor.execute("""
                    SELECT 1 FROM collection_books 
                    WHERE collection_id = %s AND book_id = %s
                """, (collection_id, book_id))
                
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': 'Book already in collection'})
                
                # Add book to collection
                cursor.execute("""
                    INSERT INTO collection_books (collection_id, book_id) 
                    VALUES (%s, %s)
                """, (collection_id, book_id))
                
        return jsonify({'success': True, 'message': 'Book added to collection'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error'})

@app.route('/collections/<int:collection_id>/books/remove', methods=['POST'])
@login_required
def remove_book_from_collection(collection_id):
    """Remove a book from a collection"""
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        
        if not book_id:
            return jsonify({'success': False, 'message': 'Book ID required'})
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check collection permission
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    return jsonify({'success': False, 'message': 'Collection not found'})
                
                if not can_edit_collection(collection['user_id']):
                    return jsonify({'success': False, 'message': 'Permission denied'})
                
                # Remove book from collection
                cursor.execute("""
                    DELETE FROM collection_books 
                    WHERE collection_id = %s AND book_id = %s
                """, (collection_id, book_id))
                
        return jsonify({'success': True, 'message': 'Book removed from collection'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error'})

@app.route('/collections/<int:collection_id>/books/search')
@login_required
def search_books_for_collection(collection_id):
    """Search for books to add to collection"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return "<div class='alert alert-warning'>Please enter at least 2 characters</div>"
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check collection permission
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    return "<div class='alert alert-danger'>Collection not found</div>"
                
                if not can_edit_collection(collection['user_id']):
                    return "<div class='alert alert-danger'>Permission denied</div>"
                
                # Search books not in this collection
                search_pattern = f"%{query}%"
                cursor.execute("""
                    SELECT DISTINCT b.id, b.title, b.publication_year, b.cover_id,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors
                    FROM books b
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    WHERE b.id NOT IN (
                        SELECT book_id FROM collection_books WHERE collection_id = %s
                    )
                    AND (
                        LOWER(b.title) LIKE LOWER(%s) OR
                        EXISTS (
                            SELECT 1 FROM book_authors ba2 
                            JOIN authors a2 ON ba2.author_id = a2.id 
                            WHERE ba2.book_id = b.id AND LOWER(a2.name) LIKE LOWER(%s)
                        )
                    )
                    GROUP BY b.id, b.title, b.publication_year, b.cover_id
                    ORDER BY b.title
                    LIMIT 20
                """, (collection_id, search_pattern, search_pattern))
                
                books = cursor.fetchall()
                
                if not books:
                    return f"""
                        <div class="text-center py-4">
                            <i class="fas fa-search text-muted" style="font-size: 3rem; opacity: 0.3;"></i>
                            <h6 class="text-muted mt-2">No books found</h6>
                            <p class="text-muted">No books match your search for "{query}"</p>
                        </div>
                    """
                
                # Render search results
                html = '<div class="row">'
                for book in books:
                    authors_str = ', '.join(book['authors']) if book['authors'] else 'Unknown Author'
                    authors_display = authors_str[:30] + '...' if len(authors_str) > 30 else authors_str
                    title_display = book['title'][:40] + '...' if len(book['title']) > 40 else book['title']
                    
                    cover_html = ''
                    if book['cover_url']:
                        cover_html = f'<img src="{book["cover_url"]}" alt="{book["title"]}" class="img-fluid" style="max-height: 180px; max-width: 120px; object-fit: cover;">'
                    else:
                        cover_html = '<div class="text-center text-muted"><i class="fas fa-book" style="font-size: 3rem; opacity: 0.3;"></i><br><small>No Cover</small></div>'
                    
                    html += f"""
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="card border-0 shadow-sm h-100">
                                <div class="card-img-top d-flex justify-content-center align-items-center bg-light" style="height: 200px;">
                                    {cover_html}
                                </div>
                                <div class="card-body p-3">
                                    <h6 class="card-title mb-1" title="{book['title']}">{title_display}</h6>
                                    <p class="card-text">
                                        <small class="text-muted">
                                            <i class="fas fa-user"></i> {authors_display}
                                            {f'<br><i class="fas fa-calendar"></i> {book["publication_year"]}' if book["publication_year"] else ''}
                                        </small>
                                    </p>
                                    <button class="btn btn-success btn-sm w-100" onclick="addBookToCollection({collection_id}, {book['id']})">
                                        <i class="fas fa-plus"></i> Add to Collection
                                    </button>
                                </div>
                            </div>
                        </div>
                    """
                
                html += '</div>'
                return html
                
    except Exception as e:
        return "<div class='alert alert-danger'>Error searching books</div>"

@app.route('/collections/<int:collection_id>/books/more')
@login_required
def load_more_books_for_collection(collection_id):
    """Load more books for collection (pagination)"""
    try:
        offset = int(request.args.get('offset', 0))
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Check collection permission
                cursor.execute("SELECT user_id FROM collections WHERE id = %s", (collection_id,))
                collection = cursor.fetchone()
                
                if not collection:
                    return "<div class='alert alert-danger'>Collection not found</div>"
                
                if not can_edit_collection(collection['user_id']):
                    return "<div class='alert alert-danger'>Permission denied</div>"
                
                # Get more books not in this collection
                cursor.execute("""
                    SELECT b.id, b.title, b.publication_year, b.cover_id,
                           ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as authors
                    FROM books b
                    LEFT JOIN book_authors ba ON b.id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.id
                    WHERE b.id NOT IN (
                        SELECT book_id FROM collection_books WHERE collection_id = %s
                    )
                    GROUP BY b.id, b.title, b.publication_year, b.cover_id
                    ORDER BY b.title
                    OFFSET %s LIMIT 20
                """, (collection_id, offset))
                
                books = cursor.fetchall()
                
                if not books:
                    return '<div class="row"></div>'  # Empty row means no more books
                
                # Render more books
                html = '<div class="row">'
                for book in books:
                    authors_str = ', '.join(book['authors']) if book['authors'] else 'Unknown Author'
                    authors_display = authors_str[:30] + '...' if len(authors_str) > 30 else authors_str
                    title_display = book['title'][:40] + '...' if len(book['title']) > 40 else book['title']
                    
                    cover_html = ''
                    if book['cover_url']:
                        cover_html = f'<img src="{book["cover_url"]}" alt="{book["title"]}" class="img-fluid" style="max-height: 180px; max-width: 120px; object-fit: cover;">'
                    else:
                        cover_html = '<div class="text-center text-muted"><i class="fas fa-book" style="font-size: 3rem; opacity: 0.3;"></i><br><small>No Cover</small></div>'
                    
                    html += f"""
                        <div class="col-md-6 col-lg-4 mb-3">
                            <div class="card border-0 shadow-sm h-100">
                                <div class="card-img-top d-flex justify-content-center align-items-center bg-light" style="height: 200px;">
                                    {cover_html}
                                </div>
                                <div class="card-body p-3">
                                    <h6 class="card-title mb-1" title="{book['title']}">{title_display}</h6>
                                    <p class="card-text">
                                        <small class="text-muted">
                                            <i class="fas fa-user"></i> {authors_display}
                                            {f'<br><i class="fas fa-calendar"></i> {book["publication_year"]}' if book["publication_year"] else ''}
                                        </small>
                                    </p>
                                    <button class="btn btn-success btn-sm w-100" onclick="addBookToCollection({collection_id}, {book['id']})">
                                        <i class="fas fa-plus"></i> Add to Collection
                                    </button>
                                </div>
                            </div>
                        </div>
                    """
                
                html += '</div>'
                return html
                
    except Exception as e:
        return "<div class='alert alert-danger'>Error loading more books</div>"

@app.route('/search')
def search():
    """Search functionality"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('home'))
    
    # Implementation for search functionality
    # This would use your existing search API endpoints
    return render_template('search_results.html', query=query)

if __name__ == '__main__':
    app.run(debug=True)
