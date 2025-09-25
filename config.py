from flask import session, redirect, flash
from functools import wraps
from pymongo import MongoClient
from bson import ObjectId

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