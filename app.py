from flask import Flask, render_template, redirect, request, session
import requests
import json
from config import login_required

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html") 

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

@app.route("/documentation")
@login_required
def documentation():
    if request.method == "GET":
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