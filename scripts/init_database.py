#!/usr/bin/env python3
"""
Initialize database with tables
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from database module without going through __init__
from sqlalchemy import create_engine
from src.database import Base

def init_database():
    """Create all database tables"""
    print("Initializing database...")

    # Get database URL
    db_path = Path(__file__).parent.parent / "data" / "mental_health.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database_url = f"sqlite:///{db_path}"
    print(f"Database URL: {database_url}")

    # Create engine
    engine = create_engine(database_url, echo=True)

    # Create all tables
    Base.metadata.create_all(engine)

    print("\n✅ Database initialized successfully!")
    print(f"Database file: {db_path}")

    # List all tables
    print("\nCreated tables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

if __name__ == "__main__":
    init_database()
