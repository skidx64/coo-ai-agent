"""Seed database with demo data for AWS deployment."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models.models import Family, FamilyMember, Child, PhoneLookup
from services.auth_service import hash_password


def seed_demo_data():
    """Create 2 parents and 2 children for demo purposes."""

    # Initialize database
    init_db()

    db = SessionLocal()

    try:
        # Check if demo family already exists
        existing = db.query(Family).filter(Family.primary_email == "demo@cooai.test").first()
        if existing:
            print("Demo data already exists. Skipping seed.")
            return existing.id

        # Create demo family
        family = Family(
            primary_name="Demo Parent",
            primary_phone="+15555550001",  # Demo phone number
            primary_email="demo@cooai.test",
            password_hash=hash_password("demo123"),  # Demo password
            is_email_verified=True,
            is_phone_verified=True,
            tier="FAMILY",  # FAMILY tier allows 2 members, 3 children
            trial_start_date=datetime.utcnow(),
            trial_end_date=datetime.utcnow() + timedelta(days=365),  # 1 year trial
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(family)
        db.flush()  # Get family.id

        # Create Parent 1 (Primary)
        parent1 = FamilyMember(
            family_id=family.id,
            name="Sarah Johnson",
            phone_number="+15555550001",
            relationship="mom",
            is_primary=True,
            receive_proactive=True,
            can_ask_questions=True,
            created_at=datetime.utcnow()
        )
        db.add(parent1)

        # Create Parent 2
        parent2 = FamilyMember(
            family_id=family.id,
            name="Michael Johnson",
            phone_number="+15555550002",
            relationship="dad",
            is_primary=False,
            receive_proactive=True,
            can_ask_questions=True,
            created_at=datetime.utcnow()
        )
        db.add(parent2)

        db.flush()  # Get member IDs

        # Create PhoneLookup entries for fast routing
        lookup1 = PhoneLookup(
            phone_number="+15555550001",
            family_id=family.id,
            member_id=parent1.id
        )
        db.add(lookup1)

        lookup2 = PhoneLookup(
            phone_number="+15555550002",
            family_id=family.id,
            member_id=parent2.id
        )
        db.add(lookup2)

        # Create Child 1 (3 years old)
        child1 = Child(
            family_id=family.id,
            name="Emma Johnson",
            birth_date=datetime.utcnow() - timedelta(days=365*3),  # 3 years old
            gender="female",
            is_pregnancy=False,
            created_at=datetime.utcnow()
        )
        db.add(child1)

        # Create Child 2 (6 months old)
        child2 = Child(
            family_id=family.id,
            name="Noah Johnson",
            birth_date=datetime.utcnow() - timedelta(days=180),  # 6 months old
            gender="male",
            is_pregnancy=False,
            created_at=datetime.utcnow()
        )
        db.add(child2)

        db.commit()

        print("=" * 60)
        print("DEMO DATA CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"Family ID: {family.id}")
        print(f"\nParents:")
        print(f"  1. {parent1.name} ({parent1.relationship}) - {parent1.phone_number}")
        print(f"  2. {parent2.name} ({parent2.relationship}) - {parent2.phone_number}")
        print(f"\nChildren:")
        print(f"  1. {child1.name} - 3 years old ({child1.gender})")
        print(f"  2. {child2.name} - 6 months old ({child2.gender})")
        print(f"\nLogin Credentials:")
        print(f"  Email: demo@cooai.test")
        print(f"  Password: demo123")
        print(f"  (Auth is bypassed in AWS deployment)")
        print("=" * 60)

        return family.id

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    family_id = seed_demo_data()
    print(f"\nDemo family_id: {family_id}")
