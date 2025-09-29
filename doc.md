# Geeks Books Manager Application - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Database Schema](#database-schema)
7. [API Documentation](#api-documentation)
8. [Frontend Components](#frontend-components)
9. [Security Features](#security-features)
10. [Deployment](#deployment)
11. [Development Guide](#development-guide)
12. [Troubleshooting](#troubleshooting)

---

## Overview

**Geeks Books Manager** is a comprehensive Flask-based web application designed for managing books, authors, categories, and user collections. The application provides a modern, responsive interface for book enthusiasts, librarians, and administrators to organize and discover books efficiently.

### Key Highlights
- **Modern Web Framework**: Built with Flask and PostgreSQL
- **Responsive Design**: Mobile-friendly Bootstrap-based UI
- **Open Library Integration**: Automatic book data enrichment
- **User Management**: Role-based access control (Admin/User)
- **Collection Management**: Personal book collections
- **Advanced Search**: Multi-criteria filtering and search
- **Admin Dashboard**: Complete CRUD operations
- **Security**: bcrypt password hashing, secure sessions

---

## Features

### 🔐 Authentication & Authorization
- **User Registration & Login**: Secure user account management
- **Role-Based Access**: Admin and regular user roles
- **Session Management**: Secure session handling with configurable security
- **Password Security**: bcrypt hashing with proper salt rounds

### 📚 Book Management
- **Book CRUD Operations**: Create, read, update, delete books
- **Open Library Integration**: Automatic book data import
- **Cover Images**: Integration with Open Library cover service
- **Multi-Author Support**: Books can have multiple authors
- **Category & Language Tagging**: Flexible categorization system

### 👥 Author Management
- **Author Profiles**: Complete author information management
- **Author Images**: Support for author profile pictures
- **Book-Author Relationships**: Many-to-many relationships
- **Author Statistics**: Book count and popularity metrics

### 🏷️ Category & Language Management
- **Flexible Categories**: Custom category creation and management
- **Multi-Language Support**: Books can be tagged with multiple languages
- **Dynamic Filtering**: Real-time filtering by categories and languages

### 📖 Collection Management
- **Personal Collections**: Users can create custom book collections
- **Collection Sharing**: Admin can view all user collections
- **Collection Statistics**: Track collection size and diversity
- **Easy Book Management**: Add/remove books from collections

### 🔍 Search & Discovery
- **Advanced Search**: Search across titles, authors, and categories
- **Real-time Filtering**: Instant results as you type
- **Sorting Options**: Sort by title, year, author, or ID
- **Pagination**: Efficient handling of large datasets

### 📊 Admin Dashboard
- **Comprehensive Overview**: Statistics and system metrics
- **CRUD Operations**: Full management of all entities
- **User Management**: Admin can manage user accounts
- **Data Import**: Bulk import from Open Library
- **System Monitoring**: Track application usage and performance

---

## Architecture

### Technology Stack
```
Frontend:
├── HTML5/CSS3
├── Bootstrap 5
├── JavaScript (ES6+)
├── jQuery (legacy support)
└── Font Awesome Icons

Backend:
├── Python 3.8+
├── Flask 3.1.2
├── PostgreSQL
├── psycopg2-binary
└── bcrypt

External Services:
├── Open Library API
└── Open Library Covers
```

### Project Structure
```
books_manager/
├── app/
│   ├── __init__.py
│   ├── index.py                 # Main Flask application
│   ├── config.py               # Configuration management
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py       # Database connection
│   │   └── data_access.py      # Data access layer
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   └── error_handlers.py   # Error handling
│   ├── routes/                 # API routes
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication
│   │   ├── books_api.py       # Book management
│   │   ├── authors_api.py     # Author management
│   │   ├── categories_api.py  # Category management
│   │   ├── collections_api.py # Collection management
│   │   ├── languages_api.py   # Language management
│   │   ├── users_api.py       # User management
│   │   ├── frontend_api.py    # Frontend utilities
│   │   ├── search_api.py      # Search functionality
│   │   └── statistics_api.py  # Statistics
│   ├── services/              # Business logic
│   │   ├── home_service.py    # Home page logic
│   │   ├── books_service.py   # Book business logic
│   │   └── open_library_service.py # External API
│   ├── templates/             # Jinja2 templates
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── admin_enhanced.html
│   │   ├── auth/
│   │   ├── components/
│   │   └── ...
│   ├── static/               # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── util/                 # Utilities
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   └── pagination.py
│   └── test/                 # Test files
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
└── README.md               # Project documentation
```

### Design Patterns
- **MVC Architecture**: Clear separation of concerns
- **Service Layer**: Business logic separation
- **Repository Pattern**: Data access abstraction
- **Blueprint Pattern**: Modular route organization
- **Factory Pattern**: Configuration management

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd books_manager
```

### Step 2: Create Virtual Environment
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using uv (recommended)
uv venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Using pip
pip install -r requirements.txt

# Or using uv
uv pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
# Create PostgreSQL database
createdb books_manager

# Run database migrations
psql books_manager < database/seed/tabels_Init.sql
psql books_manager < database/seed/add_roles.sql
```

### Step 5: Environment Configuration
Create a `.env` file in the project root:
```env
# Database Configuration
HOST=localhost
PORT=5432
DB=books_manager
USER=your_username
PASSWORD=your_password

# Application Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DEBUG=True

# Open Library API
OPEN_LIBRARY_API_BASE=https://openlibrary.org
```

### Step 6: Run the Application
```bash
python index.py
```

The application will be available at `http://localhost:5000`

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Database host | - | Yes |
| `PORT` | Database port | 5432 | No |
| `DB` | Database name | - | Yes |
| `USER` | Database username | - | Yes |
| `PASSWORD` | Database password | - | Yes |
| `SECRET_KEY` | Flask secret key | - | Yes |
| `FLASK_ENV` | Environment (development/production) | development | No |
| `DEBUG` | Debug mode | False | No |
| `OPEN_LIBRARY_API_BASE` | Open Library API base URL | https://openlibrary.org | No |

### Configuration Classes

#### DevelopmentConfig
- Debug mode enabled
- Detailed error messages
- Relaxed security settings

#### ProductionConfig
- Debug mode disabled
- Secure session cookies
- Strict configuration validation

### Security Configuration
```python
# Session Security
SESSION_COOKIE_SECURE = True  # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

---

## Database Schema

### Entity Relationship Diagram
```
Users (1) ──── (N) Collections (N) ──── (N) Books
  │                                      │
  │                                      │
  └─── Role: admin/user                  │
                                        │
Authors (N) ──── (N) Books (N) ──── (N) Categories
  │                                      │
  │                                      │
  └─── image_url                         │
                                        │
Languages (N) ──── (N) Books
```

### Tables

#### Users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Books
```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publication_year INTEGER,
    open_library_id VARCHAR(50),
    cover_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Authors
```sql
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Categories
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Languages
```sql
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Collections
```sql
CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Junction Tables
```sql
-- Book-Author relationship
CREATE TABLE book_authors (
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- Book-Category relationship
CREATE TABLE book_categories (
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, category_id)
);

-- Book-Language relationship
CREATE TABLE book_languages (
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    language_id INTEGER REFERENCES languages(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, language_id)
);

-- Collection-Book relationship
CREATE TABLE collection_books (
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, book_id)
);
```

---

## API Documentation

### Authentication Endpoints

#### POST /login
User login endpoint.
```json
{
    "username": "string",
    "password": "string"
}
```

#### POST /signup
User registration endpoint.
```json
{
    "username": "string",
    "email": "string",
    "password": "string",
    "password_confirm": "string"
}
```

#### GET /logout
User logout endpoint.

### Books API (`/api/books`)

#### GET /api/books
Retrieve all books with pagination and filtering.
**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `search`: Search term
- `category`: Filter by category
- `language`: Filter by language
- `sort`: Sort order (title, year, id)

**Response:**
```json
{
    "data": [
        {
            "id": 1,
            "title": "Book Title",
            "publication_year": 2023,
            "authors": ["Author Name"],
            "categories": ["Category Name"],
            "languages": ["English"],
            "cover_id": "12345678"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "pages": 5,
        "has_prev": false,
        "has_next": true
    }
}
```

#### GET /api/books/{id}
Retrieve a specific book by ID.

#### POST /api/books
Create a new book.
```json
{
    "title": "Book Title",
    "publication_year": 2023,
    "authors": ["Author Name"],
    "categories": ["Category Name"],
    "languages": ["English"],
    "open_library_id": "OL123456M",
    "cover_id": "12345678"
}
```

#### PUT /api/books/{id}
Update an existing book.

#### DELETE /api/books/{id}
Delete a book.

### Authors API (`/api/authors`)

#### GET /api/authors
Retrieve all authors with book counts.

#### POST /api/authors
Create a new author.
```json
{
    "name": "Author Name",
    "image": "https://example.com/image.jpg"
}
```

#### PUT /api/authors/update/{id}
Update an existing author.

#### DELETE /api/authors/delete/{id}
Delete an author.

### Collections API (`/api/collections`)

#### GET /api/collections
Retrieve user collections.

#### POST /api/collections
Create a new collection.
```json
{
    "name": "Collection Name",
    "description": "Collection description"
}
```

#### PUT /api/collections/{id}
Update a collection.

#### DELETE /api/collections/{id}
Delete a collection.

### Search API (`/api/search`)

#### GET /api/search
Global search across books and authors.
**Query Parameters:**
- `q`: Search query
- `type`: Search type (books, authors, all)

---

## Frontend Components

### Home Page
- **Featured Books**: Highlighted book recommendations
- **Category Tabs**: Books organized by categories
- **Statistics**: Application usage statistics
- **Search Bar**: Quick search functionality

### Admin Dashboard
- **Statistics Overview**: System metrics and usage
- **CRUD Tables**: Manage books, authors, categories, users
- **Advanced Filtering**: Real-time search and filtering
- **Bulk Operations**: Import books from Open Library
- **User Management**: Admin user controls

### Book Management
- **Book Grid**: Responsive book display
- **Detail Views**: Comprehensive book information
- **Cover Images**: Open Library cover integration
- **Author Links**: Navigate to author pages

### Collection Management
- **Personal Collections**: User-specific book collections
- **Collection Builder**: Easy book addition/removal
- **Collection Statistics**: Track collection metrics
- **Sharing Controls**: Admin visibility settings

### Responsive Design
- **Mobile-First**: Optimized for mobile devices
- **Bootstrap Grid**: Responsive layout system
- **Touch-Friendly**: Mobile interaction optimization
- **Progressive Enhancement**: Works without JavaScript

---

## Security Features

### Authentication Security
- **bcrypt Hashing**: Secure password storage with salt
- **Session Management**: Secure session handling
- **CSRF Protection**: Cross-site request forgery prevention
- **XSS Prevention**: Input sanitization and output encoding

### Authorization
- **Role-Based Access**: Admin and user role separation
- **Route Protection**: Decorator-based access control
- **Resource Ownership**: Users can only edit their own collections
- **Admin Override**: Admins can access all resources

### Data Security
- **SQL Injection Prevention**: Parameterized queries only
- **Input Validation**: Server-side validation for all inputs
- **Error Handling**: Secure error messages without data leakage
- **Environment Separation**: Different configs for dev/prod

### Session Security
```python
# Production session configuration
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF protection
```

---

## Deployment

### Production Deployment

#### 1. Environment Setup
```bash
# Set production environment
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key
export DEBUG=False
```

#### 2. Database Configuration
```bash
# Production database setup
createdb books_manager_prod
psql books_manager_prod < database/seed/tabels_Init.sql
```

#### 3. Web Server Configuration (Nginx + Gunicorn)
```nginx
# Nginx configuration
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/books_manager/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4. Gunicorn Configuration
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 index:app
```

#### 5. SSL Configuration
```bash
# Using Let's Encrypt
certbot --nginx -d your-domain.com
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "index:app"]
```

### Environment Variables for Production
```env
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key
DEBUG=False
HOST=your-db-host
DB=books_manager_prod
USER=your-db-user
PASSWORD=your-db-password
```

---

## Development Guide

### Code Style
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations for better code clarity
- **Docstrings**: Document all functions and classes
- **Comments**: Explain complex logic and business rules

### Adding New Features

#### 1. Database Changes
```bash
# Create migration file
touch database/migration_add_new_feature.sql

# Update schema
psql books_manager < database/migration_add_new_feature.sql
```

#### 2. API Endpoints
```python
# Create new blueprint
from flask import Blueprint
new_api = Blueprint('new_api', __name__, url_prefix='/api/new')

@new_api.route('/', methods=['GET'])
def get_new_items():
    """Get all new items."""
    # Implementation here
    pass
```

#### 3. Frontend Components
```html
<!-- Create new template -->
{% extends "base.html" %}
{% block content %}
<!-- Component content -->
{% endblock %}
```

### Testing
```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/
```

### Database Management
```bash
# Backup database
pg_dump books_manager > backup.sql

# Restore database
psql books_manager < backup.sql

# Reset database
psql books_manager < database/seed/tabels_Init.sql
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U username -d books_manager
```

#### 2. Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies
pip install -r requirements.txt
```

#### 3. Permission Errors
```bash
# Fix file permissions
chmod +x index.py
chown -R www-data:www-data /path/to/app
```

#### 4. Session Issues
```python
# Clear browser cookies
# Check SECRET_KEY configuration
# Verify session cookie settings
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_authors_name ON authors(name);
CREATE INDEX idx_users_username ON users(username);
```

#### 2. Caching
```python
# Enable Redis caching (optional)
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

#### 3. Static File Optimization
```bash
# Compress static files
gzip -k static/css/*.css
gzip -k static/js/*.js
```

### Logging
```python
# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Monitoring
- **Application Logs**: Monitor error logs and access patterns
- **Database Performance**: Track slow queries and connection usage
- **System Resources**: Monitor CPU, memory, and disk usage
- **User Analytics**: Track user behavior and feature usage

---

## Support & Contributing

### Getting Help
- **Documentation**: Refer to this documentation first
- **Issues**: Check existing GitHub issues
- **Community**: Join our community discussions

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Review Process
- All changes require code review
- Tests must pass before merging
- Documentation must be updated
- Security implications must be considered

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Changelog

### Version 1.0.0
- Initial release
- Complete book management system
- User authentication and authorization
- Admin dashboard
- Open Library integration
- Collection management
- Search and filtering
- Responsive design

---

*Last updated: September 2025*
*Documentation version: 1.0.0*
