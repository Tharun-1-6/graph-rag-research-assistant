import os
import sys
from flask import Flask, render_template, request, jsonify

# Reconfigure stdout/stderr to use UTF-8 to prevent 'charmap' encode crashes on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Initialize Flask application with static and templates folders
app = Flask(__name__,
            static_folder="static",
            template_folder="templates")

@app.route("/")
def index():
    """Serve the clean chat interface."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    POST route to receive chat requests and return a dummy response.
    Expects json payload: {"message": "..."}
    """
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message content cannot be empty."}), 400

        # Dummy response logic for now - no integration with RAG/LLM yet
        mock_response = {
            "answer": f"This is a placeholder response from the Flask server. I received your message: '{user_message}'. Full RAG integration coming next!",
            "status": "success"
        }
        return jsonify(mock_response)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # Run the server on port 5000 in debug mode
    print("Starting Flask server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
