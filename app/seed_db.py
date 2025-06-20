"""
Execute with:  python app/seed_db.py
Purpose: Adds 10 fake users to the real users table
"""
from faker import Faker
from app import create_app
from app.extensions import db
from app.models.user import User  # ✅ Using your actual User model

fake = Faker()

def run():
    app = create_app()
    with app.app_context():
        for _ in range(10):
            email = fake.unique.email()
            username = fake.user_name()

            # Check if email already exists to avoid duplicates
            if not db.session.scalar(db.select(User).filter_by(email=email)):
                user = User(
                    username=username,
                    email=email,
                    password="placeholder123"  # 🔐 Not hashed; for dev only
                )
                db.session.add(user)

        db.session.commit()
        print("🌱  Successfully seeded 10 fake users")

if __name__ == "__main__":
    run()
