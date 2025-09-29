"""
Home Service - Business Logic for Home Page
==========================================

This service handles all business logic related to the home page functionality.
It organizes and processes data for the main landing page including:

- Book organization by categories
- Featured, popular, and latest book selection
- Statistics aggregation
- Error handling and fallback data

Key Features:
- Separation of concerns from route handlers
- Centralized home page data processing
- Error handling with graceful fallbacks
- Type hints for better maintainability

Author: Books Manager Team
Version: 1.0.0
"""

from typing import Dict, List, Any
from database.data_access import get_books_data, get_categories_data, get_authors_data, get_statistics


class HomeService:
    """Service class for home page business logic."""
    
    @staticmethod
    def organize_books_by_category(books: List[Dict[str, Any]], categories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize books by category for tabbed display."""
        books_by_category = {'all': list(books)}
        
        for category in categories:
            category_name = category['name']
            category_books = [book for book in books 
                             if book['categories'] and category_name in book['categories']]
            books_by_category[category_name] = category_books
        
        return books_by_category
    
    @staticmethod
    def get_home_data() -> Dict[str, Any]:
        """Get all data needed for the home page."""
        try:
            # Fetch all data
            books = get_books_data()
            categories = get_categories_data()
            authors = get_authors_data()
            stats = get_statistics()
            
            # Organize data for template
            featured_books = books[:6] if books else []
            popular_books = books[6:14] if len(books) > 6 else books
            latest_books = books[-8:] if len(books) >= 8 else books
            special_books = books[-5:] if len(books) >= 5 else books
            
            # Organize books by category
            books_by_category_data = HomeService.organize_books_by_category(books, categories)
            
            return {
                'books': books,
                'books_by_category': books_by_category_data,
                'featured_books': featured_books,
                'popular_books': popular_books,
                'latest_books': latest_books,
                'special_books': special_books,
                'stats': stats
            }
        except Exception as e:
            # Return empty data on error
            return {
                'books': [],
                'books_by_category': {},
                'featured_books': [],
                'popular_books': [],
                'latest_books': [],
                'special_books': [],
                'stats': {}
            }
