from flask import session, redirect, flash, request, jsonify
from functools import wraps
from pymongo import MongoClient
from bson import ObjectId
import os

# Set up MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['travel360']
collection = db['users']


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            session.clear()
            return redirect("/login")
        else:
            user_id = session.get("user_id")
            user_details = collection.find_one({"_id": ObjectId(user_id)})
            if not user_details:   # safeguard if user not found
                flash("User not found!", "error")
                return redirect("/logout")
        return f(*args, **kwargs)

    return decorated_function

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        incoming_key = request.headers.get("api-key")
        server_key = os.getenv("API_KEY")
        
        # --- DEBUG PRINTS ---
        print(f"DEBUG: Incoming Header: {incoming_key}")
        print(f"DEBUG: Server Env Key: {server_key}")
        # --------------------

        if incoming_key != server_key:
            return jsonify({"status": "error", "message": "missing or invalid API key"}), 403
            
        return f(*args, **kwargs)
    return decorated_function