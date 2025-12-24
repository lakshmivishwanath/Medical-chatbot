from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# ===== DATABASE SETUP =====
conn = sqlite3.connect("friend_database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    blood_group TEXT,
    weight REAL,
    symptoms TEXT
)
""")
conn.commit()

# ===== HOME PAGE / CHATBOT =====
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Medical Intake Chatbot</title>
<style>
body {
    font-family: 'Arial', sans-serif;
    background: linear-gradient(120deg, #ff9a9e, #fad0c4);
    margin:0;
    padding:0;
}
.chatbox {
    width:450px;
    margin:50px auto;
    background:#ffffff;
    padding:25px;
    border-radius:20px;
    box-shadow:0 10px 30px rgba(0,0,0,0.2);
    animation: fadeIn 1s ease-in;
}
h2 {
    text-align:center;
    color:#ff6f61;
    font-weight:bold;
}
#chat {
    height:280px;
    overflow-y:auto;
    border:2px solid #ff6f61;
    padding:10px;
    border-radius:10px;
    background:#fff7f3;
    margin-bottom:10px;
}
.user {
    color:#3d84a8;
    font-weight:bold;
}
.bot {
    color:#ffb347;
    font-weight:bold;
}
input {
    width:75%;
    padding:12px;
    border-radius:10px;
    border:2px solid #ff6f61;
    background:#fff7f3;
    color:#333;
    font-weight:bold;
}
input::placeholder {
    color:#999;
}
button {
    padding:12px 18px;
    border:none;
    background:#ff6f61;
    color:white;
    border-radius:10px;
    cursor:pointer;
    font-weight:bold;
    transition:0.3s;
}
button:hover {
    background:#ff3d2e;
}
.view {
    margin-top:15px;
    text-align:center;
}
a {
    text-decoration:none;
    color:#3d84a8;
    font-weight:bold;
}
a:hover {
    color:#1c3f5a;
}
@keyframes fadeIn {
    0% {opacity:0; transform: translateY(-20px);}
    100% {opacity:1; transform: translateY(0);}
}
</style>
</head>
<body>
<div class="chatbox">
<h2>Medical Intake Chatbot</h2>
<div id="chat"></div>
<input id="input" placeholder="Type here...">
<button onclick="send()">Send</button>
<div class="view">
    <a href="/patients"> View Saved Data</a>
</div>
</div>

<script>
let step = 0;
let data = {};
const questions = [
    "Hello! What is your name?",
    "How old are you?",
    "What is your Bloodgroup?",
    "What is your Weight (kg)?",
    "Please describe your symptoms"
];

document.getElementById("chat").innerHTML += "<p class='bot'>Bot: "+questions[0]+"</p>";

function send(){
    let input = document.getElementById("input").value;
    if(!input) return;

    document.getElementById("chat").innerHTML += "<p class='user'>You: "+input+"</p>";

    if(step===0) data.name=input;
    if(step===1){
        if(isNaN(input)){
            document.getElementById("chat").innerHTML += "<p class='bot'>Bot: Age must be numeric</p>";
            return;
        }
        data.age=input;
    }
    if(step===2) data.blood_group=input;
    if(step===3){
        if(isNaN(input)){
            document.getElementById("chat").innerHTML += "<p class='bot'>Bot: Weight must be numeric</p>";
            return;
        }
        data.weight=input;
    }
    if(step===4){
        data.symptoms=input;
        fetch("/save",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify(data)
        })
        .then(r=>r.json())
        .then(res=>{
            document.getElementById("chat").innerHTML += "<p class='bot'>Bot: "+res.message+"</p>";
        });
        return;
    }

    step++;
    document.getElementById("chat").innerHTML += "<p class='bot'>Bot: "+questions[step]+"</p>";
    document.getElementById("input").value="";
}
</script>
</body>
</html>
"""

# ===== SAVE PATIENT DATA =====
@app.route("/save", methods=["POST"])
def save():
    d = request.json
    cursor.execute(
        "INSERT INTO patients (name, age, blood_group, weight, symptoms) VALUES (?,?,?,?,?)",
        (d["name"], d["age"], d["blood_group"], d["weight"], d["symptoms"])
    )
    conn.commit()
    return jsonify({"message":"Your medical details have been saved successfully! Thank you!"})

# ===== VIEW PATIENT DATA =====
@app.route("/patients")
def patients():
    cursor.execute("SELECT * FROM patients")
    rows = cursor.fetchall()

    html = """
    <html>
    <head>
    <title>Saved Patients</title>
    <style>
    body{font-family:Arial, sans-serif; background: linear-gradient(120deg, #ff9a9e, #fecfef); color:#333;}
    table{border-collapse:collapse;width:90%;margin:30px auto;background:#fff9f5; border-radius:10px; overflow:hidden; box-shadow:0 5px 20px rgba(0,0,0,0.15);}
    th,td{padding:12px;border:1px solid #ff6f61;text-align:center;}
    th{background:#ff6f61;color:white;}
    h2{text-align:center; color:#ff3d2e; font-weight:bold;}
    a{display:block; text-align:center; margin-top:20px; text-decoration:none; color:#3d84a8; font-weight:bold;}
    a:hover{color:#1c3f5a;}
    </style>
    </head>
    <body>
    <h2>📋 Stored Patient Records</h2>
    <table>
    <tr>
    <th>ID</th><th>Name</th><th>Age</th><th>Blood Group</th>
    <th>Weight</th><th>Symptoms</th>
    </tr>
    """

    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>"

    html += """
    </table>
    <a href="/">← Back to Chatbot</a>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)
