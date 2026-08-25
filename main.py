import firebase_admin
from firebase_admin import credentials, auth
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests

# --- Firebase Initialization ---
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = "profix-live-profile-session"
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
    try:
        response = requests.get(f"{DB_URL_A.rstrip('/')}/artisans.json", timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []

    payload = response.json() or {}
    if isinstance(payload, list):
        payload = {str(index): item for index, item in enumerate(payload)}

    artisans = []
    for key, value in payload.items():
        normalized = normalize_artisan_record(key, value)
        if normalized:
            artisans.append(normalized)
    return artisans


def clear_customer_session():
    for key in ["customer_email", "customer_id", "customer_name"]:
        session.pop(key, None)


def clear_artisan_session():
    for key in ["artisan_id", "artisan_email", "artisan_name"]:
        session.pop(key, None)


def set_customer_session(email=None, customer_id=None, name=None):
    clear_artisan_session()
    session["role"] = "customer"
    if email:
        session["customer_email"] = str(email).strip().lower()
    if customer_id:
        session["customer_id"] = customer_id
    if name:
        session["customer_name"] = str(name).strip()


def set_artisan_session(artisan_key, email=None, name=None):
    clear_customer_session()
    session["role"] = "artisan"
    if artisan_key is not None:
        session["artisan_id"] = artisan_key
    if email:
        session["artisan_email"] = str(email).strip().lower()
    if name:
        session["artisan_name"] = str(name).strip()


@app.route("/", methods=["GET"])
@app.route("/customer-sign-up", methods=["GET"])
def customer_sign_up():
    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
@app.route("/Login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("Email")
        if not email:
            return redirect(url_for("login"))

        email_norm = email.strip().lower()

        try:
            response = requests.get(f"{DB_URL_A.rstrip('/')}/artisans.json", timeout=10)
            response.raise_for_status()
            artisans = response.json() or {}
            if isinstance(artisans, list):
                artisans = {str(index): item for index, item in enumerate(artisans)}

            for artisan_key, artisan_data in artisans.items():
                if not isinstance(artisan_data, dict):
                    continue
                if str(artisan_data.get("email") or "").strip().lower() == email_norm:
                    set_artisan_session(
                        artisan_key,
                        email=email_norm,
                        name=str(artisan_data.get("name") or "Artisan").strip(),
                    )
                    return redirect(url_for("artisan_profile", artisan_id=artisan_key))
        except requests.RequestException:
            pass

        set_customer_session(email=email_norm)
        return redirect(url_for("feed_page"))
    return render_template("login.html")


app.add_url_rule("/login", endpoint="login_page", view_func=login, methods=["GET", "POST"])


@app.route("/sign_up", methods=["POST"])
@app.route("/Customer_sign_up", methods=["POST"])
def customer_sign_up_submit():
    name = request.form.get("Name")
    surname = request.form.get("Surname")
    email = request.form.get("Email")
    password = request.form.get("Password")

    customer_data = {
        "name": name,
        "surname": surname,
        "email": email,
        "password": password,
    }

    response = requests.post(f"{DB_URL}/users.json", json=customer_data, timeout=10)
    response.raise_for_status()

    result = response.json() or {}
    customer_id = result.get("name") if isinstance(result, dict) and result.get("name") else None

    set_customer_session(
        email=email,
        customer_id=customer_id,
        name=" ".join(filter(None, [name, surname])).strip() if (name or surname) else None,
    )

    return redirect(url_for("feed_page"))


@app.route("/feed")
@app.route("/Feed.html")
def feed_page():
    if session.get("role") == "artisan":
        artisan_id = session.get("artisan_id")
        if artisan_id:
            return redirect(url_for("artisan_profile", artisan_id=artisan_id))
        return redirect(url_for("artisan_sign_up"))
    return render_template("Feed.html")


@app.route("/Customer_Profile .html")
def customer_profile():
    if session.get("role") == "artisan":
        artisan_id = session.get("artisan_id")
        if artisan_id:
            return redirect(url_for("artisan_profile", artisan_id=artisan_id))
        return redirect(url_for("artisan_sign_up"))
    customer_email = request.args.get("email") or session.get("customer_email")
    customer_id = request.args.get("customer_id") or session.get("customer_id")

    if customer_email or customer_id:
        try:
            response = requests.get(f"{DB_URL}/users.json", timeout=10)
            response.raise_for_status()
            payload = response.json() or {}

            for key, value in payload.items():
                if not isinstance(value, dict):
                    continue

                record_email = str(value.get("email") or "").strip().lower()
                if customer_id and str(key) == str(customer_id):
                    customer = value
                    customer["id"] = key
                    break
                if customer_email and record_email == customer_email.strip().lower():
                    customer = value
                    customer["id"] = key
                    break
            else:
                customer = None
        except requests.RequestException:
            customer = None
    else:
        customer = None

    if customer:
        full_name = " ".join(filter(None, [customer.get("name"), customer.get("surname")])).strip() or "Customer"
        user = {
            "name": full_name,
            "email": customer.get("email") or session.get("customer_email") or "customer@example.com",
            "bookings": parse_int(customer.get("bookings", customer.get("activeBookings", 0)), 0),
            "active": parse_int(customer.get("active", 0), 0),
            "spent": parse_int(customer.get("spent", 0), 0),
        }
        current_order = customer.get("current_order") or {
            "artisan_name": "Jonny Mand",
            "artisan_role": "Electrician",
            "status": "In progress",
            "desc": "Rewiring the kitchen circuit and installing a new distribution board. Arrived on site at 10:30, estimated completion by 14:00.",
        }
    else:
        user = {
            "name": session.get("customer_name") or "Preneil Naidoo",
            "email": session.get("customer_email") or "preneil.naidoo@email.com",
            "bookings": 12,
            "active": 3,
            "spent": 2800,
        }
        current_order = {
            "artisan_name": "Jonny Mand",
            "artisan_role": "Electrician",
            "status": "In progress",
            "desc": "Rewiring the kitchen circuit and installing a new distribution board. Arrived on site at 10:30, estimated completion by 14:00.",
        }

    return render_template("Customer_Profile .html", user=user, current_order=current_order)


app.add_url_rule("/profile", endpoint="profile", view_func=customer_profile, methods=["GET"])
app.add_url_rule("/sign_up", endpoint="sign_up", view_func=customer_sign_up, methods=["GET"])


@app.route("/chat-window")
@app.route("/chat")
def chat_window():
    return render_template("chat-window.html")


@app.route("/artisan-profile")
@app.route("/Artisan_profile")
@app.route("/artisan/<artisan_id>")
def artisan_profile(artisan_id=None):
    if artisan_id is None:
        # prefer an artisan id stored in session (signed-in artisan),
        # then check the query param, otherwise fall back to demo
        artisan_id = request.args.get("artisan_id") or session.get("artisan_id") or "demo-artisan"

    try:
        artisan_response = requests.get(f"{DB_URL_A.rstrip('/')}/artisans/{artisan_id}.json", timeout=10)
        artisan_response.raise_for_status()
        record = artisan_response.json() or {}
    except requests.RequestException:
        record = {}

    artisan = {
        "id": artisan_id,
        "name": record.get("name") or "Artisan",
        "profession": record.get("profession") or "Repair",
        "email": record.get("email") or "",
        "qualification": record.get("qualification") or "Certified professional",
        "hourlyRate": parse_int(record.get("hourlyRate", record.get("rate", 550)), 550),
        "calloutFee": parse_int(record.get("calloutFee", record.get("callout_fee", 250)), 250),
        "available": bool(record.get("available", True)),
        "verified": bool(record.get("verified", True)),
        "status": "Online" if record.get("available", True) else "Offline",
    }
    return render_template("Artisan-login.html", artisan=artisan)


@app.route("/artisan-sign-up", methods=["GET"])
@app.route("/Artisan_sign_up", methods=["GET"])
def artisan_sign_up():
    return render_template("sign_up.html")


@app.route("/send_freelancer_data", methods=["POST"])
@app.route("/Artisan_sign_up", methods=["POST"])
def artisan_sign_up_submit():
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
        resp = requests.post(f"{DB_URL_A.rstrip('/')}/artisans.json", json=freelancer_data, timeout=10)
        resp.raise_for_status()
        result = resp.json() or {}
        artisan_id = result.get("name") if isinstance(result, dict) else None
        if artisan_id:
            set_artisan_session(artisan_id, email=email, name=name)
            return redirect(url_for("artisan_profile", artisan_id=artisan_id))
    except requests.RequestException:
        pass

    return render_template("Artisan-login.html")


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


if __name__ == '__main__':
    app.run()
