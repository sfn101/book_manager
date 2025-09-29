#!/usr/bin/env python3
"""
Standalone Database Reset and Population Script
===============================================

This script will:
1. Clear all data from the database while preserving table structure
2. Reset all primary key sequences
3. Fetch 100 books from Open Library with all necessary data
4. Create 4 fake users
5. Populate all tables with proper relationships
6. Create collections for each user with multiple books

Usage: python reset_and_populate_db.py
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import time
from typing import Dict, List, Any, Optional

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT', 5432)),
            'database': os.getenv('DB'),
            'user': os.getenv('USER'),
            'password': os.getenv('PASSWORD')
        }
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.conn_params)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query with proper connection handling"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall() if cursor.description else None
                return cursor.rowcount
    
    def clear_all_data(self):
        """Clear all data from all tables while preserving structure"""
        print("🗑️  Clearing all data from database...")
        
        # Clear all tables in the correct order (respect foreign keys)
        queries = [
            "DELETE FROM collection_books;",
            "DELETE FROM book_categories;", 
            "DELETE FROM book_authors;",
            "DELETE FROM book_languages;",
            "DELETE FROM books;",
            "DELETE FROM collections;",
            "DELETE FROM categories;",
            "DELETE FROM authors;",
            "DELETE FROM languages;",
            "DELETE FROM users;",
        ]
        
        for query in queries:
            try:
                self.execute_query(query)
                print(f"✅ Executed: {query.strip()}")
            except Exception as e:
                print(f"❌ Error executing {query}: {e}")
                continue
    
    def reset_sequences(self):
        """Reset all primary key sequences"""
        print("🔄 Resetting primary key sequences...")
        
        sequences = [
            "ALTER SEQUENCE authors_id_seq RESTART WITH 1;",
            "ALTER SEQUENCE books_id_seq RESTART WITH 1;", 
            "ALTER SEQUENCE categories_id_seq RESTART WITH 1;",
            "ALTER SEQUENCE collections_id_seq RESTART WITH 1;",
            "ALTER SEQUENCE languages_id_seq RESTART WITH 1;",
            "ALTER SEQUENCE users_id_seq RESTART WITH 1;"
        ]
        
        for query in sequences:
            try:
                self.execute_query(query)
                print(f"✅ Reset: {query.strip()}")
            except Exception as e:
                print(f"❌ Error resetting sequence: {e}")

class OpenLibraryFetcher:
    """Handles fetching data from Open Library API"""
    
    BASE_URL = "https://openlibrary.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Books Manager Database Seeder/1.0'
        })
    
    def search_books(self, subjects: List[str], books_per_subject: int = 20) -> List[Dict]:
        """Search for books across multiple subjects"""
        print(f"📚 Fetching books from Open Library...")
        
        all_books = []
        
        for subject in subjects:
            print(f"  🔍 Searching subject: {subject}")
            try:
                # Search by subject
                url = f"{self.BASE_URL}/subjects/{subject}.json"
                params = {
                    'limit': books_per_subject,
                    'offset': 0,
                    'details': 'true'
                }
                
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                works = data.get('works', [])
                print(f"    Found {len(works)} books in {subject}")
                
                for work in works:
                    book_data = self._process_work(work)
                    if book_data and book_data.get('title'):
                        all_books.append(book_data)
                        if len(all_books) >= 120:  # Get extra in case some fail
                            break
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    ❌ Error fetching {subject}: {e}")
                continue
            
            if len(all_books) >= 120:
                break
        
        print(f"📖 Total books collected: {len(all_books)}")
        return all_books[:100]  # Return exactly 100 books
    
    def _process_work(self, work: Dict) -> Optional[Dict]:
        """Process a work from Open Library and enhance with details"""
        try:
            # Basic work information
            work_key = work.get('key', '')
            title = work.get('title', '').strip()
            
            if not title:
                return None
            
            # Get detailed work information
            details = self._get_work_details(work_key)
            
            # Get first edition for publication info
            first_edition = self._get_first_edition(work_key)
            
            processed_book = {
                'title': title,
                'authors': self._extract_authors(work, details),
                'categories': self._extract_subjects(work, details),
                'languages': self._extract_languages(first_edition),
                'publication_year': self._extract_publication_year(work, first_edition),
                'cover_id': self._extract_cover_id(work, details, first_edition),
                'open_library_id': work_key.replace('/works/', '') if work_key else None
            }
            
            return processed_book
            
        except Exception as e:
            print(f"      ⚠️ Error processing work: {e}")
            return None
    
    def _get_work_details(self, work_key: str) -> Dict:
        """Get detailed information about a work"""
        try:
            url = f"{self.BASE_URL}{work_key}.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return {}
    
    def _get_first_edition(self, work_key: str) -> Dict:
        """Get the first edition of a work for publication details"""
        try:
            url = f"{self.BASE_URL}{work_key}/editions.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            editions = data.get('entries', [])
            if editions:
                # Return the first edition details
                edition_key = editions[0].get('key', '')
                if edition_key:
                    edition_url = f"{self.BASE_URL}{edition_key}.json"
                    edition_response = self.session.get(edition_url, timeout=10)
                    edition_response.raise_for_status()
                    return edition_response.json()
            
            return {}
        except:
            return {}
    
    def _extract_authors(self, work: Dict, details: Dict) -> List[str]:
        """Extract author names"""
        authors = []
        
        # Try work authors first
        work_authors = work.get('authors', [])
        if work_authors:
            for author in work_authors:
                if isinstance(author, dict) and author.get('name'):
                    authors.append(author['name'].strip())
        
        # Try detailed authors
        if not authors and details.get('authors'):
            for author in details.get('authors', []):
                if isinstance(author, dict):
                    author_key = author.get('author', {}).get('key', '')
                    if author_key:
                        author_name = self._get_author_name(author_key)
                        if author_name:
                            authors.append(author_name)
        
        return authors[:3] if authors else ['Unknown Author']  # Limit to 3 authors
    
    def _get_author_name(self, author_key: str) -> Optional[str]:
        """Get author name from author key"""
        try:
            url = f"{self.BASE_URL}{author_key}.json"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            author_data = response.json()
            return author_data.get('name', '').strip()
        except:
            return None
    
    def _extract_subjects(self, work: Dict, details: Dict) -> List[str]:
        """Extract and clean subjects/categories"""
        subjects = set()
        
        # Get subjects from work and details
        for source in [work, details]:
            work_subjects = source.get('subjects', [])
            if work_subjects:
                subjects.update(work_subjects)
        
        # Clean and filter subjects
        cleaned_subjects = []
        for subject in subjects:
            if isinstance(subject, str):
                subject = subject.strip()
                # Filter out unwanted subjects
                if (len(subject) > 2 and len(subject) < 50 and
                    not subject.startswith('Reading Level') and
                    not subject.startswith('nyt:') and
                    not subject.startswith('Times reviewed') and
                    not 'accessible book' in subject.lower() and
                    not 'protected daisy' in subject.lower()):
                    cleaned_subjects.append(subject)
        
        return cleaned_subjects[:5] if cleaned_subjects else ['General']  # Limit to 5
    
    def _extract_languages(self, edition: Dict) -> List[str]:
        """Extract languages"""
        languages = []
        
        if edition.get('languages'):
            for lang in edition['languages']:
                if isinstance(lang, dict) and lang.get('key'):
                    lang_code = lang['key'].split('/')[-1]
                    lang_name = self._language_code_to_name(lang_code)
                    if lang_name:
                        languages.append(lang_name)
        
        return languages[:3] if languages else ['English']  # Default to English
    
    def _language_code_to_name(self, code: str) -> str:
        """Convert language code to name"""
        lang_map = {
            'eng': 'English', 'fre': 'French', 'ger': 'German', 'spa': 'Spanish',
            'ita': 'Italian', 'por': 'Portuguese', 'rus': 'Russian', 'jpn': 'Japanese',
            'chi': 'Chinese', 'ara': 'Arabic', 'hin': 'Hindi', 'ben': 'Bengali',
            'dut': 'Dutch', 'kor': 'Korean', 'pol': 'Polish', 'swe': 'Swedish',
            'nor': 'Norwegian', 'dan': 'Danish', 'fin': 'Finnish', 'gre': 'Greek'
        }
        return lang_map.get(code, code.capitalize())
    
    def _extract_publication_year(self, work: Dict, edition: Dict) -> Optional[int]:
        """Extract publication year"""
        # Try first_publish_date from work
        if work.get('first_publish_date'):
            try:
                date_str = work['first_publish_date']
                if len(date_str) >= 4 and date_str[:4].isdigit():
                    return int(date_str[:4])
            except:
                pass
        
        # Try publish_date from edition
        if edition.get('publish_date'):
            try:
                date_str = edition['publish_date']
                if len(date_str) >= 4 and date_str[:4].isdigit():
                    return int(date_str[:4])
            except:
                pass
        
        # Random year between 1950 and 2023
        return random.randint(1950, 2023)
    
    def _extract_cover_id(self, work: Dict, details: Dict, edition: Dict) -> Optional[str]:
        """Extract cover ID"""
        # Try covers from various sources
        for source in [details, edition, work]:
            if source.get('covers'):
                covers = source['covers']
                if covers and isinstance(covers, list) and covers[0]:
                    return str(covers[0])
        
        return None

class DataPopulator:
    """Handles populating the database with fetched data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_fake_users(self) -> List[int]:
        """Create 4 fake users"""
        print("👤 Creating fake users...")
        
        users_data = [
            {
                'username': 'alice_reader',
                'email': 'alice@example.com',
                'password_hash': generate_password_hash('password123'),
                'role': 'admin'
            },
            {
                'username': 'bob_bookworm',
                'email': 'bob@example.com', 
                'password_hash': generate_password_hash('password123'),
                'role': 'user'
            },
            {
                'username': 'carol_critic',
                'email': 'carol@example.com',
                'password_hash': generate_password_hash('password123'),
                'role': 'user'
            },
            {
                'username': 'david_scholar',
                'email': 'david@example.com',
                'password_hash': generate_password_hash('password123'),
                'role': 'user'
            }
        ]
        
        user_ids = []
        for user_data in users_data:
            query = """
                INSERT INTO users (username, email, password_hash, role, created_at)
                VALUES (%(username)s, %(email)s, %(password_hash)s, %(role)s, NOW())
                RETURNING id;
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, user_data)
                    user_id = cursor.fetchone()[0]
                    user_ids.append(user_id)
                    print(f"✅ Created user: {user_data['username']} (ID: {user_id})")
        
        return user_ids
    
    def populate_books(self, books_data: List[Dict]) -> List[int]:
        """Populate books and related data"""
        print("📚 Populating books and related data...")
        
        # Create lookup dictionaries
        authors_map = {}  # name -> id
        categories_map = {}  # name -> id
        languages_map = {}  # name -> id
        book_ids = []
        
        for i, book_data in enumerate(books_data, 1):
            print(f"  📖 Processing book {i}/{len(books_data)}: {book_data['title'][:50]}...")
            
            try:
                # Handle authors
                author_ids = []
                for author_name in book_data['authors']:
                    author_name = author_name.strip()
                    if author_name not in authors_map:
                        author_id = self._insert_author(author_name)
                        authors_map[author_name] = author_id
                    author_ids.append(authors_map[author_name])
                
                # Handle categories
                category_ids = []
                for category_name in book_data['categories']:
                    category_name = category_name.strip()
                    if category_name not in categories_map:
                        category_id = self._insert_category(category_name)
                        categories_map[category_name] = category_id
                    category_ids.append(categories_map[category_name])
                
                # Handle languages
                language_ids = []
                for language_name in book_data['languages']:
                    language_name = language_name.strip()
                    if language_name not in languages_map:
                        language_id = self._insert_language(language_name)
                        languages_map[language_name] = language_id
                    language_ids.append(languages_map[language_name])
                
                # Insert book
                book_id = self._insert_book(
                    title=book_data['title'],
                    publication_year=book_data['publication_year'],
                    cover_id=book_data['cover_id'],
                    open_library_id=book_data['open_library_id']
                )
                
                if book_id:
                    book_ids.append(book_id)
                    
                    # Create relationships
                    self._create_book_relationships(book_id, author_ids, category_ids, language_ids)
                
            except Exception as e:
                print(f"    ❌ Error processing book: {e}")
                continue
        
        print(f"✅ Successfully created {len(book_ids)} books")
        return book_ids
    
    def _insert_author(self, name: str) -> int:
        """Insert author and return ID"""
        query = """
            INSERT INTO authors (name) 
            VALUES (%s) 
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name,))
                return cursor.fetchone()[0]
    
    def _insert_category(self, name: str) -> int:
        """Insert category and return ID"""
        query = """
            INSERT INTO categories (name) 
            VALUES (%s) 
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name,))
                return cursor.fetchone()[0]
    
    def _insert_language(self, name: str) -> int:
        """Insert language and return ID"""
        query = """
            INSERT INTO languages (name) 
            VALUES (%s) 
            RETURNING id;
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (name,))
                return cursor.fetchone()[0]
    
    def _insert_book(self, title: str, publication_year: int, cover_id: str, open_library_id: str) -> int:
        """Insert book and return ID"""
        query = """
            INSERT INTO books (title, publication_year, cover_id, open_library_id, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id;
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (title, publication_year, cover_id, open_library_id))
                return cursor.fetchone()[0]
    
    def _create_book_relationships(self, book_id: int, author_ids: List[int], 
                                 category_ids: List[int], language_ids: List[int]):
        """Create all book relationships"""
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Book-Authors
                for author_id in author_ids:
                    cursor.execute(
                        "INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (book_id, author_id)
                    )
                
                # Book-Categories
                for category_id in category_ids:
                    cursor.execute(
                        "INSERT INTO book_categories (book_id, category_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (book_id, category_id)
                    )
                
                # Book-Languages
                for language_id in language_ids:
                    cursor.execute(
                        "INSERT INTO book_languages (book_id, language_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (book_id, language_id)
                    )
    
    def create_collections(self, user_ids: List[int], book_ids: List[int]):
        """Create collections for each user with multiple books"""
        print("📁 Creating user collections...")
        
        collection_types = [
            'Favorites', 'Currently Reading', 'Want to Read', 'Classics',
            'Science Fiction', 'Mystery & Thriller', 'Romance', 'History',
            'Biography', 'Self-Help', 'Fiction', 'Non-Fiction'
        ]
        
        for user_id in user_ids:
            # Create 2-4 collections per user
            num_collections = random.randint(2, 4)
            selected_types = random.sample(collection_types, num_collections)
            
            for collection_type in selected_types:
                # Create collection
                query = """
                    INSERT INTO collections (name, description, user_id, created_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """
                
                description = f"My {collection_type} collection"
                created_at = datetime.now() - timedelta(days=random.randint(1, 365))
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query, (collection_type, description, user_id, created_at))
                        collection_id = cursor.fetchone()[0]
                        
                        # Add 3-10 random books to each collection
                        num_books = random.randint(3, 10)
                        selected_books = random.sample(book_ids, min(num_books, len(book_ids)))
                        
                        for book_id in selected_books:
                            added_at = created_at + timedelta(days=random.randint(0, 30))
                            cursor.execute(
                                "INSERT INTO collection_books (collection_id, book_id, added_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                (collection_id, book_id, added_at)
                            )
                        
                        print(f"  ✅ Created '{collection_type}' for user {user_id} with {len(selected_books)} books")

def main():
    """Main function to orchestrate the database reset and population"""
    print("🚀 Starting Database Reset and Population Script")
    print("=" * 60)
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        fetcher = OpenLibraryFetcher()
        populator = DataPopulator(db_manager)
        
        # Step 1: Clear existing data
        db_manager.clear_all_data()
        
        # Step 2: Reset sequences
        db_manager.reset_sequences()
        
        # Step 3: Create fake users
        user_ids = populator.create_fake_users()
        
        # Step 4: Fetch books from Open Library
        subjects = [
            'science_fiction', 'mystery', 'romance', 'biography', 'history',
            'philosophy', 'psychology', 'business', 'health', 'cooking',
            'art', 'music', 'travel', 'technology', 'education'
        ]
        
        books_data = fetcher.search_books(subjects, books_per_subject=8)
        
        if not books_data:
            print("❌ No books were fetched from Open Library!")
            return
        
        # Step 5: Populate books and related data
        book_ids = populator.populate_books(books_data)
        
        # Step 6: Create collections
        populator.create_collections(user_ids, book_ids)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 Database Reset and Population Complete!")
        print(f"✅ Users created: {len(user_ids)}")
        print(f"✅ Books imported: {len(book_ids)}")
        print("\nFake Users (password: password123):")
        print("  - alice_reader (admin)")
        print("  - bob_bookworm (user)")
        print("  - carol_critic (user)")
        print("  - david_scholar (user)")
        print("\nYou can now log in to the application with any of these users!")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)