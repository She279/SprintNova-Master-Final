"""
One-time bootstrap script: creates the first Owner/Admin account so there's
someone who can log in and start creating employees through the API.

Usage:
    python create_first_admin.py
"""
import getpass

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.role import RoleEnum
from app.models.user import User
from app.utils.email_generator import generate_company_email
from app import models  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == RoleEnum.OWNER_ADMIN).first():
            print("An Owner/Admin account already exists.")
            create_another = input("Create another Owner/Admin account? [y/N]: ").strip().lower()
            if create_another != "y":
                print("Aborting.")
                return

        print("=== Create the first SprintNova Owner/Admin ===")
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        personal_email = input("Personal email: ").strip()
        employee_id = input("Employee ID: ").strip()
        password = getpass.getpass("Set initial password: ")

        company_email = generate_company_email(db, first_name, last_name)

        admin = User(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            personal_email=personal_email,
            company_email=company_email,
            role=RoleEnum.OWNER_ADMIN,
            password_hash=hash_password(password),
            must_change_password=False,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        print("\nAdmin account created.")
        print(f"Login (company) email: {company_email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
