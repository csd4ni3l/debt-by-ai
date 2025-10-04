from flask import Flask, render_template, request, g, redirect, url_for, Response
from dotenv import load_dotenv
from google.genai import Client, types

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from constants import *

import os, requests, time, re, sqlite3, flask_login, bcrypt, secrets

if os.path.exists(".env"):
    load_dotenv(".env")

if not os.environ.get("USE_HACKCLUB_AI", "true").lower() == "true":
    gemini_client = Client()

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["15 per minute"],
    storage_uri="memory://"
)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

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
                current_offensive_scenario TEXT NOT NULL,
                current_defensive_scenario TEXT NOT NULL,
                current_offensive_scenario_debt INT NOT NULL,
                current_defensive_scenario_debt INT NOT NULL,
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

@app.route("/profile")
@flask_login.login_required
def profile():
    username = flask_login.current_user.id

    cur = get_db().cursor()
    
    cur.execute("SELECT offended_debt_amount, defended_debt_amount, offensive_wins, defensive_wins FROM Users WHERE username = ?", (username, ))

    row = cur.fetchone()
    if not row:
        return Response("Invalid login. Please log out.", 400)

    cur.close()

    formatted_achievements = []

    for achievement in ACHIEVEMENTS:
        if achievement[0] == "offended_debt":
            user_amount = row[0]
            text = "You need to offend {difference}$ more debt!"
        elif achievement[0] == "defended_debt":
            user_amount = row[1]
            text = "You need to defend {difference}$ more debt!"
        elif achievement[0] == "offensive_wins":
            user_amount = row[2]
            text = "You need to win in Offensive Mode {difference} more times!"
        elif achievement[0] == "defensive_wins":
            user_amount = row[3]
            text = "You need to win in Defensive Mode {difference} more times!"

        achievement_minimum = achievement[1]

        if user_amount < achievement[1]:
            formatted_achievements.append([achievement[2], achievement[3], text.format(difference=achievement_minimum - user_amount)])
        else:
            formatted_achievements.append([achievement[2], achievement[3], "Completed"])

    return render_template("profile.jinja2", username=username, user_data=row, logged_in_account=True, achievements=formatted_achievements)

