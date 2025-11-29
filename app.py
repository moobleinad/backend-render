from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/hola")
def hola():
    return jsonify({"msg": "Render funciona wey!"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensaje = data.get("prompt", "")
    return jsonify({"respuesta": f"Recibido: {mensaje}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
