import firebase_admin
from firebase_admin import credentials
from flask import Flask, render_template, request, jsonify
import requests
from firebase_admin import auth 

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
    return render_template("Feed.html")


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
    
#Customer-Profile Page
@app.route("/Customer_Profile")
def profile():
    return render_template("Customer_Profile.html")

# User Authentication - create a custom token for the signed-up UID and return it
# as JSON so the frontend can call signInWithCustomToken(auth, customToken)
@app.route('/sessionLogin', methods=['POST'])
def session_token():
    data = request.get_json(silent=True) or {}
    uid 
    uid = data.get("uid")
    
    custom_token = auth.create_custom_token(uid)

    if not uid:
        return jsonify({"error": "uid is required"}), 400

    
    if isinstance(custom_token, (bytes, bytearray)):
        custom_token = custom_token.decode("utf-8")

    return jsonify({
        "customToken": custom_token,
        "token": custom_token,
        "custom_token": custom_token,
    })