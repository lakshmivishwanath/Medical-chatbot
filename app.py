from flask import Flask, request, jsonify
import sqlite3
import spacy
import re

app = Flask(__name__)

# ================= NLP (LIGHT & FAST) =================
nlp = spacy.load(
    "en_core_web_sm",
    disable=["parser", "tagger", "lemmatizer"]
)

# ================= DATABASE =================
conn = sqlite3.connect("friend_database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    symptoms TEXT,
    possible_condition TEXT,
    precautions TEXT
)
""")
conn.commit()

# ================= RULES =================

SYMPTOMS_LIST = ["fever", "headache", "cough", "cold", "sore throat", "body pain"]

CONDITION_RULES = {
    ("fever", "headache"): "Possible viral infection",
    ("fever", "cough"): "Possible flu-like illness",
    ("cold", "cough"): "Possible common cold"
}

PRECAUTIONS = {
    "fever": [
        "Drink plenty of fluids",
        "Take adequate rest",
        "Monitor body temperature"
    ],
    "headache": [
        "Reduce screen time",
        "Rest in a quiet room",
        "Stay hydrated"
    ],
    "cough": [
        "Drink warm fluids",
        "Avoid cold drinks",
        "Cover mouth while coughing"
    ],
    "cold": [
        "Keep yourself warm",
        "Avoid cold food",
        "Use warm water for drinking"
    ]
}

# ================= NLP EXTRACTION =================
def extract_details(text):
    doc = nlp(text)

    name = None
    age = None
    found_symptoms = []

    # Name
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text

    # Age
    age_match = re.search(r'(\d{1,3})\s*(years|year|yrs)?', text.lower())
    if age_match:
        age = int(age_match.group(1))

    # Symptoms
    text_lower = text.lower()
    for s in SYMPTOMS_LIST:
        if s in text_lower:
            found_symptoms.append(s)

    return name, age, found_symptoms

# ================= CONDITION LOGIC =================
def infer_condition(symptoms):
    for rule, condition in CONDITION_RULES.items():
        if all(r in symptoms for r in rule):
            return condition
    if symptoms:
        return "General health issue (needs medical evaluation)"
    return "Not enough information"

# ================= PRECAUTION LOGIC =================
def infer_precautions(symptoms):
    tips = []
    for s in symptoms:
        tips.extend(PRECAUTIONS.get(s, []))
    if not tips:
        tips.append("Please consult a doctor for proper evaluation")
    return list(set(tips))

# ================= CHAT =================
@app.route("/", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user_text = request.json.get("message", "")

        name, age, symptoms = extract_details(user_text)
        condition = infer_condition(symptoms)
        precautions = infer_precautions(symptoms)

        report_text = f"""
Health Summary
--------------
Name: {name if name else "Not provided"}
Age: {age if age else "Not provided"}
Symptoms: {", ".join(symptoms) if symptoms else "Not clearly mentioned"}

Possible Condition:
{condition}

General Precautions:
- """ + "\n- ".join(precautions) + """

⚠️ Disclaimer:
This chatbot provides general health information only.
It is NOT a medical diagnosis.
Please consult a healthcare professional if symptoms persist.
"""

        # Save to DB
        cursor.execute(
            "INSERT INTO reports (name, age, symptoms, possible_condition, precautions) VALUES (?,?,?,?,?)",
            (
                name,
                age,
                ", ".join(symptoms),
                condition,
                "; ".join(precautions)
            )
        )
        conn.commit()

        return jsonify({"reply": report_text})

    # ---------- SIMPLE UI ----------
    return """
<!DOCTYPE html>
<html>
<head>
<title>NLP Medical Chatbot</title>
</head>
<body>
<h2>NLP Medical Chatbot</h2>
<div id="chat"></div>
<input id="input" placeholder="Describe your health problem..." style="width:70%;">
<button onclick="send()">Send</button>
<br><br>
<a href="/reports">View Saved Reports</a>

<script>
function send(){
    let msg = document.getElementById("input").value;
    if(!msg) return;

    document.getElementById("chat").innerHTML += "<p><b>You:</b> "+msg+"</p>";

    fetch("/",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:msg})
    })
    .then(res=>res.json())
    .then(data=>{
        document.getElementById("chat").innerHTML += "<pre><b>Bot:</b> "+data.reply+"</pre>";
    });

    document.getElementById("input").value="";
}
</script>
</body>
</html>
"""

# ================= VIEW SAVED REPORTS =================
@app.route("/reports")
def view_reports():
    cursor.execute("SELECT * FROM reports")
    rows = cursor.fetchall()

    html = """
    <h2>Saved Medical Reports</h2>
    <table border="1" cellpadding="8">
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Age</th>
        <th>Symptoms</th>
        <th>Possible Condition</th>
        <th>Precautions</th>
    </tr>
    """

    for r in rows:
        html += f"""
        <tr>
            <td>{r[0]}</td>
            <td>{r[1]}</td>
            <td>{r[2]}</td>
            <td>{r[3]}</td>
            <td>{r[4]}</td>
            <td>{r[5]}</td>
        </tr>
        """

    html += "</table><br><a href='/'>Back to Chatbot</a>"
    return html

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=False)
