from sqlalchemy import inspect
from db import engine, Base
from models import User # Import your models so SQLAlchemy knows about them

def reset_database():
    # 1. Drop Tables
    print("🗑️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    # 2. VERIFICATION STEP
    print("🔍 Verifying drop...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # We check if any of OUR known tables still exist in the database
    # (We compare database tables vs. tables defined in models.py)
    tables_to_check = Base.metadata.tables.keys()
    failed_drops = [t for t in tables_to_check if t in existing_tables]

    if failed_drops:
        print(f"❌ ERROR: Failed to drop these tables: {failed_drops}")
        print("   (This might happen if there are active connections or locks.)")
        return # Stop here, do not recreate
    else:
        print("✅ Verification Passed: Tables dropped successfully.")

    # 3. Recreate Tables
    print("✨ Recreating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables recreated successfully!")

if __name__ == "__main__":
    confirmation = input("⚠️ Are you sure you want to DELETE ALL DATA? (y/n): ")
    if confirmation.lower() == "y":
        reset_database()
    else:
        print("Cancelled.")