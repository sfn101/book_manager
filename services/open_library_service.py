import requests
from typing import Optional, Dict, Any, List
from database import get_db
from util import normalize_strings

class OpenLibraryService:
    BASE_URL = "https://openlibrary.org"
    
    @staticmethod
    def search_book_by_title(title: str, limit: int = 1) -> Optional[Dict[Any, Any]]:
        """Search for a book by title using Open Library API."""
        try:
            url = f"{OpenLibraryService.BASE_URL}/search.json"
            params = {
                'title': title,
                'limit': limit 
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('docs') and len(data['docs']) > 0:
                books = []
                for book_data in data['docs']:
                    # Enhance book data with detailed work information
                    enhanced_book = OpenLibraryService._enhance_book_with_work_details(book_data)
                    books.append(enhanced_book)
                
                if limit == 1:
                    return books[0] if books else None
                else:
                    return books
            return None
            
        except requests.RequestException as e:
            print(f"Error fetching from Open Library: {e}")
            return None
    
    @staticmethod
    def _enhance_book_with_work_details(book_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Enhance book data by fetching detailed work information for subjects/categories."""
        try:
            work_key = book_data.get('key')
            if work_key:
                # Fetch detailed work information
                work_url = f"{OpenLibraryService.BASE_URL}{work_key}.json"
                work_response = requests.get(work_url, timeout=10)
                if work_response.status_code == 200:
                    work_data = work_response.json()
                    # Merge work details with search result
                    book_data.update({
                        'subjects': work_data.get('subjects', []),
                        'covers': work_data.get('covers', [])
                    })
        except requests.RequestException as e:
            print(f"Warning: Could not fetch work details: {e}")
        
        # Format the enhanced data
        return OpenLibraryService._format_book_data(book_data)
    
    @staticmethod
    def get_book_by_id(open_library_id: str) -> Optional[Dict[Any, Any]]:
        """Get book details by Open Library ID."""
        try:
            url = f"{OpenLibraryService.BASE_URL}/books/{open_library_id}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return OpenLibraryService._format_book_data(response.json())
            
        except requests.RequestException as e:
            print(f"Error fetching from Open Library: {e}")
            return None
    
    @staticmethod
    def _format_book_data(raw_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Format Open Library data to match our database schema."""
        # Extract cover ID from different possible fields
        cover_id = None
        if raw_data.get('cover_i'):  # Most common field in search results
            cover_id = raw_data.get('cover_i')
        elif raw_data.get('covers') and len(raw_data.get('covers', [])) > 0:
            cover_id = raw_data['covers'][0]
        elif raw_data.get('cover_edition_key'):
            cover_id = raw_data.get('cover_edition_key')
        
        # Get all authors, not just the first one
        authors = raw_data.get('author_name', [])
        if not authors and raw_data.get('author'):
            authors = [raw_data.get('author')]
        
        # Get categories/subjects from work details if available
        categories = []
        subjects = raw_data.get('subjects', [])
        if subjects:
            # Filter and clean subjects to get meaningful categories
            categories = []
            for subject in subjects[:10]:  # Limit to first 10 subjects
                subject = subject.strip()
                # Filter out very specific or meta subjects
                if (len(subject) > 2 and len(subject) < 50 and 
                    not subject.startswith('Reading Level') and
                    not subject.startswith('nyt:') and
                    not 'fiction' in subject.lower() or subject.lower() in ['fiction', 'juvenile fiction']):
                    categories.append(subject)
        
        # Get languages - clean and limit
        languages = raw_data.get('language', [])
        if languages:
            # Convert language codes to full names where possible
            lang_map = {
                'eng': 'English', 'fre': 'French', 'ger': 'German', 'spa': 'Spanish',
                'ita': 'Italian', 'por': 'Portuguese', 'rus': 'Russian', 'jpn': 'Japanese',
                'chi': 'Chinese', 'ara': 'Arabic', 'hin': 'Hindi', 'ben': 'Bengali'
            }
            languages = [lang_map.get(lang, lang) for lang in languages[:5]]  # Limit to 5 languages
        else:
            languages = ['English']  # Default to English
        
        return {
            'title': raw_data.get('title', ''),
            'authors': authors,  # Return all authors as array
            'author': authors[0] if authors else '',  # Keep single author for backward compatibility
            'categories': categories,  # Return categories as array
            'publication_year': raw_data.get('first_publish_year'),
            'cover_id': cover_id,
            'languages': languages,  # Return all languages as array
            'language': languages[0] if languages else 'English',  # Keep single language for backward compatibility
            'open_library_id': raw_data.get('key', '').replace('/works/', '') if raw_data.get('key') else None
        }
    
    @staticmethod
    def get_cover_url(cover_id: int, size: str = 'M') -> Optional[str]:
        """Generate cover image URL from cover ID."""
        if not cover_id:
            return None
        # Size options: S (small), M (medium), L (large)
        return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"
    
    @staticmethod
    def verify_cover_exists(cover_id: int) -> bool:
        """Verify if a cover image exists by making a HEAD request."""
        if not cover_id:
            return False
        
        try:
            cover_url = OpenLibraryService.get_cover_url(cover_id, 'L')
            if not cover_url:
                return False
                
            response = requests.head(cover_url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    @staticmethod
    def find_missing_covers():
        """Find all books in database that are missing cover images."""
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            books.id,
                            books.title,
                            books.cover_id,
                            books.open_library_id,
                            COALESCE(
                                ARRAY_AGG(DISTINCT authors.name) FILTER (WHERE authors.name IS NOT NULL), 
                                ARRAY[]::text[]
                            ) AS authors
                        FROM books
                        LEFT JOIN book_authors ON books.id = book_authors.book_id
                        LEFT JOIN authors ON book_authors.author_id = authors.id
                        WHERE books.cover_id IS NULL OR books.cover_id = ''
                        GROUP BY books.id, books.title, books.cover_id, books.open_library_id
                        ORDER BY books.id
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error finding missing covers: {e}")
            return []
    
    @staticmethod
    def update_book_cover(book_id: int, cover_id: str) -> bool:
        """Update a book's cover ID in the database."""
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE books SET cover_id = %s WHERE id = %s",
                        (cover_id, book_id)
                    )
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating book cover for book {book_id}: {e}")
            return False
    
    @staticmethod
    def fetch_and_update_missing_covers() -> Dict[str, int]:
        """Find books missing covers and try to fetch them from Open Library."""
        results = {
            'processed': 0,
            'updated': 0,
            'not_found': 0,
            'errors': 0
        }
        
        missing_covers = OpenLibraryService.find_missing_covers()
        print(f"Found {len(missing_covers)} books missing covers")
        
        for book in missing_covers:
            results['processed'] += 1
            book_id = book['id']
            title = book['title']
            authors = book['authors']
            
            print(f"Processing book {book_id}: {title}")
            
            try:
                # Try to find the book on Open Library
                search_result = OpenLibraryService.search_book_by_title(title)
                
                if search_result and search_result.get('cover_id'):
                    cover_id = search_result['cover_id']
                    
                    # Verify the cover exists
                    if OpenLibraryService.verify_cover_exists(cover_id):
                        # Update the database
                        if OpenLibraryService.update_book_cover(book_id, str(cover_id)):
                            results['updated'] += 1
                            print(f"✓ Updated cover for: {title}")
                        else:
                            results['errors'] += 1
                            print(f"✗ Failed to update database for: {title}")
                    else:
                        results['not_found'] += 1
                        print(f"- Cover not available for: {title}")
                else:
                    results['not_found'] += 1
                    print(f"- No Open Library match found for: {title}")
                    
            except Exception as e:
                results['errors'] += 1
                print(f"✗ Error processing {title}: {e}")
        
        return results
    
    @staticmethod
    def import_books_from_search(query: str, limit: int = 10) -> Dict[str, Any]:
        """Search Open Library and import multiple books to database."""
        results = {
            'searched': 0,
            'imported': 0,
            'duplicates': 0,
            'errors': 0,
            'books': []
        }
        
        try:
            # Search for multiple books
            search_results = OpenLibraryService.search_book_by_title(query, limit=limit)
            
            if not search_results:
                return results
            
            # Ensure it's a list
            if not isinstance(search_results, list):
                search_results = [search_results]
            
            results['searched'] = len(search_results)
            
            for book_data in search_results:
                try:
                    book_id = OpenLibraryService._import_single_book(book_data)
                    if book_id == -1:  # Duplicate
                        results['duplicates'] += 1
                    elif book_id > 0:  # Success
                        results['imported'] += 1
                        results['books'].append(book_id)
                    else:  # Error
                        results['errors'] += 1
                        
                except Exception as e:
                    results['errors'] += 1
                    print(f"Error importing book: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error in bulk import: {e}")
            results['errors'] = 1
            return results
    
    @staticmethod
    def _import_single_book(book_data: Dict[str, Any]) -> int:
        """Import a single book to database. Returns book_id on success, -1 for duplicate, 0 for error."""
        title = normalize_strings(book_data.get('title'))
        author = normalize_strings(book_data.get('author'))
        language = normalize_strings(book_data.get('language'))
        open_library_id = book_data.get('open_library_id')
        publication_year = book_data.get('publication_year')
        cover_id = book_data.get('cover_id')

        if not title:
            print("No title provided")
            return 0
        
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    # Check if book already exists
                    cursor.execute(
                        "SELECT id FROM books WHERE LOWER(title) = %s OR open_library_id = %s",
                        (title.lower(), open_library_id)
                    )
                    existing_book = cursor.fetchone()
                    
                    if existing_book:
                        print(f"Book already exists: {title}")
                        return -1  # Duplicate
                    
                    # Insert book
                    cursor.execute(
                        "INSERT INTO books (title, publication_year, open_library_id, cover_id) VALUES (%s, %s, %s, %s) RETURNING id",
                        (title, publication_year, open_library_id, str(cover_id) if cover_id else None)
                    )
                    new_book_id = cursor.fetchone()["id"]
                    
                    # Handle language if provided
                    if language:
                        cursor.execute("SELECT id FROM languages WHERE LOWER(name) = %s", (language.lower(),))
                        language_result = cursor.fetchone()
                        if language_result:
                            language_id = language_result["id"]
                        else:
                            cursor.execute("INSERT INTO languages (name) VALUES (%s) RETURNING id", (language,))
                            language_id = cursor.fetchone()["id"]
                        
                        cursor.execute("INSERT INTO book_languages (book_id, language_id) VALUES (%s, %s)", (new_book_id, language_id))
                    
                    # Handle author if provided
                    if author:
                        cursor.execute("SELECT id FROM authors WHERE LOWER(name) = %s", (author.lower(),))
                        author_result = cursor.fetchone()
                        if author_result:
                            author_id = author_result["id"]
                        else:
                            cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id", (author,))
                            author_id = cursor.fetchone()["id"]
                        
                        cursor.execute("INSERT INTO book_authors (book_id, author_id) VALUES (%s, %s)", (new_book_id, author_id))

                    print(f"✓ Imported: {title}")
                    return new_book_id

        except Exception as e:
            print(f"Error importing {title}: {e}")
            return 0
    
    @staticmethod
    def get_books_without_covers() -> List[Dict[str, Any]]:
        """Get all books that don't have cover images for dashboard display."""
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            books.id,
                            books.title,
                            books.publication_year,
                            books.open_library_id,
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
                        WHERE books.cover_id IS NULL OR books.cover_id = ''
                        GROUP BY books.id, books.title, books.publication_year, books.open_library_id
                        ORDER BY books.title
                        LIMIT 50
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error getting books without covers: {e}")
            return []
    
    # Author Image Management Methods
    @staticmethod
    def search_author_by_name(author_name: str) -> Optional[Dict[str, Any]]:
        """Search for an author by name using Open Library API."""
        try:
            url = f"{OpenLibraryService.BASE_URL}/search/authors.json"
            params = {
                'q': author_name,
                'limit': 1
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('docs') and len(data['docs']) > 0:
                return OpenLibraryService._format_author_data(data['docs'][0])
            return None
            
        except requests.RequestException as e:
            print(f"Error fetching author from Open Library: {e}")
            return None

    @staticmethod
    def _format_author_data(raw_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Format Open Library author data."""
        # Extract OLID (Open Library ID) from key field
        # In search results, key is directly the OLID like 'OL229501A'
        # In author detail pages, key might be '/authors/OL229501A'
        olid = None
        if raw_data.get('key'):
            key = raw_data.get('key', '')
            if key.startswith('/authors/'):
                olid = key.replace('/authors/', '')
            else:
                # Direct OLID from search results
                olid = key
        
        return {
            'name': raw_data.get('name', ''),
            'birth_date': raw_data.get('birth_date'),
            'death_date': raw_data.get('death_date'),
            'bio': raw_data.get('bio', ''),
            'olid': olid,
            'open_library_key': olid
        }

    @staticmethod
    def get_author_image_url(olid: str, size: str = 'M') -> Optional[str]:
        """Generate author image URL from OLID (Open Library ID)."""
        if not olid:
            return None
        # Size options: S (small), M (medium), L (large)
        # URL Pattern: https://covers.openlibrary.org/a/olid/OL229501A-S.jpg
        return f"https://covers.openlibrary.org/a/olid/{olid}-{size}.jpg"

    @staticmethod
    def verify_author_image_exists(olid: str) -> bool:
        """Verify if an author image exists by making a HEAD request."""
        if not olid:
            return False
        
        try:
            image_url = OpenLibraryService.get_author_image_url(olid, 'L')
            if not image_url:
                return False
                
            response = requests.head(image_url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @staticmethod
    def find_authors_missing_images():
        """Find all authors in database that are missing profile images."""
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            authors.id,
                            authors.name,
                            authors.image_url,
                            COUNT(books.id) as book_count
                        FROM authors
                        LEFT JOIN book_authors ON authors.id = book_authors.author_id
                        LEFT JOIN books ON book_authors.book_id = books.id
                        WHERE authors.image_url IS NULL OR authors.image_url = ''
                        GROUP BY authors.id, authors.name, authors.image_url
                        ORDER BY book_count DESC, authors.name
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error finding authors missing images: {e}")
            return []

    @staticmethod
    def update_author_image(author_id: int, image_url: str) -> bool:
        """Update an author's image URL in the database."""
        try:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE authors SET image_url = %s WHERE id = %s",
                        (image_url, author_id)
                    )
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating author image for author {author_id}: {e}")
            return False

    @staticmethod
    def fetch_and_update_missing_author_images() -> Dict[str, int]:
        """Find authors missing images and try to fetch them from Open Library."""
        results = {
            'processed': 0,
            'updated': 0,
            'not_found': 0,
            'errors': 0
        }
        
        missing_images = OpenLibraryService.find_authors_missing_images()
        print(f"Found {len(missing_images)} authors missing images")
        
        for author in missing_images:
            results['processed'] += 1
            author_id = author['id']
            author_name = author['name']
            
            print(f"Processing author {author_id}: {author_name}")
            
            try:
                # Try to find the author on Open Library
                search_result = OpenLibraryService.search_author_by_name(author_name)
                
                if search_result and search_result.get('olid'):
                    olid = search_result['olid']
                    
                    # Verify the image exists
                    if OpenLibraryService.verify_author_image_exists(olid):
                        # Update the database
                        if OpenLibraryService.update_author_image(author_id, olid):
                            results['updated'] += 1
                            print(f"✓ Updated image for: {author_name} (OLID: {olid})")
                        else:
                            results['errors'] += 1
                            print(f"✗ Failed to update database for: {author_name}")
                    else:
                        results['not_found'] += 1
                        print(f"- Image not available for: {author_name} (OLID: {olid})")
                else:
                    results['not_found'] += 1
                    print(f"- No Open Library match found for: {author_name}")
                    
            except Exception as e:
                results['errors'] += 1
                print(f"✗ Error processing {author_name}: {e}")
        
        return results
    
    @staticmethod
    def get_book_cover_by_isbn(isbn: str) -> Optional[str]:
        """Get book cover URL by ISBN"""
        try:
            # Clean the ISBN
            isbn = isbn.replace('-', '').replace(' ', '')
            
            # Try Open Library Covers API with ISBN
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
            
            # Verify the cover exists
            response = requests.head(cover_url, timeout=5)
            if response.status_code == 200:
                return cover_url
            
            return None
            
        except requests.RequestException:
            return None
    
    @staticmethod
    def get_book_cover_by_title_author(title: str, author: str) -> Optional[str]:
        """Get book cover URL by searching with title and author"""
        try:
            # Search for the book
            url = f"{OpenLibraryService.BASE_URL}/search.json"
            params = {
                'title': title,
                'author': author,
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('docs') and len(data['docs']) > 0:
                book = data['docs'][0]
                
                # Get cover ID if available
                if book.get('cover_i'):
                    cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
                    
                    # Verify the cover exists
                    cover_response = requests.head(cover_url, timeout=5)
                    if cover_response.status_code == 200:
                        return cover_url
                
                # Try with ISBN if available
                if book.get('isbn'):
                    for isbn in book['isbn'][:3]:  # Try first 3 ISBNs
                        cover_url = OpenLibraryService.get_book_cover_by_isbn(isbn)
                        if cover_url:
                            return cover_url
            
            return None
            
        except requests.RequestException:
            return None