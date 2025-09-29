from flask import Flask, render_template, url_for, redirect, jsonify, request, session, flash
from routes import books_api, categories_api, authors_api, users_api, collections_api, languages_api
from routes.frontend_api import frontend_api
from routes.auth import auth, get_current_user, is_logged_in, login_required, admin_required, is_admin, can_edit_collection
from database import get_db
import requests
from datetime import datetime
import random
import os

app = Flask(__name__)

# Session configuration
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register blueprints
app.register_blueprint(books_api)
app.register_blueprint(categories_api)
app.register_blueprint(languages_api)
app.register_blueprint(collections_api)
app.register_blueprint(users_api)
app.register_blueprint(authors_api)
app.register_blueprint(frontend_api)
app.register_blueprint(auth)

# Make auth functions available to all templates
@app.context_processor
def inject_auth():
    return {
        'current_user': get_current_user(),
        'is_logged_in': is_logged_in(),
        'is_admin': is_admin(),
        'can_edit_collection': can_edit_collection
    }

def get_books_data():
    """Fetch books data from the database"""
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
                               GROUP BY books.id, books.title, books.publication_year, books.open_library_id, books.cover_id
                               ORDER BY books.id""")
                return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching books: {e}")
        return []

def get_categories_data():
    """Fetch categories data from the database"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM categories ORDER BY name")
                return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []

def get_authors_data():
    """Fetch authors data from the database"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        authors.id, 
                        authors.name,
                        authors.image_url,
                        COUNT(books.id) as book_count,
                        COALESCE(
                            ARRAY_AGG(books.title) FILTER (WHERE books.title IS NOT NULL), 
                            ARRAY[]::text[]
                        ) as book_titles
                    FROM authors
                    LEFT JOIN book_authors ON authors.id = book_authors.author_id
                    LEFT JOIN books ON book_authors.book_id = books.id
                    GROUP BY authors.id, authors.name, authors.image_url
                    ORDER BY book_count DESC, authors.name;
                """)
                return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching authors: {e}")
        return []

