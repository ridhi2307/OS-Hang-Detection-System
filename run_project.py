"""Start the local OS Guardian dashboard."""
from backend.app import app
from backend.database import create_tables


if __name__ == "__main__":
    create_tables()
    print("Open OS Guardian at http://127.0.0.1:5000", flush=True)
    app.run(host="127.0.0.1", port=5000)
