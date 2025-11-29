from flask import Flask, request, jsonify
import os
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/hola")
def hola():
    return jsonify({"msg": "Render funciona wey!"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensaje = data.get("prompt", "")

    try:
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": mensaje}
            ]
        )

        texto = respuesta.choices[0].message["content"]
        return jsonify({"respuesta": texto})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