def get_statistics():
    """Get application statistics"""
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                stats = {}
                
                cursor.execute("SELECT COUNT(*) as count FROM books")
                stats['total_books'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM authors")
                stats['total_authors'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM categories")
                stats['total_categories'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM users")
                stats['total_users'] = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM collections")
                stats['total_collections'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM books WHERE cover_id IS NOT NULL")
                stats['books_with_covers'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM books WHERE cover_id IS NULL")
                stats['missing_covers'] = cursor.fetchone()['count']
                
                return stats
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return {}

def organize_books_by_category(books, categories):
    """Organize books by category for tabbed display"""
    books_by_category = {'all': list(books)}
    
    for category in categories:
        category_name = category['name']
        category_books = [book for book in books 
                         if book['categories'] and category_name in book['categories']]
        books_by_category[category_name] = category_books
    
    return books_by_category

@app.route('/')
def home():
    try:
        # Fetch all data
        books = get_books_data()
        categories = get_categories_data()
        authors = get_authors_data()
        stats = get_statistics()
        
        print(f"DEBUG: Found {len(books)} books")
        print(f"DEBUG: Sample book: {books[0] if books else 'No books'}")
        
        # Organize data for template
        featured_books = books[:6] if books else []
        popular_books = books[6:14] if len(books) > 6 else books
        latest_books = books[-8:] if len(books) >= 8 else books
        special_books = books[-5:] if len(books) >= 5 else books
        
        print(f"DEBUG: Featured books: {len(featured_books)}")
        print(f"DEBUG: Popular books: {len(popular_books)}")
        
        # Organize books by category
        books_by_category_data = organize_books_by_category(books, categories)
        
        return render_template('home.html',
                             books=books,
                             books_by_category=books_by_category_data,
                             featured_books=featured_books,
                             popular_books=popular_books,
                             latest_books=latest_books,
                             special_books=special_books,
                             stats=stats)
    except Exception as e:
        print(f"Home route error: {e}")
        return render_template('home.html',
                             books=[],
                             books_by_category={},
                             featured_books=[],
                             popular_books=[],
                             latest_books=[],
                             special_books=[],
                             stats={})

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
        print(f"Error fetching book {book_id}: {e}")
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
        print(f"Admin dashboard error: {e}")
        return render_template('admin_enhanced.html', stats={}, error=str(e))

@app.route('/books')
def all_books():
    """All books page with search and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        per_page = 20
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # Build the query based on filters
                where_conditions = []
                params = []
                
                if search:
                    where_conditions.append("""
                        (books.title ILIKE %s 
                         OR authors.name ILIKE %s 
                         OR categories.name ILIKE %s)
                    """)
                    search_param = f'%{search}%'
                    params.extend([search_param, search_param, search_param])
                
                if category:
                    where_conditions.append("categories.name = %s")
                    params.append(category)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(DISTINCT books.id)
                    FROM books
                    LEFT JOIN book_authors ON books.id = book_authors.book_id
                    LEFT JOIN authors ON book_authors.author_id = authors.id
                    LEFT JOIN book_categories ON books.id = book_categories.book_id
                    LEFT JOIN categories ON book_categories.category_id = categories.id
                    {where_clause}
                """
                cursor.execute(count_query, params)
                result = cursor.fetchone()
                total = list(result.values())[0] if result else 0
                
                # Get books for current page
                offset = (page - 1) * per_page
                books_query = f"""
                    SELECT DISTINCT books.id, books.title, books.publication_year, books.cover_id,
                           COALESCE(
                               ARRAY_AGG(DISTINCT authors.name) FILTER (WHERE authors.name IS NOT NULL), 
                               ARRAY[]::text[]
                           ) AS authors,
                           COALESCE(
                               ARRAY_AGG(DISTINCT categories.name) FILTER (WHERE categories.name IS NOT NULL), 
                               ARRAY[]::text[]
                           ) AS categories
                    FROM books
                    LEFT JOIN book_authors ON books.id = book_authors.book_id
                    LEFT JOIN authors ON book_authors.author_id = authors.id
                    LEFT JOIN book_categories ON books.id = book_categories.book_id
                    LEFT JOIN categories ON book_categories.category_id = categories.id
                    {where_clause}
                    GROUP BY books.id, books.title, books.publication_year, books.cover_id
                    ORDER BY books.title
                    LIMIT %s OFFSET %s
                """
                cursor.execute(books_query, params + [per_page, offset])
                books = cursor.fetchall()
                
                # Get categories for filter dropdown
                cursor.execute("SELECT id, name FROM categories ORDER BY name")
                categories = cursor.fetchall()
                
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
                
                return render_template('all_books.html', 
                                     books=books, 
                                     categories=categories,
                                     pagination=pagination)
                
    except Exception as e:
        print(f"All books error: {e}")
        return render_template('all_books.html', books=[], categories=[], error=str(e))

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
                count_query = f"""
                    SELECT COUNT(DISTINCT authors.id)
                    FROM authors
                    {where_clause}
                """
                cursor.execute(count_query, params)
                result = cursor.fetchone()
                total = list(result.values())[0] if result else 0
                
                # Get authors for current page with book count
                offset = (page - 1) * per_page
                authors_query = f"""
                    SELECT authors.id, authors.name, authors.image_url,
                           COUNT(DISTINCT books.id) as book_count
                    FROM authors
                    LEFT JOIN book_authors ON authors.id = book_authors.author_id
                    LEFT JOIN books ON book_authors.book_id = books.id
                    {where_clause}
                    GROUP BY authors.id, authors.name, authors.image_url
                    ORDER BY authors.name
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
        print(f"All authors error: {e}")
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
        print(f"Collections page error: {e}")
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
        print(f"Create collection error: {e}")
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
        print(f"Edit collection error: {e}")
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
        print(f"Get collection error: {e}")
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
        print(f"Edit collection by ID error: {e}")
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
        print(f"Delete collection error: {e}")
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
        print(f"Manage collection books error: {e}")
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
        print(f"Add book to collection error: {e}")  # Log the error for debugging
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
        print(f"Remove book from collection error: {e}")
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
        print(f"Search books error: {e}")
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
        print(f"Load more books error: {e}")
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
