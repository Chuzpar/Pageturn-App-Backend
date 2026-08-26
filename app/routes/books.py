from flask import Blueprint, jsonify, request

from app import db
from app.models.book import Book


books_bp = Blueprint("books", __name__)


@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
	book = Book.query.get(book_id)
	if not book:
		return jsonify({"error": "Book not found"}), 404
	return jsonify({"book": book.to_dict()})


@books_bp.route("", methods=["GET"])
def list_books():
	query = Book.query
	search = request.args.get("q", "").strip()
	if search:
		query = query.filter(Book.title.ilike(f"%{search}%") | Book.author.ilike(f"%{search}%"))
	genre = request.args.get("genre")
	if genre:
		query = query.filter_by(genre=genre)

	sort = request.args.get("sort", "created_at")
	if sort == "rating":
		query = query.order_by(Book.rating.desc())
	elif sort == "price":
		query = query.order_by(Book.price.asc())
	else:
		query = query.order_by(Book.created_at.desc())

	return jsonify({"books": [book.to_dict() for book in query.all()]})


@books_bp.route("/genres", methods=["GET"])
def list_genres():
	genres = db.session.query(Book.genre).filter(Book.genre.isnot(None), Book.genre != "").distinct().order_by(Book.genre).all()
	return jsonify({"genres": [genre for (genre,) in genres]})
