"""
Vigil Backend - Migration Runner

Runs all pending database migrations in order.

Usage:
    VIGIL_DB_PATH=/path/to/vigil.db python3 migrations/run_migrations.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DB_PATH as DEFAULT_DB_PATH

# Use environment variable or default
DB_PATH = os.environ.get("VIGIL_DB_PATH", DEFAULT_DB_PATH)


def get_migration_files():
    """Get all migration files in order."""
    migrations_dir = Path(__file__).parent
    files = sorted([
        f for f in migrations_dir.glob("*.py")
        if f.name.startswith(("001", "002", "003", "004", "005"))
        and f.name not in ("run_migrations.py",)
    ])
    return files


def run_migration(migration_file: Path):
    """Run a single migration file."""
    print(f"\n{'='*60}")
    print(f"Running: {migration_file.name}")
    print('='*60)

    # Import and run
    import importlib.util
    spec = importlib.util.spec_from_file_location("migration", migration_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "migrate"):
        module.migrate()
    elif hasattr(module, "enrich_vendors"):
        module.enrich_vendors()
    else:
        print(f"Warning: No migrate() or enrich_vendors() function found in {migration_file.name}")


def main():
    """Run all pending migrations."""
    print(f"Vigil Backend Migration Runner")
    print(f"Database: {DB_PATH}")
    print()

    migrations = get_migration_files()

    if not migrations:
        print("No migration files found.")
        return

    print(f"Found {len(migrations)} migration(s):")
    for m in migrations:
        print(f"  - {m.name}")

    for migration in migrations:
        try:
            run_migration(migration)
        except Exception as e:
            print(f"\n❌ Migration failed: {migration.name}")
            print(f"Error: {e}")
            print("\nFix the error and re-run migrations.")
            sys.exit(1)

    print(f"\n{'='*60}")
    print("✅ All migrations completed successfully!")
    print('='*60)


if __name__ == "__main__":
    main()
