from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# ----- Telegram alert setup (optional) -----
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# ----- Store last 10 readings -----
history = []

# ----- Contamination rules -----
contamination_rules = [
    {"ph_range": (6.5, 8.5), "turbidity_range": (0, 5),
     "result": "Safe", "disease": "None", "symptoms": [],
     "prevention": "Water is safe. Maintain hygiene."},
    {"ph_range": (6.5, 8.5), "turbidity_range": (5, 100),
     "result": "Unsafe", "disease": "Diarrhea",
     "symptoms": ["Loose stools", "Stomach cramps", "Nausea", "Dehydration"],
     "prevention": "Boil water or use purifier; avoid raw foods."},
    {"ph_range": (0, 6.5), "turbidity_range": (0, 5),
     "result": "Unsafe", "disease": "Cholera / Gastroenteritis",
     "symptoms": ["Severe diarrhea", "Vomiting", "Stomach cramps", "Fever"],
     "prevention": "Boil water, purify, maintain hygiene."},
    {"ph_range": (0, 6.5), "turbidity_range": (5, 100),
     "result": "Unsafe", "disease": "Cholera / Diarrhea",
     "symptoms": ["Severe diarrhea", "Vomiting", "Fever", "Dehydration"],
     "prevention": "Do not drink; boil or filter water; consult doctor if sick."},
    {"ph_range": (8.5, 14), "turbidity_range": (0, 5),
     "result": "Unsafe", "disease": "Alkaline water effect",
     "symptoms": ["Bitter taste", "Mild nausea"],
     "prevention": "Avoid excessive consumption; purify water."},
    {"ph_range": (8.5, 14), "turbidity_range": (5, 100),
     "result": "Unsafe", "disease": "Diarrhea / Stomach upset",
     "symptoms": ["Stomach cramps", "Loose stools", "Nausea"],
     "prevention": "Boil water or use purifier; avoid raw foods."}
]

# ----- Function to detect contamination -----
def detect_water_contamination(ph, turbidity):
    for rule in contamination_rules:
        ph_min, ph_max = rule["ph_range"]
        tur_min, tur_max = rule["turbidity_range"]
        if ph_min <= ph <= ph_max and tur_min <= turbidity <= tur_max:
            return rule["result"], rule["disease"], rule["symptoms"], rule["prevention"]
    # Fallback
    return "Unsafe", "Unknown", ["Check water"], "Boil or filter water"

# ----- Routes -----
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            ph = float(request.form['ph'])
            turbidity = float(request.form['turbidity'])
        except ValueError:
            return render_template('predict.html', result="Invalid input",
                                   disease="-", prevention="-",
                                   symptoms=[], ph=0, turbidity=0,
                                   history=history)

        # ----- Detect contamination -----
        result, disease, symptoms, prevention = detect_water_contamination(ph, turbidity)

        # ----- Append to history (max 10) -----
        history.append({"ph": ph, "turbidity": turbidity, "result": result})
        if len(history) > 10:
            history.pop(0)

        # ----- Send Telegram alert -----
        if result != "Safe":
            message = f"⚠️ Unsafe Water Detected!\nContamination Level: {result}\nPossible Disease: {disease}\nPrevention: {prevention}\nPH: {ph}, Turbidity: {turbidity}"
            send_telegram_alert(message)

        return render_template('predict.html', 
                               result=result,
                               disease=disease,
                               prevention=prevention,
                               symptoms=symptoms,
                               ph=ph,
                               turbidity=turbidity,
                               history=history)

    # GET request
    return render_template('predict.html', result=None, disease=None, prevention=None,
                           symptoms=[], ph=0, turbidity=0, history=history)

# ----- Run App -----
if __name__ == '__main__':
    app.run(debug=True)
