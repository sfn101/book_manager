from typing import Dict, List, Any, Optional, Tuple
from database import get_db
from database.data_access import fetch_books, count_books


class BooksService:
    """Service class for books listing and filtering business logic."""
    
    @staticmethod
    def build_filters_from_request(request_args: Dict[str, Any]) -> Dict[str, Any]:
        """Build filter dictionary from request arguments."""
        filters = {}
        
        search = request_args.get('search', '').strip()
        if search:
            filters['search'] = search
        
        category = request_args.get('category', '').strip()
        if category:
            filters['category'] = category
        
        language = request_args.get('language', '').strip()
        if language:
            filters['language'] = language
        
        return filters
    
    @staticmethod
    def get_sort_order(sort_by: str) -> str:
        """Get the appropriate sort order for the given sort parameter."""
        sort_mapping = {
            'title': 'title',
            'year': 'id',  # Will be handled by custom ORDER BY
            'year_asc': 'id',  # Will be handled by custom ORDER BY
            'title_desc': 'id'  # Will be handled by custom ORDER BY
        }
        return sort_mapping.get(sort_by, 'title')
    
    @staticmethod
    def get_books_page_data(page: int, per_page: int, filters: Dict[str, Any], sort_by: str) -> Dict[str, Any]:
        """Get paginated books data with filters and sorting."""
        try:
            # Calculate pagination
            offset = (page - 1) * per_page
            
            # Get total count
            total = count_books(filters)
            
            # Get books for current page
            pagination_params = {'limit': per_page, 'offset': offset}
            order = BooksService.get_sort_order(sort_by)
            
            books = fetch_books(filters, pagination_params, order)
            
            # Get filter options
            categories = BooksService._get_categories_for_filter()
            languages = BooksService._get_languages_for_filter()
            
            # Create pagination object
            pagination = BooksService._create_pagination_object(page, per_page, total)
            
            return {
                'books': books,
                'categories': categories,
                'languages': languages,
                'pagination': pagination,
                'current_filters': {
                    'search': filters.get('search', ''),
                    'category': filters.get('category', ''),
                    'language': filters.get('language', ''),
                    'sort': sort_by
                }
            }
        except Exception as e:
            return {
                'books': [],
                'categories': [],
                'languages': [],
                'pagination': None,
                'current_filters': {},
                'error': str(e)
            }
    
    @staticmethod
    def _get_categories_for_filter() -> List[Dict[str, Any]]:
        """Get categories for filter dropdown."""
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name FROM categories ORDER BY name")
                return cursor.fetchall()
    
    @staticmethod
    def _get_languages_for_filter() -> List[Dict[str, Any]]:
        """Get languages for filter dropdown."""
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name FROM languages ORDER BY name")
                return cursor.fetchall()
    
    @staticmethod
    def _create_pagination_object(page: int, per_page: int, total: int):
        """Create a pagination object."""
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
        
        return Pagination(page, per_page, total)
