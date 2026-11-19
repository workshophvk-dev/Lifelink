"""'AI' logic: triage, donor ranking, demand forecast, FAQ assistant.
Deterministic and explainable, which suits medical use.
Replace assistant() with an LLM API call when you are ready."""
import math
import re

COMPAT = {
    "O-": ["O-"], "O+": ["O-", "O+"], "A-": ["O-", "A-"], "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"], "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}
HOSPITAL = {"x": 50, "y": 50}


def triage(text=""):
    t = (text or "").lower()
    if re.search(r"accident|bleed|hemorrh|emergency|icu|now|critical|trauma|immediate|urgent", t):
        return "critical"
    if re.search(r"surgery|operation|delivery|transfusion|thalass|anemi|cancer", t):
        return "moderate"
    return "low" if t.strip() else None


def rank(group, urgency, donors):
    w_d = {"critical": 0.5, "moderate": 0.35, "low": 0.25}.get(urgency, 0.35)
    w_e = 0.25
    w_c = 1 - w_d - w_e
    out = []
    for d in donors:
        if d["group"] not in COMPAT[group] or d["lastDonationDays"] < 90:
            continue
        km = math.hypot(d["x"] - HOSPITAL["x"], d["y"] - HOSPITAL["y"]) * 0.4
        s = max(0, 1 - km / 40)                                   # distance
        e = min(1, (d["lastDonationDays"] - 90) / 180 + 0.4)      # eligibility / rest time
        c = 1 if d["group"] == group else 0.7                     # exact-match bonus
        out.append({
            "id": d["id"], "name": d["name"], "g": d["group"], "x": d["x"], "y": d["y"],
            "last": d["lastDonationDays"], "km": km, "s": s, "e": e, "c": c,
            "score": round(100 * (w_d * s + w_e * e + w_c * c)),
        })
    return sorted(out, key=lambda r: r["score"], reverse=True)


def forecast(series, stock):
    """Least-squares trend on the last 6 months, projected 3 months ahead."""
    n = 6
    ys = series[-n:]
    xs = list(range(n))
    mx, my = (n - 1) / 2, sum(ys) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    nxt = [round(my + slope * (n - 1 + k - mx)) for k in (1, 2, 3)]
    bad = next((i for i, v in enumerate(nxt) if v > stock), -1)
    return {"history": series, "forecast": nxt, "stock": stock, "shortageMonthIndex": bad}


KB = [
    (r"tattoo|piercing", "Most guidelines ask you to wait about 6 to 12 months after a tattoo or piercing. Please confirm the exact period with the blood bank."),
    (r"age|old|young", "In India, donors are usually aged 18 to 65 and weigh at least 45 kg."),
    (r"weight|kg", "You generally need to weigh at least 45 kg and have haemoglobin of 12.5 g/dL or more."),
    (r"often|gap|again|interval|how many times", "Men can usually donate whole blood every 3 months and women every 4 months."),
    (r"fever|cold|flu|sick|ill", "Wait until you are fully recovered and off antibiotics before donating."),
    (r"pregnan|breastfeed|period", "Pregnant and recently delivered women should not donate. Ask a doctor about breastfeeding and menstruation."),
    (r"diabet|sugar|bp|pressure|heart", "Well-controlled conditions may be acceptable, but a doctor at the centre makes the decision on the day."),
    (r"body|pledge|organ", "Body donation is pledged by registering and informing your family. The medical college needs family consent at the time of death, usually within a few hours."),
    (r"eat|food|prepare|before", "Eat a light meal, drink plenty of water, and sleep well before donating."),
    (r"hello|hi|hey", "Hello! Ask me about donor eligibility, tattoos, how often you can give, or body donation."),
]


def assistant(question=""):
    q = (question or "").lower()
    for pattern, answer in KB:
        if re.search(pattern, q):
            return answer
    return "I'm not sure about that one. Please ask the blood bank or a doctor."
