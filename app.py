from flask import Flask, request, jsonify, render_template_string
import os
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------
# PERMITIR IFRAME
# -------------------------------------------
@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

@app.route("/")
def root():
    return "Backend funcionando wey!"

@app.route("/hola")
def hola():
    return jsonify({"msg": "Render funciona wey!"})

# -------------------------------------------
# WIDGET HTML COMPLETO (ahora sí)
# -------------------------------------------
WIDGET_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>ChatGPT Blogger</title>
  <style>
    body { margin: 0; font-family: Arial; background: #f5f5f5; }
    #chat-container { height: 100vh; display: flex; flex-direction: column; padding: 10px; }
    #messages { flex: 1; overflow-y: auto; border: 1px solid #ddd; background: white; padding: 10px; border-radius: 8px; }
    .msg-user { text-align: right; color: #0b7285; white-space: pre-wrap; margin: 6px 0; }
    .msg-bot { text-align: left; color: #333; white-space: pre-wrap; margin: 6px 0; }
    #form { display: flex; gap: 10px; margin-top: 10px; }
    #input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 8px; }
    #send-btn { padding: 8px 14px; background: #0d6efd; color: white; border-radius: 8px; border: none; cursor: pointer; }
  </style>
</head>

<body>
  <div id="chat-container">
    <div id="messages"></div>

    <form id="form">
      <input id="input" autocomplete="off" placeholder="Escribe tu mensaje..." />
      <button id="send-btn" type="submit">Enviar</button>
    </form>
  </div>

  <script>
    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const messages = document.getElementById("messages");
    const sendBtn = document.getElementById("send-btn");

    function addMessage(text, type) {
      const msg = document.createElement("div");
      msg.className = type === "user" ? "msg-user" : "msg-bot";
      msg.textContent = text;
      messages.appendChild(msg);
      messages.scrollTop = messages.scrollHeight;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      addMessage(text, "user");
      input.value = "";
      sendBtn.disabled = true;

      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: text })
        });

        const data = await res.json();
        addMessage(data.respuesta || "Error de respuesta", "bot");

      } catch (error) {
        addMessage("Error conectando al backend.", "bot");
      }

      sendBtn.disabled = false;
    });
  </script>
</body>
</html>
"""

# -------------------------------------------
# Mostrar widget
# -------------------------------------------
@app.route("/widget")
def widget():
    return render_template_string(WIDGET_HTML)

# -------------------------------------------
# CHATGPT
# -------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No enviaste JSON"}), 400

    prompt = data.get("prompt", "")

    try:
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        texto = respuesta.choices[0].message["content"]
        return jsonify({"respuesta": texto})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# -------------------------------------------
# RUN (local)
# -------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
