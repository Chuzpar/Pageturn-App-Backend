from app import create_app, db
from app.models.user import User
from app.models.book import Book

app = create_app()

BOOKS = [
    dict(title="The Odyssey", author="Homer", price=12.99, genre="Classics",
         rating=4.6, stock_for_lending=3, is_new_arrival=True),
    dict(title="Moby Dick", author="Herman Melville", price=14.50, genre="Classics",
         rating=4.2, stock_for_lending=2, is_new_arrival=True),
    dict(title="The Republic", author="Plato", price=11.00, genre="Philosophy",
         rating=4.5, stock_for_lending=4, is_new_arrival=True),
    dict(title="Crime and Punishment", author="Fyodor Dostoevsky", price=13.25, genre="Classics",
         rating=4.7, stock_for_lending=2, is_popular=True),
    dict(title="Pride & Prejudice", author="Jane Austen", price=9.99, genre="Romance",
         rating=4.8, stock_for_lending=5, is_popular=True),
    dict(title="To Kill a Mockingbird", author="Harper Lee", price=10.50, genre="Classics",
         rating=4.9, stock_for_lending=3, is_popular=True),
    dict(title="The Great Gatsby", author="F. Scott Fitzgerald", price=14.99, genre="Classics",
         rating=4.4, stock_for_lending=3),
    dict(title="Frankenstein", author="Mary Shelley", price=10.99, genre="Gothic",
         rating=4.3, stock_for_lending=2),
    dict(title="The Trial", author="Franz Kafka", price=11.75, genre="Classics",
         rating=4.1, stock_for_lending=1),
    dict(title="The Secret History", author="Donna Tartt", price=16.00, genre="Mystery",
         rating=4.6, stock_for_lending=2, description=(
             "Under the influence of their charismatic classics professor, a group of "
             "clever, eccentric misfits at an elite New England college discover a way "
             "of thinking and living that is a world away from the humdrum existence of "
             "their contemporaries."
         )),
]


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(full_name="Curator Admin", email="admin@pageturn.dev", role="admin")
        admin.set_password("admin123")
        member = User(full_name="Jane Reader", email="jane@pageturn.dev", role="member")
        member.set_password("password123")
        db.session.add_all([admin, member])

        for b in BOOKS:
            db.session.add(Book(**b))

        db.session.commit()
        print("Seeded database with 2 users and", len(BOOKS), "books.")
        print("  Admin login:  admin@pageturn.dev / admin123")
        print("  Member login: jane@pageturn.dev / password123")


if __name__ == "__main__":
    run()