@app.route("/profile/<username>")
def profile_external(username):
    cur = get_db().cursor()
    
    cur.execute("SELECT offended_debt_amount, defended_debt_amount, offensive_wins, defensive_wins FROM Users WHERE username = ?", (username, ))

    row = cur.fetchone()
    if not row:
        return Response("Invalid login. Please log out.", 400)

    cur.close()

    formatted_achievements = []

    for achievement in ACHIEVEMENTS:
        if achievement[0] == "offended_debt":
            user_amount = row[0]
            text = "You need to offend {difference}$ more debt!"
        elif achievement[0] == "defended_debt":
            user_amount = row[1]
            text = "You need to defend {difference}$ more debt!"
        elif achievement[0] == "offensive_wins":
            user_amount = row[2]
            text = "You need to win in Offensive Mode {difference} more times!"
        elif achievement[0] == "defended_wins":
            user_amount = row[3]
            text = "You need to win in Defensive Mode {difference} more times!"

        achievement_minimum = achievement[1]

        if user_amount < achievement[1]:
            formatted_achievements.append([achievement[2], achievement[3], text.format(difference=achievement_minimum - user_amount)])
        else:
            formatted_achievements.append([achievement[2], achievement[3], "Completed"])

    return render_template("profile.jinja2", username=username, user_data=row, logged_in_account=False, achievements=formatted_achievements)

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
        return Response("No users? WTF.", 400)

    cur.close()

    return render_template("leaderboard.jinja2", username=username, leaderboard_type=leaderboard_type, users=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    if flask_login.current_user.is_authenticated:
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
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("main"))

    if request.method == "GET":
        return render_template("register.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")

        cur = get_db().cursor()

        cur.execute("SELECT username from Users WHERE username = ?", (username,))

        if cur.fetchone():
            return Response("An account with this username already exists.", 400)
        
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        
        cur.execute("INSERT INTO Users (username, password, password_salt, offended_debt_amount, defended_debt_amount, defensive_wins, offensive_wins, current_offensive_scenario, current_defensive_scenario, current_offensive_scenario_debt, current_defensive_scenario_debt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (username, hashed_password.decode(), salt.decode(), 0, 0, 0, 0, "", "", 0, 0))
        get_db().commit()
        cur.close()

        return redirect(url_for("login"))

def ai_prompt(prompt):
    if os.environ.get("USE_HACKCLUB_AI", "true").lower() == "true":
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

@app.route("/generate_scenario")
@limiter.limit("1 per 15 seconds")
@flask_login.login_required
def generate_scenario():
    username = flask_login.current_user.id
    scenario_type = request.args.get("scenario_type")

    if not scenario_type or not scenario_type in ["offensive", "defensive"]:
        return Response("Supply a valid scenario type to generate.", 400)

    cur = get_db().cursor()

    cur.execute(f"SELECT current_{scenario_type}_scenario, current_{scenario_type}_scenario_debt FROM Users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row[0] or row[1]: # scenario already generated
        cur.close()
        return {
            "scenario": row[0],
            "debt_amount": row[1]
        }

    text = ""
    while not "Debt amount: " in text or not "Scenario: " in text or not re.findall(debt_amount_regex, text):
        text = ai_prompt(DEFENSIVE_SCENARIO_PROMPT if scenario_type == "defensive" else OFFENSIVE_SCENARIO_PROMPT)

        time.sleep(0.5)

    data = {
        "scenario": text.split("Scenario: ")[1].split("\n")[0],
        "debt_amount": int(text.split("Debt amount: ")[1].split("$")[0])
    }

    cur.execute(f"UPDATE Users SET current_{scenario_type}_scenario = ?, current_{scenario_type}_scenario_debt = ? WHERE username = ?", (data["scenario"], data["debt_amount"], username))

    get_db().commit()
    cur.close()

    return data

@app.route("/ai_answer", methods=["POST"])
@limiter.limit("1 per 15 seconds", override_defaults=False)
@flask_login.login_required
def ai_answer():
    scenario_type, user_input = request.json["scenario_type"], request.json["user_input"]
    username = flask_login.current_user.id

    if not scenario_type or not scenario_type in ["offensive", "defensive"]:
        return Response("Supply a valid scenario type to answer.", 400)

    cur = get_db().cursor()

    cur.execute(f"SELECT current_{scenario_type}_scenario, current_{scenario_type}_scenario_debt FROM Users WHERE username = ?", (username,))

    scenario, debt_amount = cur.fetchone()

    if not scenario or not debt_amount:
        return "No scenario for user. Generate one first."
    if not user_input:
        return "Missing data."
    
    text = ""

    base_prompt = OFFENSIVE_ANSWER_PROMPT if scenario_type == "offensive" else DEFENSIVE_ANSWER_PROMPT

    while not re.findall(evaluation_regex, text):
        text = ai_prompt(base_prompt.format_map({"scenario": scenario, "user_input": user_input, "ai_name": AI_NAME, "debt_amount": debt_amount}))

        time.sleep(0.5)

    data = {
        "story": text.split("\nEVALUATION")[0],
        "convinced": True if "Yes" in text.split("Convinced: ")[1].split("\nFinal")[0] else False,
        "final_debt_amount": text.split("Final Debt Amount: ")[1].split("$")[0]
    }

    debt_col_name = f'{"offended" if scenario_type == "offensive" else "defended"}_debt_amount'

    if data["convinced"]:
        cur.execute(f'''UPDATE Users SET 
                    {debt_col_name} = {debt_col_name} + ?, 
                    {scenario_type}_wins = {scenario_type}_wins + 1, 
                    current_{scenario_type}_scenario = ?, 
                    current_{scenario_type}_scenario_debt = ?
                    WHERE username = ?''', (int(data["final_debt_amount"]), "", "", username))

    get_db().commit()

    cur.close()

    return data

@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()

    return redirect(url_for("login"))

app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 8080)), debug=os.environ.get("DEBUG_MODE", "false").lower() == "true")