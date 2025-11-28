from flask import Flask, flash, jsonify, render_template, redirect, request, session
from pymongo import MongoClient
from flask_session import Session
import requests
import json
from config import login_required, require_api_key
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId
from dotenv import load_dotenv
import os

# load env variables
load_dotenv()

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['travel360']
collection = db['users']


# Google OAuth2.0 configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# The redirect URI must match exactly what you configured in the Google Cloud Console
GOOGLE_REDIRECT_URI = "http://localhost:5000/callback" 
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session.get("user_id")
    user_details = collection.find_one({"_id": ObjectId(user_id)})

    username = user_details["username"]

    if request.method == "POST":
        country = request.form.get("country", "").strip()
        if not country:
            flash("Enter a Country Name!", "error")
            return redirect("/")

        covid_19_api = f"https://disease.sh/v3/covid-19/countries/{country}"
        country_api = f"https://restcountries.com/v3.1/name/{country}"

        try:
            covid_response = requests.get(covid_19_api).json()
            country_response = requests.get(country_api).json()
        except Exception as e:
            flash("Error fetching data from APIs. Please try again later.", "error")
            return redirect("/")
        
        # Handle invalid country case (RestCountries API)
        if isinstance(country_response, dict) and country_response.get("status") == 404:
            flash("Invalid Country Name!", "error")
            return redirect("/")

        # Handle invalid country case (Covid API)
        if isinstance(covid_response, dict) and covid_response.get("message"):
            flash(covid_response["message"], "error")
            return redirect("/")


        # If valid, pick first country object
        country_data = country_response[0] if isinstance(country_response, list) else country_response
        
        aggregated_data = {
            "name": country_data["name"]["common"],
            "currencies": country_data.get("currencies", {}),
            "capital": country_data.get("capital", []),
            "population": country_data.get("population"),
            "timezones": country_data.get("timezones", []),
            "continents": country_data.get("continents", []),
            "flag": country_data.get("flags", {}).get("png"),
            "todayCases": covid_response.get("todayCases"),
            "todayDeaths": covid_response.get("todayDeaths"),
            "todayRecovered": covid_response.get("todayRecovered"),
            "active": covid_response.get("active"),
        }

        return render_template("index.html", username=username, data=aggregated_data)

    # Default GET request (no API results yet)
    return render_template("index.html", username=username)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    # If the user request the login page
    if request.method == "GET":
        return render_template("login.html")
    
    # If the user has submitted login info via form
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == "" or password == "":
            flash("All fields must be filled!", "error")
            return redirect("/login")
        
        user = collection.find_one({'username': username})
        
        if not user or not check_password_hash(user["password_hashed"], password):
            flash("Invalid Username/Password Combination!", "error")
            return redirect("/login")
        
        
        # Save user ID in session
        session["user_id"] = str(user["_id"])
        flash("Login successful!", "success")
        return redirect("/")




@app.route("/login/google")
def login_google():
    """
    Redirects the user to Google's authorization page.
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "prompt": "select_account"
    }
    return redirect(f"{GOOGLE_AUTHORIZATION_URL}?{requests.compat.urlencode(params)}")

@app.route("/callback")
def callback():
    """
    Handles the redirect from Google and exchanges the code for tokens.
    """
    code = request.args.get("code")
    if not code:
        flash("Google login failed. No code received.", "error")
        return redirect("/login")
    
    # Exchange authorization code for access and ID tokens
    token_payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    try:
        # Step 1: Get tokens
        token_response = requests.post(GOOGLE_TOKEN_URL, data=token_payload)
        token_response.raise_for_status()
        tokens = token_response.json()
        print("Google token response:", tokens)  # Debugging

        access_token = tokens.get("access_token")
        id_token = tokens.get("id_token")

        if not access_token:
            flash("Google login failed. No access token received.", "error")
            return redirect("/login")

        # Step 2: Get user info with the access token
        user_info_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        print("User info:", user_info)  # Debugging

        # Step 3: Extract useful fields
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", email)

        if not google_id or not email:
            flash("Google login failed. Missing user information.", "error")
            return redirect("/login")

        # Step 4: Check if user exists
        user = collection.find_one({"google_id": google_id})
        
        if user:
            # User exists, log them in
            session["user_id"] = str(user["_id"])
            flash(f"Welcome back, {name}!", "success")
        else:
            # User does not exist, create a new entry
            new_user = {
                "google_id": google_id,
                "email": email,
                "username": name,
                "password_hashed": ""  # no password needed for Google login
            }
            result = collection.insert_one(new_user)
            session["user_id"] = str(result.inserted_id)
            flash("Registered successfully with Google!", "success")

    except Exception as e:
        print(f"Error during Google OAuth: {e}")
        flash("Google login failed. Please try again.", "error")
        return redirect("/login")
    
    return redirect("/")
      
@app.route("/logout")
def logout():
    # clear any user_id
    session.clear()
    return redirect("/") 

@app.route("/register", methods=["GET", "POST"])
def register():
    # if the user has requested the register page
    if request.method == "GET":
        return render_template("register.html")
    
    # if the user has submitted register data via form
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if username == "" or password == "" or confirmation == "":
            flash("All fields must be filled!", "error")
            return redirect("/register")
        elif password != confirmation:
            flash("Password and Re-type Password must match!", "error")
            return redirect("/register")

        existing_user = collection.find_one({'username': username})
        if existing_user:
            flash("Username already taken!", "error")
            return redirect("/register")
        
        password_hashed = generate_password_hash(password, method="pbkdf2", salt_length=16)
        
        result = collection.insert_one({'username': username, 'password_hashed': password_hashed})
        if result:
            session["user_id"] = str(result.inserted_id)
            flash("Registered Successfully", "success")
            return redirect("/")
        

@app.route("/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json()
        if not data:
            flash("No data provided", "error")
            return redirect("/")
        
        data["user_id"] = session.get("user_id")
        
        db.records.insert_one(data)
        return jsonify({"status": "success", "message": "Data saved successfully!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/documentation")
@login_required
def documentation():
    return render_template("documentation.html")


@app.route("/records", methods=["GET"])
@login_required
def records():
    user_id = session.get("user_id")
    saved_records = list(db.records.find({'user_id': user_id}))
    return render_template("records.html", records=saved_records)


@app.route("/get", methods=["GET"])
@require_api_key
def get_all_records():
    try:
        # Note the two sets of curly braces:
        # 1st {}: The query (empty = find all)
        # 2nd {}: The projection (0 = hide this field)
        records = list(db.records.find({}, {"_id": 0, "user_id": 0}))
        
        return jsonify({
            "status": "success",
            "count": len(records),
            "data": records
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

if __name__ == "__main__":
    app.run(debug=True)