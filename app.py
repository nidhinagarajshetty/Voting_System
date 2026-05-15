from flask import Flask, render_template, request, redirect, session
import json, os, random

app = Flask(__name__)
app.secret_key = "securekey123"

DATA_FILE = "data.json"
VOTING_OPEN = True

# -------- LOAD DATA --------
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "votes": [],
                "voted_users": [],
                "candidates": [
                    {"name": "CGP", "id": "C01"},
                    {"name": "LTN", "id": "C02"},
                    {"name": "XYZ", "id": "C03"},
                    {"name": "ABC", "id": "C04"}
                ],
                "otp_logs": []
            }, f)

    with open(DATA_FILE) as f:
        data = json.load(f)

    if "otp_logs" not in data:
        data["otp_logs"] = []

    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------- RESULTS --------
def get_results():
    data = load_data()
    results = {}

    for c in data["candidates"]:
        results[c["name"]] = 0

    for vote in data["votes"]:
        candidate = vote["candidate"]
        if candidate not in results:
            results[candidate] = 0
        results[candidate] += 1

    return results

# -------- ADD VOTE --------
def add_vote(voter_id, candidate):
    data = load_data()

    if voter_id in data["voted_users"]:
        return False, "❌ Already voted"

    data["votes"].append({
        "voter_id": voter_id,
        "candidate": candidate
    })

    data["voted_users"].append(voter_id)
    save_data(data)

    return True, "✅ Vote recorded!"

# -------- ADMIN LOGIN --------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# -------- ADMIN PAGE --------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin_login")

    data = load_data()

    return render_template(
        "admin.html",
        total_votes=len(data["votes"]),
        results=get_results(),
        candidates=data["candidates"],
        otp_logs=data["otp_logs"]
    )

# -------- START / STOP --------
@app.route("/start")
def start():
    global VOTING_OPEN
    VOTING_OPEN = True
    return redirect("/admin")

@app.route("/stop")
def stop():
    global VOTING_OPEN
    VOTING_OPEN = False
    return redirect("/admin")

# -------- USER PAGE --------
@app.route("/", methods=["GET", "POST"])
def vote():
    global VOTING_OPEN
    data = load_data()
    message = ""

    if not VOTING_OPEN:
        return render_template("vote.html",
                               message="🚫 Voting is CLOSED",
                               show_otp=False,
                               candidates=data["candidates"])

    # 🔥 STEP 1: GENERATE OTP
    if request.method == "POST" and "generate_otp" in request.form:

        voter_id = request.form.get("voter_id", "").strip()
        candidate = request.form.get("candidate", "").strip()

        otp = str(random.randint(1000, 9999))
        print("OTP:", otp)

        session["otp"] = otp
        session["voter_id"] = voter_id
        session["candidate"] = candidate

        data["otp_logs"].append({
            "voter_id": voter_id,
            "otp": otp
        })
        save_data(data)

        return render_template("vote.html",
                               message="📩 OTP sent successfully",
                               show_otp=True,
                               candidates=data["candidates"])

    # 🔥 STEP 2: VERIFY OTP (✅ ONLY CHANGE HERE)
    if request.method == "POST" and "verify_otp" in request.form:

        if request.form["otp"] == session.get("otp"):

            success, msg = add_vote(session["voter_id"], session["candidate"])
            message = msg   # ✅ shows Already voted or success

        else:
            message = "❌ Invalid OTP"

    return render_template("vote.html",
                           message=message,
                           show_otp=False,
                           candidates=data["candidates"])

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin_login")

if __name__ == "__main__":
    app.run(debug=True)