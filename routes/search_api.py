from flask import Blueprint, jsonify, request
from database import get_db


search_api = Blueprint('search_api', __name__, url_prefix='/api')


@search_api.route('/search', methods=['GET'])
def search():
	q = (request.args.get('q') or '').strip()
	if not q:
		return jsonify({"books": [], "authors": []})

	with get_db() as conn:
		with conn.cursor() as cursor:
			# Books search by title or author name
			cursor.execute(
				"""
				SELECT DISTINCT b.id, b.title, b.publication_year, b.cover_id,
				       COALESCE(ARRAY_AGG(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), ARRAY[]::text[]) AS authors,
				       COALESCE(ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), ARRAY[]::text[]) AS categories
				FROM books b
				LEFT JOIN book_authors ba ON b.id = ba.book_id
				LEFT JOIN authors a ON ba.author_id = a.id
				LEFT JOIN book_categories bc ON b.id = bc.book_id
				LEFT JOIN categories c ON bc.category_id = c.id
				WHERE LOWER(b.title) LIKE LOWER(%s)
				   OR EXISTS (
				       SELECT 1 FROM book_authors ba2
				       JOIN authors a2 ON ba2.author_id = a2.id
				       WHERE ba2.book_id = b.id AND LOWER(a2.name) LIKE LOWER(%s)
				   )
				GROUP BY b.id, b.title, b.publication_year, b.cover_id
				ORDER BY b.title
				""",
				(f"%{q}%", f"%{q}%"),
			)
			books = cursor.fetchall()

			# Authors search by name
			cursor.execute(
				"""
				SELECT a.id, a.name, a.image_url,
				       COUNT(DISTINCT b.id) AS book_count
				FROM authors a
				LEFT JOIN book_authors ba ON a.id = ba.author_id
				LEFT JOIN books b ON ba.book_id = b.id
				WHERE LOWER(a.name) LIKE LOWER(%s)
				GROUP BY a.id, a.name, a.image_url
				ORDER BY a.name
				""",
				(f"%{q}%",),
			)
			authors = cursor.fetchall()

	return jsonify({"books": books, "authors": authors})


