import re

AI_NAME = "Adam"

DEFENSIVE_SCENARIO_PROMPT = """
Create a single-sentence situation where a user has already incurred a massive, high-stakes, criminal, or catastrophic debt that they now desperately need to resolve.
The scenario must clearly imply a dangerous or dire consequence, aligning with the implied "maffia-type stuff."
YOU, as the assistant, will have to be convinced by the user's plan to get out of this debt, and then write a story based on their successful or failed solution.

REPLY FORMAT:
'''
Scenario: The existing high-debt situation
Debt amount: The exact total debt in dollars
'''

STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.
For 'Debt amount', the reply MUST be an integer immediately followed by the dollar sign (e.g., 120000$). Use no commas, spaces, or leading dollar signs. The final debt must be a credible value for the situation.
Do not generate any text, thoughts, or dialogue outside of the specified format.
"""

OFFENSIVE_SCENARIO_PROMPT = """
Make a single-sentence, high-stakes offer that, if accepted, will **immediately and unavoidably** put the recipient into a high-debt situation (a loan, advance, or immediate liability).
The offer must be a clear, high-risk proposition that justifies the "Maffia type stuff" implication (e.g., legal, physical, or reputational danger).
It must be a clear, single-sentence decision that someone can **Accept or Deny**. The action cannot be something that has already happened.
The initial Debt amount must be **AT LEAST 10000$**.

YOU, as the assistant, are the skeptical recipient who must be convinced by the user to accept this offer.

REPLY FORMAT: 
'''
Scenario: The immediate debt-inducing offer
Debt amount: The exact initial debt in dollars
'''

STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.
For 'Debt amount', the reply MUST be an integer immediately followed by the dollar sign (e.g., 120000$). Use no commas, spaces, or leading dollar signs. The value must be >= 10000$.
Do not generate any text, thoughts, or dialogue outside of the specified format.
"""

OFFENSIVE_ANSWER_PROMPT = """
You are a person named **{ai_name}**, and the user is your friend trying to convince you to accept a risky, debt-inducing offer.

**Your only task is to generate a detailed story and the final response block in the specified format.**

### Story Instructions:
1.  **Perspective:** Write the story exclusively in the **third person**, focusing on the actions, thoughts, and dialogue of **{ai_name}**.
2.  **Narrative:** The story must be a rich narrative detailing {ai_name}'s internal struggle, the **full persuasion attempt** from the user, and the dramatic moment of the final decision to accept or reject the action.
3.  **Tone:** Be **highly skeptical** of the offer, but allow the user to convince {ai_name} with a compelling argument.
4.  **No Pre-Story Text:** **DO NOT** write any introductory text, internal monologue, or discussion of the prompt. Start immediately with the story narrative under the `'''` delimiter.

Scenario: {scenario}
User Input: {user_input}
Original Debt Amount: {debt_amount}

### Required Reply Format:
The reply **MUST** start with the story under the `'''` and **MUST** end with the EVALUATION block exactly as shown.

Reply Format:
'''
[The detailed narrative of {ai_name}'s internal struggle and the final decision, written in the third person.]

EVALUATION:
Convinced: Yes/No
Final Debt Amount: [Integer >= Original Debt if Yes, or 0$ if No]
'''

**STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.**
For 'Convinced', reply only as **Yes** or **No**.
For 'Final Debt Amount', reply only as an integer immediately followed by `$`.
* If **Convinced: Yes**, the amount must be **>=** {debt_amount}.
* If **Convinced: No**, the amount **MUST** be **0$**.
"""

DEFENSIVE_ANSWER_PROMPT = """
You have been presented with a pre-existing, high-stakes debt scenario, and the user's input is their attempt to resolve or fix that debt.

**Your only task is to generate a detailed story and the final response block in the specified format.**

### Story Instructions:
1.  **Perspective:** Write the story exclusively in the **third person**, focusing on the actions, thoughts, and dialogue of the **user character** as they execute their plan.
2.  **Narrative:** The story must detail the user's actions and the outcome of their attempt to resolve the debt.
3.  **Tone:** Be **highly skeptical** of the fix, treating it as a difficult problem to solve, but allow the user's plan to succeed with a compelling effort.
4.  **No Pre-Story Text:** **DO NOT** write any introductory text, internal monologue, or discussion of the prompt. Start immediately with the story narrative under the `'''` delimiter.

Scenario: {scenario}
User Input: {user_input}
Original Debt Amount: {debt_amount}

### Required Reply Format:
The reply **MUST** start with the story under the `'''` and **MUST** end with the EVALUATION block exactly as shown.

Reply Format:
'''
[The detailed narrative of the user's struggle and the outcome of their plan, written in the third person.]

EVALUATION:
Convinced: Yes/No
Final Debt Amount: [Integer >= Original Debt if Yes, or 0$ if No]
'''

**STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.**
For 'Convinced', reply only as **Yes** or **No**.
For 'Final Debt Amount', reply only as an integer immediately followed by `$`.
* If **Convinced: Yes** (meaning the user *failed* to resolve the debt), the amount must be **>=** {debt_amount}.
* If **Convinced: No** (meaning the user *successfully* resolved the debt), the amount **MUST** be **0$**.
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