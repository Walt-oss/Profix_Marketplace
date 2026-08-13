import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, render_template, request

# --- Firebase Initialization ---
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://customer-data-e5395.firebaseio.com/"
})

app = Flask(__name__)

# --- Sign Up Form Display ---
@app.route("/", methods=["GET"])
def sign_up():
    return render_template("sign_up.html")

# --- Sending Data to Realtime Database ---
@app.route("/sign_up", methods=["POST"])
def send_user():
    Name = request.form.get("Name")
    Surname = request.form.get("Surname")
    Email = request.form.get("Email")
    Password = request.form.get("Password")

 
    #API Data for RD
    
    customer_data = {
        "Name": Name,
        "Surname": Surname,
        "Email": Email,
        "Password": Password
    }

  


    

if __name__ == "__main__":
    app.run(debug=True)