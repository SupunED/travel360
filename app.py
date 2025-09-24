from flask import Flask, flash, render_template, redirect, request, session
from pymongo import MongoClient
from flask_session import Session
import requests
import json
from config import login_required
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['travel360']
collection = db['users']

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        
        user_id = session.get("user_id")
        # Convert string back to ObjectId
        user_details = collection.find_one({"_id": ObjectId(user_id)})
        if not user_details:   # safeguard if user not found
            flash("User not found!", "error")
            return redirect("/login")
        
        username = user_details["username"]
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
            return redirect("/")
        
        user = collection.find_one({'username': username})
        
        if not user or not check_password_hash(user["password_hashed"], password):
            flash("Invalid Username/Password Combination!", "error")
            return redirect("/")
        
        
        # Save user ID in session
        session["user_id"] = str(user["_id"])
        flash("Login successful!", "success")
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
            return redirect("/")
        elif password != confirmation:
            flash("Password and Re-type Password must match!", "error")
            return redirect("/")

        existing_user = collection.find_one({'username': username})
        if existing_user:
            flash("Username already taken!", "error")
            return redirect("/")
        
        password_hashed = generate_password_hash(password, method="pbkdf2", salt_length=16)
        
        result = collection.insert_one({'username': username, 'password_hashed': password_hashed})
        if result:
            session["user_id"] = str(result.inserted_id)
            flash("Registered Successfully", "success")
            return redirect("/")
        

@app.route("/documentation")
@login_required
def documentation():
    return render_template("documentation.html")


@app.route("/records", methods=["GET", "POST"])
@login_required
def records():
    if request.method == "GET":
        return render_template("records.html")



''' # Get country input
country = input("Enter Country Code: ").strip().upper()

covid_19_api = f"https://disease.sh/v3/covid-19/countries/{country}"
country_api = f"https://restcountries.com/v3.1/name/{country}"


covid_response = requests.get(covid_19_api)
country_response = requests.get(country_api)

print(json.dumps(covid_response.json(), indent=4, sort_keys=True))
print()
print(json.dumps(country_response.json(), indent=4, sort_keys=True))

'''

if __name__ == "__main__":
    app.run(debug=True)