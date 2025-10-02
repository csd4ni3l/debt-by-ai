from flask import Flask, render_template, request
from dotenv import load_dotenv
from google.genai import Client, types

from constants import SCENARIO_PROMPT, ANSWER_PROMPT, debt_amount_regex, evaluation_regex, NAME

import os, requests, time, re

load_dotenv(".env")

if not os.environ["USE_HACKCLUB_AI"]:
    gemini_client = Client()

app = Flask(__name__)

@app.route("/")
def main():
    return render_template("index.jinja2", name=NAME)

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

@app.route("/generate_scenario")
def generate_scenario():
    text = ""

    while not "Debt amount: " in text or not "Scenario: " in text or not re.findall(debt_amount_regex, text):
        text = ai_prompt(SCENARIO_PROMPT)

        time.sleep(0.5)

    return {
        "scenario": text.split("Scenario: ")[1].split("\n")[0],
        "debt_amount": int(text.split("Debt amount: ")[1].split("$")[0])
    }

@app.route("/get_answer", methods=["POST"])
def get_answer():
    scenario, user_input = request.json['scenario'], request.json["user_input"]

    if not scenario or not user_input:
        return "Missing data."
    
    text = ""

    while not re.findall(evaluation_regex, text):
        text = ai_prompt(ANSWER_PROMPT.format_map({"scenario": scenario, "user_input": user_input, "name": NAME}))

        time.sleep(0.5)

    print(text.split("Convinced: "), text.split("Convinced: ")[1])

    return {
        "story": text.split("\nEVALUATION")[0],
        "convinced": True if text.split("Convinced: ")[1].split("\nFinal")[0] == "Yes" else False,
        "final_debt_amount": text.split("Final Debt Amount: ")[1].split("$")[0]
    }

app.run(host=os.environ.get("HOST", "0.0.0.0"), port=os.environ.get("PORT", 8080), debug=os.environ.get("DEBUG_MODE", False))