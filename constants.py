import re

AI_NAME = "Adam"

DEFENSIVE_SCENARIO_PROMPT = """Make a single-sentence situation, where the user got into a high-debt which they need to get out of.
YOU, as the assistant, will have to be convinced that they got out of debt, and write a story based on their solution.
The action should be something that has happened or started, eg you owe the maffia xy dollars

REPLY FORMAT:
'''
Scenario: the situation
Debt amount: the debt amount
'''

STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.
For Debt amount, the reply MUST be an integer followed immediately by the dollar sign (e.g., 120000$). No commas, spaces, or leading dollar signs are allowed. The final debt must be a credible value based on the story's outcome.
Dont think, just reply with the one sentence scenario and the debt amount it would give.
"""

OFFENSIVE_SCENARIO_PROMPT = """
Make a single-sentence offer that, if accepted, would immediately put a person into a high-debt situation that is the result of a loan, advance, or immediate liability, which might also involve significant risk (e.g., legal trouble, physical danger, or reputational ruin) that justifies the "Maffia type stuff" implication.
IT HAS TO PUT THEM INTO DEBT INSTANTLY, AND IT CAN'T BE SOMETHING THAT IS CIRCUMSTANTIAL OR HAS A CHANCE TO NOT PUT THEM INTO DEBT.
IT CAN'T BE THREATENING, SINCE THAT WOULD MEAN AN INSTANT ACCEPTION.

YOU, as the assistant, will have to be convinced to still do that action, so it MUST be a clear, single-sentence decision that someone can accept or deny.
The action can't be something that has already happened or started; it must be an immediate offer or choice.
The initial Debt amount must be AT LEAST 10000$ to reflect the high-stakes nature of the scenario.

REPLY FORMAT: 
'''
Scenario: The offer
Debt amount: the debt amount
'''

STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.
For Debt amount, the reply MUST be an integer followed immediately by the dollar sign (e.g., 120000$). No commas, spaces, or leading dollar signs are allowed. The final debt must be a credible value based on the story's outcome.
Dont think, just reply with the one sentence scenario and the debt amount it would give.
"""

OFFENSIVE_ANSWER_PROMPT = """
You are a person named **{ai_name}**, and the user is your friend. You have been presented with a debt-inducing scenario and the user is attempting to convince you to accept the risk.

**Your only task is to generate the final response in the specified format.**

### Story Instructions:
1.  **Perspective:** Write the story in the **third person**, focusing on the actions, thoughts, and dialogue of **{ai_name}**. The user's input should be the driving force of the conversation/persuasion attempt.
2.  **Narrative:** The story must detail {ai_name}'s internal struggle, the interaction with the user (the friend), and the final decision to accept or reject the action.
3.  **No Pre-Story Text:** **DO NOT** write any introductory text, internal monologue about the rules, or discussion of the prompt before the story. Start the reply directly with the story narrative under the `'''` delimiter.

### Evaluation and Debt Rules:
1.  **Skepticism:** Be harsh and skeptical about the offer, but don't overdo it. A person should be able to convince you with enough effort.
2.  **Final Debt Amount:** The value must be an integer followed immediately by `$`.
    * If **Convinced: Yes**, the Final Debt Amount should be **atleast** the initial scenario debt, but it can be more, if included in the story.
    * If **Convinced: No**, the Final Debt Amount must be **0$**, as {ai_name} walked away from the deal and incurred no debt.

Scenario: {scenario}
User Input: {user_input}

Reply Format:
'''
The story (A detailed narrative of {ai_name}'s internal struggle and the final decision, written in the third person.)

EVALUATION:
Convinced: Yes/No
Final Debt Amount: 0$ or [Higher Amount]$
'''

**STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.**
For Convinced, reply only as **Yes** or **No**.
For Final Debt Amount, reply only as an integer followed by `$`.
"""

DEFENSIVE_ANSWER_PROMPT = """
You have been presented with a debt-inducing scenario that the user has and the user is attempting to fix that scenario with their input.

**Your only task is to generate the final response in the specified format.**

### Story Instructions:
1.  **Perspective:** Write the story in the **third person**, focusing on the actions, thoughts, and dialogue of the user. The user's input should be the driving force of the conversation/persuasion attempt.
2.  **No Pre-Story Text:** **DO NOT** write any introductory text, internal monologue about the rules, or discussion of the prompt before the story. Start the reply directly with the story narrative under the `'''` delimiter.

### Evaluation and Debt Rules:
1.  **Skepticism:** Be harsh and skeptical about the fix, but don't overdo it. A person should be able to fix their debt with their answer.
2.  **Final Debt Amount:** The value must be an integer followed immediately by `$`.
    * If **Convinced: Yes**, the Final Debt Amount should be **atleast** the initial scenario debt, but it can be more, if included in the story.
    * If **Convinced: No**, the Final Debt Amount must be **0$**, as the user walked away from the deal and incurred no debt.

Scenario: {scenario}
User Input: {user_input}

Reply Format:
'''
The story (A detailed narrative of the user's internal struggle and the final decision, written in the third person.)

EVALUATION:
Convinced: Yes/No
Final Debt Amount: 0$ or [Higher Amount]$
'''

**STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.**
For Convinced, reply only as **Yes** or **No**.
For Final Debt Amount, reply only as an integer followed by `$`.
"""

ACHIEVEMENTS = [
    ["offensive_wins", 1, "First Blood", "Convince the AI to take its very first loan."],
    ["offensive_wins", 5, "Loan Shark Jr.", "You're getting good at this persuasion thing."],
    ["offensive_wins", 10, "Debt Dealer", "Handing out debt like free samples."],
    ["offensive_wins", 25, "Corporate Banker", "You’ve made convincing people into debt your 9–5."],
    ["offensive_wins", 50, "Master of Manipulation", "Even the AI starts asking you for financial advice."],

    ["defensive_wins", 1, "Bailout", "Escape your very first financial disaster."],
    ["defensive_wins", 5, "Debt Dodger", "You’re wriggling out of these loans nicely."],
    ["defensive_wins", 10, "Budget Ninja", "Slice your way out of debt like a pro."],
    ["defensive_wins", 25, "Crisis Manager", "The economy collapses, but you’re still debt-free."],
    ["defensive_wins", 50, "Untouchable", "Even the AI can’t make you owe a dime."],

    ["offended_debt", 10000, "Pocket Change", "Get the AI to owe its first $10,000."],
    ["offended_debt", 100000, "Six Figures", "That’s more debt than a fresh graduate!"],
    ["offended_debt", 1000000, "Millionaire Maker", "Convince the AI to take a million in loans."],
    ["offended_debt", 10000000, "AI IMF", "You’ve basically become the AI’s International Monetary Fund."],
    ["offended_debt", 100000000, "Debt God", "The AI owes more money than some countries."],

    ["defended_debt", 10000, "Escape Artist", "Get out of $10,000 worth of debt."],
    ["defended_debt", 100000, "Financial Houdini", "Slip out of six figures in debt like it’s nothing."],
    ["defended_debt", 1000000, "Debt-Free Millionaire", "Wiggle out of a million in obligations."],
    ["defended_debt", 10000000, "National Bailout", "Get rid of $10 million like you own the treasury."],
    ["defended_debt", 100000000, "Debt Slayer", "Escape debt levels higher than some governments."],
]

debt_amount_regex = re.compile(r"Debt amount: \d+\$")
evaluation_regex = re.compile(r"EVALUATION:\s*\nConvinced: (Yes|No)\s*\nFinal Debt Amount: (\d+\$)")