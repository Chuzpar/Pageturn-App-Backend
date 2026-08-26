# Entrypoint for running the Flask dev server.
# Usage: python run.py

from app import create_app

app = create_app()

if __name__ == "__main__":
    # --- Sprint 1 - Task 2: Configure Flask Backend ---
    app.run(host="0.0.0.0", port=5001, debug=True)
