import json
import hashlib
import uuid

import firebase_admin
from firebase_admin import credentials, auth
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import requests

# --- Firebase Initialization ---
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
DB_URL = "https://customer-data-e5395.firebaseio.com"
DB_URL_A = "https://artisan-data.firebaseio.com/"


def parse_int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def normalize_artisan_record(key, artisan):
    if not isinstance(artisan, dict):
        return None

    profession = (artisan.get("profession") or artisan.get("Profession") or "Repair").strip()
    profession_text = profession or "Repair"
    lower_profession = profession_text.lower()

    if "electric" in lower_profession:
        category = "electrician"
    elif "plumb" in lower_profession or "pipe" in lower_profession:
        category = "plumber"
    elif "ict" in lower_profession or "tech" in lower_profession or "computer" in lower_profession:
        category = "ict"
    else:
        category = "repair"

    name = artisan.get("name") or artisan.get("Name") or "Artisan"
    email = artisan.get("email") or artisan.get("Email") or ""
    qualification = artisan.get("qualification") or artisan.get("Qualification") or "Certified professional"
    rate = parse_int(artisan.get("hourlyRate", artisan.get("rate", 550)), 550)
    callout = parse_int(artisan.get("calloutFee", artisan.get("callout_fee", 250)), 250)

    return {
        "id": key,
        "name": name,
        "email": email,
        "profession": profession_text,
        "qualification": qualification,
        "label": profession_text,
        "area": artisan.get("area") or artisan.get("location") or "Gqeberha",
        "rate": rate,
        "hourlyRate": rate,
        "calloutFee": callout,
        "jobs": parse_int(artisan.get("jobs", 12), 12),
        "rating": parse_int(artisan.get("rating", 5), 5),
        "verified": bool(artisan.get("verified", True)),
        "available": bool(artisan.get("available", True)),
        "category": category,
        "certs": qualification,
        "status": "Online" if artisan.get("available", True) else "Offline",
    }


def fetch_artisans():
    response = requests.get(f"{DB_URL_A.rstrip('/')}/artisans.json", timeout=10)
    response.raise_for_status()
    payload = response.json() or {}

    if isinstance(payload, list):
        payload = {str(index): item for index, item in enumerate(payload)}

    artisans = []
    for key, value in payload.items():
        normalized = normalize_artisan_record(key, value)
        if normalized:
            artisans.append(normalized)
    return artisans


