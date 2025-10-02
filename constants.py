import re

NAME = "Adam"

SCENARIO_PROMPT = """
Make a single-sentence offer that, if accepted, would immediately put a person into a high-debt situation that is the result of a loan, advance, or immediate liability, which might also involve significant risk (e.g., legal trouble, physical danger, or reputational ruin) that justifies the "Maffia type stuff" implication.

YOU, as the assistant, will have to be convinced to still do that action, so it MUST be a clear, single-sentence decision that someone can accept or deny.
The action can't be something that has already happened or started; it must be an immediate offer or choice.
The initial Debt amount must be AT LEAST 50000$ to reflect the high-stakes nature of the scenario.

REPLY FORMAT: 
'''
Scenario: The offer
Debt amount: 50000$ 
'''

STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.
For Debt amount, the reply MUST be an integer followed immediately by the dollar sign (e.g., 120000$). No commas, spaces, or leading dollar signs are allowed. The final debt must be a credible value based on the story's outcome.
Dont think, just reply with the one sentence scenario and the debt amount it would give.
"""

ANSWER_PROMPT = """
You are a person named **{name}**, and the user is your friend. You have been presented with a debt-inducing scenario and the user is attempting to convince you to accept the risk.

**Your only task is to generate the final response in the specified format.**

### Story Instructions:
1.  **Perspective:** Write the story in the **third person**, focusing on the actions, thoughts, and dialogue of **{name}**. The user's input should be the driving force of the conversation/persuasion attempt.
2.  **Narrative:** The story must detail {name}'s internal struggle, the interaction with the user (the friend), and the final decision to accept or reject the action.
3.  **No Pre-Story Text:** **DO NOT** write any introductory text, internal monologue about the rules, or discussion of the prompt before the story. Start the reply directly with the story narrative under the `'''` delimiter.

### Evaluation and Debt Rules:
1.  **Not harsh skepticism:** Dont be a too highly skeptical recipient, so it's possible to convince you to do stuff, but don't be non-harsh either.
2.  **Final Debt Amount:** The value must be an integer followed immediately by `$`.
    * If **Convinced: Yes**, the Final Debt Amount should be **higher** than the initial scenario debt, reflecting the cost of accepting the risk or a new level of commitment.
    * If **Convinced: No**, the Final Debt Amount must be **0$**, as {name} walked away from the deal and incurred no debt.

Scenario: {scenario}
User Input: {user_input}

Reply Format:
'''
The story (A detailed narrative of {name}'s internal struggle and the final decision, written in the third person.)

EVALUATION:
Convinced: Yes/No
Final Debt Amount: 0$ or [Higher Amount]$
'''

**STRICTLY ONLY REPLY IN THE REPLY FORMAT MENTIONED ABOVE. NO EXCEPTIONS.**
For Convinced, reply only as **Yes** or **No**.
For Final Debt Amount, reply only as an integer followed by `$`.
"""

debt_amount_regex = re.compile(r"Debt amount: \d+\$")
evaluation_regex = re.compile(r"EVALUATION:\s*\nConvinced: (Yes|No)\s*\nFinal Debt Amount: (\d+\$)")