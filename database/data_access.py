"""
Database Data Access Layer
=========================

This module provides data access functions for the Books Manager application.
It handles all database operations including:

- Book data retrieval with related entities (authors, categories, languages)
- Category and author data management
- Statistics calculation with caching
- Filtered book queries with pagination
- Optimized database queries to prevent N+1 problems

Key Features:
- Centralized query functions to avoid duplication
- LRU caching for frequently accessed data
- Type hints for better code maintainability
- Parameterized queries for security

Author: Books Manager Team
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional, Tuple
from database import get_db
import time
from functools import lru_cache


# =============================================================================
# BASE QUERY FUNCTIONS
# =============================================================================

def _get_books_base_query() -> str:
	"""
	Get the base SQL query for fetching books with all related data.
	
	This query joins books with their related entities (authors, categories, languages)
	and aggregates them into arrays for efficient data retrieval.
	
	Returns:
		str: SQL query string for book data with related entities
	"""
	return """
		SELECT 
		       b.id,
		       b.title,
		       b.publication_year,
		       b.open_library_id,
		       b.cover_id,
		       COALESCE(ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), ARRAY[]::text[]) AS categories,
		       COALESCE(ARRAY_AGG(DISTINCT l.name) FILTER (WHERE l.name IS NOT NULL), ARRAY[]::text[]) AS languages,
		       COALESCE(ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), ARRAY[]::text[]) AS authors
		FROM books b
		LEFT JOIN book_languages bl ON b.id = bl.book_id
		LEFT JOIN languages l ON bl.language_id = l.id
		LEFT JOIN book_authors ba ON b.id = ba.book_id
		LEFT JOIN authors a ON ba.author_id = a.id
		LEFT JOIN book_categories bc ON b.id = bc.book_id
		LEFT JOIN categories c ON bc.category_id = c.id
		GROUP BY b.id, b.title, b.publication_year, b.open_library_id, b.cover_id
	"""

def get_books_data() -> List[Dict[str, Any]]:
	"""Fetch books data with aggregated authors, categories, and languages."""
	with get_db() as conn:
		with conn.cursor() as cursor:
			cursor.execute(_get_books_base_query() + " ORDER BY b.id")
			return cursor.fetchall()

def get_book_by_id(book_id: int) -> Optional[Dict[str, Any]]:
	"""Fetch a single book by ID with all related data."""
	with get_db() as conn:
		with conn.cursor() as cursor:
			cursor.execute("""
				SELECT 
				       b.id,
				       b.title,
				       b.publication_year,
				       b.open_library_id,
				       b.cover_id,
				       COALESCE(ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), ARRAY[]::text[]) AS categories,
				       COALESCE(ARRAY_AGG(DISTINCT l.name) FILTER (WHERE l.name IS NOT NULL), ARRAY[]::text[]) AS languages,
				       COALESCE(ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), ARRAY[]::text[]) AS authors
				FROM books b
				LEFT JOIN book_languages bl ON b.id = bl.book_id
				LEFT JOIN languages l ON bl.language_id = l.id
				LEFT JOIN book_authors ba ON b.id = ba.book_id
				LEFT JOIN authors a ON ba.author_id = a.id
				LEFT JOIN book_categories bc ON b.id = bc.book_id
				LEFT JOIN categories c ON bc.category_id = c.id
				WHERE b.id = %s
				GROUP BY b.id, b.title, b.publication_year, b.open_library_id, b.cover_id
			""", (book_id,))
			return cursor.fetchone()


def get_categories_data() -> List[Dict[str, Any]]:
	"""Fetch categories list ordered by name."""
	with get_db() as conn:
		with conn.cursor() as cursor:
			cursor.execute("SELECT * FROM categories ORDER BY name")
			return cursor.fetchall()


def get_authors_data() -> List[Dict[str, Any]]:
	"""Fetch authors with their book counts and titles."""
	with get_db() as conn:
		with conn.cursor() as cursor:
			cursor.execute(
				"""
				SELECT 
					authors.id, 
					authors.name,
					authors.image_url,
					COUNT(books.id) as book_count,
					COALESCE(ARRAY_AGG(books.title) FILTER (WHERE books.title IS NOT NULL), ARRAY[]::text[]) as book_titles
				FROM authors
				LEFT JOIN book_authors ON authors.id = book_authors.author_id
				LEFT JOIN books ON book_authors.book_id = books.id
				GROUP BY authors.id, authors.name, authors.image_url
				ORDER BY book_count DESC, authors.name;
				"""
			)
			return cursor.fetchall()


@lru_cache(maxsize=1)
def get_statistics() -> Dict[str, int]:
	"""
	Get application statistics counts with caching.
	
	Returns:
		Dict[str, int]: Statistics including total_books, total_authors, 
		total_categories, total_languages, total_users, total_collections,
		books_with_covers, and missing_covers
	"""
	stats: Dict[str, int] = {}
	with get_db() as conn:
		with conn.cursor() as cursor:
			# Use a single query to get all counts
			cursor.execute("""
				SELECT 
					(SELECT COUNT(*) FROM books) as total_books,
					(SELECT COUNT(*) FROM authors) as total_authors,
					(SELECT COUNT(*) FROM categories) as total_categories,
					(SELECT COUNT(*) FROM languages) as total_languages,
					(SELECT COUNT(*) FROM users) as total_users,
					(SELECT COUNT(*) FROM collections) as total_collections,
					(SELECT COUNT(*) FROM books WHERE cover_id IS NOT NULL) as books_with_covers,
					(SELECT COUNT(*) FROM books WHERE cover_id IS NULL) as missing_covers
			""")
			result = cursor.fetchone()
			stats = dict(result)

	return stats

def clear_statistics_cache():
	"""Clear the statistics cache when data changes."""
	get_statistics.cache_clear()


def _build_books_where(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
	conditions: List[str] = []
	params: List[Any] = []

	search = (filters.get("search") or "").strip()
	if search:
		conditions.append(
			"(b.title ILIKE %s OR a.name ILIKE %s OR c.name ILIKE %s)"
		)
		like = f"%{search}%"
		params.extend([like, like, like])

	category = (filters.get("category") or "").strip()
	if category:
		conditions.append("c.name = %s")
		params.append(category)

	language_id = filters.get("language_id")
	if language_id is not None:
		conditions.append("bl.language_id = %s")
		params.append(language_id)

	author_id = filters.get("author_id")
	if author_id is not None:
		conditions.append("ba.author_id = %s")
		params.append(author_id)

	include_collection_id = filters.get("include_collection_id")
	if include_collection_id is not None:
		conditions.append("EXISTS (SELECT 1 FROM collection_books cb2 WHERE cb2.book_id = b.id AND cb2.collection_id = %s)")
		params.append(include_collection_id)

	exclude_collection_id = filters.get("exclude_collection_id")
	if exclude_collection_id is not None:
		conditions.append("NOT EXISTS (SELECT 1 FROM collection_books cb3 WHERE cb3.book_id = b.id AND cb3.collection_id = %s)")
		params.append(exclude_collection_id)

	where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
	return where_clause, params


def count_books(filters: Optional[Dict[str, Any]] = None) -> int:
	filters = filters or {}
	where_clause, params = _build_books_where(filters)
	with get_db() as conn:
		with conn.cursor() as cursor:
			cursor.execute(
				f"""
				SELECT COUNT(DISTINCT b.id)
				FROM books b
				LEFT JOIN book_authors ba ON b.id = ba.book_id
				LEFT JOIN authors a ON ba.author_id = a.id
				LEFT JOIN book_categories bc ON b.id = bc.book_id
				LEFT JOIN categories c ON bc.category_id = c.id
				LEFT JOIN book_languages bl ON b.id = bl.book_id
				{where_clause}
				""",
				params,
			)
			row = cursor.fetchone()
			return list(row.values())[0] if row else 0


def fetch_books(
	filters: Optional[Dict[str, Any]] = None,
	pagination: Optional[Dict[str, int]] = None,
	order: Optional[str] = None,
) -> List[Dict[str, Any]]:
	"""Fetch books with optional filters and pagination.

	order supports 'title' (default) or 'id'.
	"""
	filters = filters or {}
	pagination = pagination or {}
	where_clause, params = _build_books_where(filters)

	limit = pagination.get("limit")
	offset = pagination.get("offset", 0)
	order_by = "b.title" if order == "title" or order is None else "b.id"

	limit_clause = ""
	if limit is not None:
		limit_clause = " LIMIT %s OFFSET %s"
		params.extend([limit, offset])

	with get_db() as conn:
		with conn.cursor() as cursor:
			cursor.execute(
				f"""
				SELECT DISTINCT b.id, b.title, b.publication_year, b.cover_id,
				       COALESCE(ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), ARRAY[]::text[]) AS authors,
				       COALESCE(ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), ARRAY[]::text[]) AS categories
				FROM books b
				LEFT JOIN book_authors ba ON b.id = ba.book_id
				LEFT JOIN authors a ON ba.author_id = a.id
				LEFT JOIN book_categories bc ON b.id = bc.book_id
				LEFT JOIN categories c ON bc.category_id = c.id
				LEFT JOIN book_languages bl ON b.id = bl.book_id
				{where_clause}
				GROUP BY b.id, b.title, b.publication_year, b.cover_id
				ORDER BY {order_by}
				{limit_clause}
				""",
				params,
			)
			return cursor.fetchall()