# --- Sign Up Form Display ---
@app.route("/", methods=["GET"])
def sign_up():
    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("Email")
        password = request.form.get("Password")
        print(f"Login attempt for {email} with password length {len(password) if password else 0}")
        return render_template("Feed.html")
    return render_template("login.html")


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
        "qualification": qualification,
        "hourlyRate": 550,
        "calloutFee": 250,
        "available": True,
        "verified": True,
        "rating": 5,
        "jobs": 0,
        "area": "Gqeberha",
    }
    try:
        resp = requests.post(
            f"{DB_URL_A.rstrip('/')}/artisans.json",
            json=freelancer_data,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        artisan_id = result.get("name") if isinstance(result, dict) else None
        print("Firebase response (artisan):", result)
        if artisan_id:
            return redirect(url_for("artisan_dashboard", artisan_id=artisan_id))
        return render_template("Artisan-login.html")
    except requests.RequestException as e:
        print("Error writing artisan to RTDB:", e)
        return (f"Failed to save artisan: {e}", 500)


@app.route("/api/artisans", methods=["GET"])
def api_artisans():
    try:
        return jsonify(fetch_artisans())
    except requests.RequestException as exc:
        print("Error reading artisans:", exc)
        return jsonify([])


@app.route('/api/artisan/<artisan_id>', methods=['GET'])
def api_get_artisan(artisan_id):
    """Return a single normalized artisan record as JSON."""
    try:
        resp = requests.get(f"{DB_URL_A.rstrip('/')}/artisans/{artisan_id}.json", timeout=10)
        resp.raise_for_status()
        record = resp.json() or {}
    except requests.RequestException as exc:
        print("Error loading artisan for API:", exc)
        return jsonify({}), 404

    normalized = normalize_artisan_record(artisan_id, record)
    return jsonify(normalized or {})


@app.route("/artisan/<artisan_id>", methods=["GET"])
def artisan_dashboard(artisan_id):
    try:
        artisan_response = requests.get(f"{DB_URL_A.rstrip('/')}/artisans/{artisan_id}.json", timeout=10)
        artisan_response.raise_for_status()
        record = artisan_response.json() or {}
    except requests.RequestException as exc:
        print("Error loading artisan profile:", exc)
        record = {}

    artisan = normalize_artisan_record(artisan_id, record) or {
        "id": artisan_id,
        "name": "Artisan",
        "profession": "Repair",
        "email": "",
        "qualification": "Certified professional",
        "hourlyRate": 550,
        "calloutFee": 250,
        "available": True,
        "verified": True,
        "status": "Online",
    }
    return render_template("Artisan-login.html", artisan=artisan)


@app.route("/api/artisan/<artisan_id>/profile", methods=["POST"])
def update_artisan_profile(artisan_id):
    payload = request.get_json(silent=True) or {}

    try:
        existing_response = requests.get(f"{DB_URL_A.rstrip('/')}/artisans/{artisan_id}.json", timeout=10)
        existing_response.raise_for_status()
        current = existing_response.json() or {}
    except requests.RequestException:
        current = {}

    if not isinstance(current, dict):
        current = {}

    merged = dict(current)
    for key, value in payload.items():
        merged[key] = value

    update_response = requests.put(f"{DB_URL_A.rstrip('/')}/artisans/{artisan_id}.json", json=merged, timeout=10)
    update_response.raise_for_status()

    return jsonify(normalize_artisan_record(artisan_id, merged))


#Customer-Profile Page
@app.route("/Customer_Profile")
def profile():
    # Template file in workspace is named "Customer_Profile (1).html" — render that.
    return render_template("Customer_Profile (1).html")


# Chat window page opened from the feed when a user books a pro
@app.route("/chat-window")
@app.route("/chat")
def chat_window():
    return render_template("chat-window.html")


# User Authentication - create a custom token for the signed-up UID and return it
# as JSON so the frontend can call signInWithCustomToken(auth, customToken)
@app.route('/sessionLogin', methods=['POST'])
def session_token():
    data = request.get_json(silent=True) or {}
    uid = data.get("uid")

    if not uid:
        return jsonify({"error": "uid is required"}), 400

    custom_token = auth.create_custom_token(uid)

    if isinstance(custom_token, (bytes, bytearray)):
        custom_token = custom_token.decode("utf-8")

    return jsonify({
        "customToken": custom_token,
        "token": custom_token,
        "custom_token": custom_token,
    })


PAYFAST_URL = "https://www.payfast.co.za/eng/process"
PAYFAST_MERCHANT_ID = "10000105"
PAYFAST_MERCHANT_KEY = "YOUR_MERCHANT_KEY"
PAYFAST_PASSPHRASE = "YOUR_PAYFAST_PASSPHRASE"
PAYFAST_RETURN_URL = "http://localhost:5000/payments/return"
PAYFAST_CANCEL_URL = "http://localhost:5000/payments/cancel"
PAYFAST_NOTIFY_URL = "http://localhost:5000/payments/notify"


def generate_payfast_signature(payload):
    """Generate a PayFast signature for a standard payment form payload.
    Replace the placeholder merchant key/passphrase with your real credentials
    before going live. The form data must be signed using PayFast's documented
    algorithm.
    """
    if not PAYFAST_MERCHANT_KEY or PAYFAST_MERCHANT_KEY == "YOUR_MERCHANT_KEY":
        return "" 

    data = {k: str(v) for k, v in payload.items() if v is not None and v != ""}
    sorted_keys = sorted(data)
    joined = "&".join(f"{key}={data[key]}" for key in sorted_keys)
    to_hash = f"{joined}{PAYFAST_PASSPHRASE}"
    return hashlib.md5(to_hash.encode("utf-8")).hexdigest()


@app.route('/payments/checkout', methods=['POST'])
def create_split_payment_checkout():
    """Build a PayFast split-payment form for a confirmed booking.
    This is intended to be called from the chat payment confirm action.
    """
    data = request.get_json(silent=True) or {}
    amount = float(data.get('amount', 0) or 0)
    artisan_name = data.get('artisan_name') or 'Pro Fix Artisan'
    item_description = data.get('item_description') or f"Booking with {artisan_name}"
    email_address = data.get('email_address') or 'customer@example.com'

    split_payment = {
        "merchant_id": int(data.get('merchant_id', PAYFAST_MERCHANT_ID)),
        "percentage": int(data.get('split_percentage', 10)),
        "min": int(data.get('split_min', 100)),
        "max": int(data.get('split_max', 100000)),
    }

    if amount <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400

    payment_id = data.get('payment_id') or f"booking-{uuid.uuid4().hex[:12]}"
    form_data = {
        "merchant_id": PAYFAST_MERCHANT_ID,
        "merchant_key": PAYFAST_MERCHANT_KEY,
        "return_url": data.get('return_url', PAYFAST_RETURN_URL),
        "cancel_url": data.get('cancel_url', PAYFAST_CANCEL_URL),
        "notify_url": data.get('notify_url', PAYFAST_NOTIFY_URL),
        "m_payment_id": payment_id,
        "amount": f"{amount:.2f}",
        "item_name": data.get('item_name') or f"Booking with {artisan_name}",
        "item_description": item_description,
        "email_address": email_address,
        "split_payment": json.dumps(split_payment),
    }

    signature = generate_payfast_signature(form_data)
    if signature:
        form_data['signature'] = signature

    input_fields = "\n".join(
        f'<input type="hidden" name="{key}" value="{value}">' for key, value in form_data.items()
    )

    html = f"""
    <html><body>
    <form id="payfast_form" method="post" action="{PAYFAST_URL}">
        {input_fields}
    </form>
    <script>document.getElementById('payfast_form').submit();</script>
    </body></html>
    """
    return Response(html, mimetype='text/html')


@app.route('/payments/notify', methods=['POST'])
def payfast_notify():
    payload = request.form.to_dict()
    print('PayFast notify payload:', payload)
    return '', 200


@app.route('/payments/return', methods=['GET'])
def payfast_return():
    return jsonify({"status": "payment returned"})


@app.route('/payments/cancel', methods=['GET'])
def payfast_cancel():
    return jsonify({"status": "payment cancelled"})


if __name__ == '__main__':
    app.run() 