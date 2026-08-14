import firebase_admin
from firebase_admin import credentials
from flask import Flask, render_template, request
import requests

# --- Firebase Initialization ---
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
DB_URL = "https://customer-data-e5395.firebaseio.com"
DB_URL_A = "https://artisan-data.firebaseio.com/"

# --- Sign Up Form Display ---
@app.route("/", methods=["GET"])
def sign_up():
    return render_template("sign_up.html")

# --- Sending Data to Realtime Database ---
@app.route("/sign_up", methods=["POST"])
def send_customer_data():
    name = request.form.get("Name")
    surname = request.form.get("Surname")
    email = request.form.get("Email")
    password = request.form.get("Password")

    customer_data = {
        "name": name,
        "surname": surname,
        "email": email,
        "password": password
    }

    response = requests.post(
        f"{DB_URL}/users.json",
        json=customer_data,
        timeout=10
    )
    response.raise_for_status()

    result = response.json()
    print("Firebase response:", result)
    return "User saved!"


@app.route("/send_freelancer_data", methods=["POST"])
def send_freelancer_data():
    name = request.form.get("Name")
    profession = request.form.get("Profession")
    email = request.form.get("Email")
    password = request.form.get("Password")
    qualification = request.form.get("Qualification")

    freelancer_data = {
        "name": name,
        "profession": profession,
        "email": email,
        "password": password,
        "qualification": qualification
    }
    try:
        resp = requests.post(
            f"{DB_URL_A.rstrip('/')}/artisans.json",
            json=freelancer_data,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        print("Firebase response (artisan):", result)
        return render_template("Artisan-login.html")
    except requests.RequestException as e:
        print("Error writing artisan to RTDB:", e)
        return (f"Failed to save artisan: {e}", 500)

if __name__ == "__main__":
    app.run(debug=True)