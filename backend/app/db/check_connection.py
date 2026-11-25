"""Command-line check that the backend can reach the configured PostgreSQL database.

Run from the backend folder with: uv run python -m app.db.check_connection
The connection string is never printed, because it contains the database password.
"""

import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import DatabaseNotConfiguredError, get_engine


def main() -> int:
    try:
        with get_engine().connect() as connection:
            server_version = connection.execute(text("SHOW server_version")).scalar_one()
    except DatabaseNotConfiguredError as error:
        print(f"Not configured: {error}")
        return 1
    except SQLAlchemyError as error:
        # Only the exception type is shown; driver messages can echo connection details.
        print(f"Connection failed ({type(error).__name__}). Check DATABASE_URL in backend/.env.")
        return 1

    print(f"Connected. PostgreSQL version: {server_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
