from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Telegram setup (optional)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # Replace with your bot token
CHAT_ID = "YOUR_CHAT_ID_HERE"       # Replace with your Telegram chat ID

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

# Store last 10 readings
history = []

# Disease → Symptoms mapping
disease_symptoms = {
    "Diarrhea / Cholera risk": ["Loose stools", "Stomach cramps", "Nausea", "Dehydration"],
    "None": []
}

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
            return render_template('predict.html', result="Invalid input", disease="-", prevention="-",
                                   symptoms=[], ph=0, turbidity=0, history=history)

        # Contamination logic
        if ph < 6.5 or ph > 8.5 or turbidity > 5:
            result = "Unsafe"
            disease = "Diarrhea / Cholera risk"
            prevention = "Boil water, use purifier, and avoid raw foods."
        else:
            result = "Safe"
            disease = "None"
            prevention = "Water quality is good. Maintain hygiene."

        symptoms = disease_symptoms.get(disease, [])

        # Append to history (max 10)
        history.append({"ph": ph, "turbidity": turbidity, "result": result})
        if len(history) > 10:
            history.pop(0)

        # Telegram alert
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

    return render_template('predict.html', result=None, disease=None, prevention=None,
                           symptoms=[], ph=0, turbidity=0, history=history)

if __name__ == '__main__':
    app.run(debug=True)
