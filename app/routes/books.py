from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.book import Book
from app.models.review import Review
from app.models.favorite import Favorite
from app.utils import current_user

books_bp = Blueprint("books", __name__)


@books_bp.route("", methods=["GET"])
def list_books():
    query = Book.query

    q = request.args.get("q")  # Task 6: search by title/author
    if q:
        like = f"%{q}%"
        query = query.filter((Book.title.ilike(like)) | (Book.author.ilike(like)))

    genre = request.args.get("genre")  # Task 8: filter by genre
    if genre:
        query = query.filter(Book.genre.ilike(genre))

    min_price = request.args.get("min_price", type=float)
    if min_price is not None:
        query = query.filter(Book.price >= min_price)

    max_price = request.args.get("max_price", type=float)
    if max_price is not None:
        query = query.filter(Book.price <= max_price)

    section = request.args.get("section")  # 'new_arrivals' | 'popular'
    if section == "new_arrivals":
        query = query.filter(Book.is_new_arrival.is_(True))
    elif section == "popular":
        query = query.filter(Book.is_popular.is_(True))

    sort = request.args.get("sort")  # 'price_asc' | 'price_desc' | 'rating'
    if sort == "price_asc":
        query = query.order_by(Book.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Book.price.desc())
    elif sort == "rating":
        query = query.order_by(Book.rating.desc())
    else:
        query = query.order_by(Book.created_at.desc())

    books = query.all()
    return jsonify({"books": [b.to_dict() for b in books], "count": len(books)})


@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"book": book.to_dict()})


@books_bp.route("/genres", methods=["GET"])
def list_genres():
    genres = [g[0] for g in Book.query.with_entities(Book.genre).distinct() if g[0]]
    return jsonify({"genres": genres})


@books_bp.route("/<int:book_id>/reviews", methods=["GET"])
def list_reviews(book_id):
    if not Book.query.get(book_id):
        return jsonify({"error": "Book not found"}), 404
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.created_at.desc()).all()
    return jsonify({"reviews": [r.to_dict() for r in reviews]})


@books_bp.route("/<int:book_id>/reviews", methods=["POST"])
@jwt_required()
def submit_review(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    data = request.get_json(force=True, silent=True) or {}
    rating = data.get("rating")
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "Rating must be an integer from 1 to 5"}), 400

    user = current_user()
    existing = Review.query.filter_by(user_id=user.id, book_id=book_id).first()
    if existing:
        existing.rating = rating
        existing.comment = data.get("comment", existing.comment)
        review = existing
    else:
        review = Review(user_id=user.id, book_id=book_id, rating=rating, comment=data.get("comment"))
        db.session.add(review)
    db.session.flush()

    all_ratings = [r.rating for r in Review.query.filter_by(book_id=book_id).all()]
    book.rating = round(sum(all_ratings) / len(all_ratings), 1) if all_ratings else 0.0

    db.session.commit()
    return jsonify({"review": review.to_dict(), "book_rating": book.rating}), 201

@books_bp.route("/favorites", methods=["GET"])
@jwt_required()
def list_favorites():
    user = current_user()
    favorites = Favorite.query.filter_by(user_id=user.id).order_by(Favorite.created_at.desc()).all()
    return jsonify({"favorites": [f.to_dict() for f in favorites]})


@books_bp.route("/<int:book_id>/favorite", methods=["POST"])
@jwt_required()
def add_favorite(book_id):
    if not Book.query.get(book_id):
        return jsonify({"error": "Book not found"}), 404
    user = current_user()
    if Favorite.query.filter_by(user_id=user.id, book_id=book_id).first():
        return jsonify({"message": "Already in your favorites"}), 200
    db.session.add(Favorite(user_id=user.id, book_id=book_id))
    db.session.commit()
    return jsonify({"message": "Added to favorites"}), 201


@books_bp.route("/<int:book_id>/favorite", methods=["DELETE"])
@jwt_required()
def remove_favorite(book_id):
    user = current_user()
    fav = Favorite.query.filter_by(user_id=user.id, book_id=book_id).first()
    if not fav:
        return jsonify({"error": "Not in your favorites"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Removed from favorites"})
