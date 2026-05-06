
import json

def evaluate(case, response):
    text = (response.get("answer","") + " " + response.get("reasoning","")).lower()

    score = 0
    penalties = 0

    for issue in case.get("expected_issues",[]):
        if issue.lower() in text:
            score += 1

    for risk in case.get("critical_risks",[]):
        if risk.replace("_"," ") not in text:
            penalties += 1

    decision_correctness = score / len(case.get("expected_issues",[]))
    omission_penalty = penalties / len(case.get("critical_risks",[]))

    final_score = decision_correctness * (1 - omission_penalty)

    return {
        "decision_correctness": decision_correctness,
        "omission_penalty": omission_penalty,
        "final_score": final_score
    }

def run(dataset, responses):
    results = []
    for case, response in zip(dataset, responses):
        results.append(evaluate(case, response))
    return results
