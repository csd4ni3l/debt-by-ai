from flask import Flask, render_template, request, g, redirect, url_for, Response
from dotenv import load_dotenv
from google.genai import Client, types

from constants import OFFENSIVE_SCENARIO_PROMPT, OFFENSIVE_ANSWER_PROMPT, DEFENSIVE_SCENARIO_PROMPT, DEFENSIVE_ANSWER_PROMPT, debt_amount_regex, evaluation_regex, AI_NAME

import os, requests, time, re, sqlite3, flask_login, bcrypt, secrets

load_dotenv(".env")

if not os.environ["USE_HACKCLUB_AI"]:
    gemini_client = Client()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect(os.environ.get("DB_FILE", "data.db"))
        db.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                username TEXT PRIMARY KEY,
                offended_debt_amount INT NOT NULL,
                defended_debt_amount INT NOT NULL,
                defensive_wins INT NOT NULL,
                offensive_wins INT NOT NULL,
                password TEXT NOT NULL,
                password_salt TEXT NOT NULL
            )
        """)

    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(user_id):
    user = User()
    user.id = user_id
    return user

@login_manager.unauthorized_handler
def unathorized_handler():
    return redirect(url_for("login"))

@app.route("/")
@flask_login.login_required
def main():
    username = flask_login.current_user.id
    return render_template("index.jinja2", username=username)

@app.route("/offensive")
@flask_login.login_required
def offensive_mode():
    username = flask_login.current_user.id
    return render_template("offensive.jinja2", ai_name=AI_NAME, username=username)

@app.route("/defensive")
@flask_login.login_required
def defensive_mode():
    username = flask_login.current_user.id
    return render_template("defensive.jinja2", ai_name=AI_NAME, username=username)

@app.route("/leaderboard")
@flask_login.login_required
def leaderboard():
    username = flask_login.current_user.id
    leaderboard_type = request.args.get("leaderboard_type", "offended_debt_amount")

    cur = get_db().cursor()

    if leaderboard_type == "offended_debt_amount":
        leaderboard_type = "Offended Debt Amount"
        cur.execute("SELECT offended_debt_amount, username FROM Users ORDER BY offended_debt_amount DESC")
    elif leaderboard_type == "defended_debt_amount":
        leaderboard_type = "Defended Debt Amount"
        cur.execute("SELECT defended_debt_amount, username FROM Users ORDER BY defended_debt_amount DESC")
    elif leaderboard_type == "offensive_wins":
        leaderboard_type = "Offensive Wins"
        cur.execute("SELECT offensive_wins, username FROM Users ORDER BY offensive_wins DESC")
    elif leaderboard_type == "defensive_wins":
        leaderboard_type = "Defensive Wins"
        cur.execute("SELECT defensive_wins, username FROM Users ORDER BY defensive_wins DESC")

    rows = cur.fetchall()
    if not rows:
        cur.close()

    return render_template("leaderboard.jinja2", username=username, leaderboard_type=leaderboard_type, users=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    if hasattr(flask_login.current_user, "id"):
        return redirect(url_for("main"))

    if request.method == "GET":
        return render_template("login.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")

        cur = get_db().cursor()

        cur.execute("SELECT password, password_salt FROM Users WHERE username = ?", (username,))

        row = cur.fetchone()
        if not row:
            cur.close()
            return redirect(url_for("login"))
        
        hashed_password, salt = row

        if secrets.compare_digest(bcrypt.hashpw(password.encode(), salt.encode()), hashed_password.encode()):
            cur.close()

            user = User()
            user.id = username
            flask_login.login_user(user, remember=True)

            return redirect(url_for("main"))
        else:
            cur.close()
            return Response("Unathorized", 401)

@app.route("/register", methods=["GET", "POST"])
def register():
    if hasattr(flask_login.current_user, "id"):
        return redirect(url_for("main"))

    if request.method == "GET":
        return render_template("register.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")

        cur = get_db().cursor()

        cur.execute("SELECT username from Users WHERE username = ?", (username,))

        if cur.fetchone():
            return Response("An Account with this username already exists.", 400)
        
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        
        cur.execute("INSERT INTO Users (username, password, password_salt, offended_debt_amount, defended_debt_amount, defensive_wins, offensive_wins) VALUES (?, ?, ?, ?, ?, ?, ?)", (username, hashed_password.decode(), salt.decode(), 0, 0, 0, 0))
        get_db().commit()
        cur.close()

        return redirect(url_for("login"))

def ai_prompt(prompt):
    if os.environ["USE_HACKCLUB_AI"]:
        response = requests.post(
            "https://ai.hackclub.com/chat/completions", 
            headers={"Content-Type": "application/json"},
            json={"messages": [{"role": "user", "content": prompt}]}
        )
        return re.sub(r'<think>.*?</think>', '', response.json()["choices"][0]["message"]["content"].replace("'''", ''), flags=re.DOTALL)
    else:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            )
        )

        return response.text.replace("'''", '')

@app.route("/defensive_scenario")
@flask_login.login_required
def defensive_scenario():
    text = ""

    while not "Debt amount: " in text or not "Scenario: " in text or not re.findall(debt_amount_regex, text):
        text = ai_prompt(DEFENSIVE_SCENARIO_PROMPT)

        time.sleep(0.5)

    return {
        "scenario": text.split("Scenario: ")[1].split("\n")[0],
        "debt_amount": int(text.split("Debt amount: ")[1].split("$")[0])
    }

@app.route("/offensive_scenario")
@flask_login.login_required
def offensive_scenario():
    text = ""

    while not "Debt amount: " in text or not "Scenario: " in text or not re.findall(debt_amount_regex, text):
        text = ai_prompt(OFFENSIVE_SCENARIO_PROMPT)

        time.sleep(0.5)

    return {
        "scenario": text.split("Scenario: ")[1].split("\n")[0],
        "debt_amount": int(text.split("Debt amount: ")[1].split("$")[0])
    }

@app.route("/offensive_answer", methods=["POST"])
@flask_login.login_required
def offensive_answer():
    scenario, user_input = request.json['scenario'], request.json["user_input"]

    if not scenario or not user_input:
        return "Missing data."
    
    text = ""

    while not re.findall(evaluation_regex, text):
        text = ai_prompt(OFFENSIVE_ANSWER_PROMPT.format_map({"scenario": scenario, "user_input": user_input, "ai_name": AI_NAME}))

        time.sleep(0.5)

    return {
        "story": text.split("\nEVALUATION")[0],
        "convinced": True if "Yes" in text.split("Convinced: ")[1].split("\nFinal")[0] else False,
        "final_debt_amount": text.split("Final Debt Amount: ")[1].split("$")[0]
    }

@app.route("/defensive_answer", methods=["POST"])
@flask_login.login_required
def defensive_answer():
    scenario, user_input = request.json['scenario'], request.json["user_input"]

    if not scenario or not user_input:
        return "Missing data."
    
    text = ""

    while not re.findall(evaluation_regex, text):
        text = ai_prompt(DEFENSIVE_ANSWER_PROMPT.format_map({"scenario": scenario, "user_input": user_input, "ai_name": AI_NAME}))

        time.sleep(0.5)

    return {
        "story": text.split("\nEVALUATION")[0],
        "convinced": True if "Yes" in text.split("Convinced: ")[1].split("\nFinal")[0] else False,
        "final_debt_amount": text.split("Final Debt Amount: ")[1].split("$")[0]
    }

app.run(host=os.environ.get("HOST", "0.0.0.0"), port=os.environ.get("PORT", 8080), debug=os.environ.get("DEBUG_MODE", False))