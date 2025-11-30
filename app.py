from flask import Flask, request, jsonify
import os
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------
# Probar si Render acepta triple comillas
# -------------------------------------------
WIDGET_HTML = """<html><body>Widget funcionando wey!</body></html>"""

@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

@app.route("/")
def root():
    return "Backend funcionando!"

@app.route("/widget")
def widget():
    return WIDGET_HTML

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No enviaste JSON"}), 400

    prompt = data.get("prompt", "")

    try:
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        texto = respuesta.choices[0].message["content"]
        return jsonify({"respuesta": texto})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
