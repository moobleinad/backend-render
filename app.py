# =======================================================
#  CHATGPT PARA BLOGGER — BACKEND RENDER
#  Versión simple (sin historial, sin favoritos)
#  Con comentarios y títulos claros
# =======================================================

from flask import Flask, request, jsonify, render_template_string
import os
from openai import OpenAI
from flask_cors import CORS

# =======================================================
# 1. CONFIGURACIÓN BASE DE FLASK
# =======================================================
app = Flask(__name__)
CORS(app)  # permite que Blogger llame al backend

# Cliente OpenAI usando variable de entorno OPENAI_API_KEY
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =======================================================
# 2. PERMITIR QUE EL SITIO SE CARGUE EN IFRAMES
#    (Necesario para Blogger o no se verá nada)
# =======================================================
@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response


# =======================================================
# 3. ENDPOINTS DE PRUEBA
# =======================================================
@app.route("/")
def root():
    return "Backend funcionando wey!"

@app.route("/hola")
def hola():
    return jsonify({"msg": "Render funciona wey!"})


# =======================================================
# 4. WIDGET HTML (EL FRONTEND DEL CHAT)
#    Versión simple — un solo panel de chat
# =======================================================
WIDGET_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>ChatGPT Blogger</title>

  <style>
    /* ============================
       ESTILOS GENERALES
       ============================ */
    body {
      margin: 0;
      padding: 0;
      font-family: Arial;
      background: #f5f5f5;
      height: 100%;
      overflow: hidden;  /* mantiene siempre los 500px del iframe */
    }

    /* ============================
       CONTENEDOR PRINCIPAL DEL CHAT
       ============================ */
    #chat-container {
      height: 500px;         /* altura exacta para que encaje en el iframe */
      display: flex;
      flex-direction: column;
      padding: 10px;
      box-sizing: border-box;
    }

    /* ============================
       ZONA DE MENSAJES
       ============================ */
    #messages {
      flex: 1;
      overflow-y: auto;
      background: white;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 10px;
    }

    .msg-user {
      text-align: right;
      color: #0b7285;
      margin: 8px 0;
      white-space: pre-wrap;
    }

    .msg-bot {
      text-align: left;
      color: #333;
      margin: 8px 0;
      white-space: pre-wrap;
    }

    /* ============================
       INPUT DEL CHAT + BOTÓN
       ============================ */
    #form {
      display: flex;
      gap: 10px;
      margin-top: 10px;
      height: 45px;
      flex-shrink: 0; /* evita que se achique */
    }

    #input {
      flex: 1;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid #ccc;
    }

    #send-btn {
      padding: 10px 16px;
      background: #0d6efd;
      border: none;
      border-radius: 8px;
      color: white;
      cursor: pointer;
      font-weight: bold;
    }
  </style>

</head>

<body>
  <!-- ============================
       ESTRUCTURA DEL CHAT
       ============================ -->
  <div id="chat-container">

    <!-- Caja donde se pintan los mensajes -->
    <div id="messages"></div>

    <!-- Formulario para enviar mensajes -->
    <form id="form">
      <input id="input" autocomplete="off" placeholder="Escribe tu mensaje..." />
      <button id="send-btn" type="submit">Enviar</button>
    </form>

  </div>

  <!-- ============================
       LÓGICA DEL CHAT (JAVASCRIPT)
       ============================ -->
  <script>
    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const messages = document.getElementById("messages");

    /* ------------------------------------------
       FUNCIÓN PARA AGREGAR UN MENSAJE AL CHAT
       ------------------------------------------ */
    function addMessage(text, type) {
      const div = document.createElement("div");
      div.className = type === "user" ? "msg-user" : "msg-bot";
      div.textContent = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;  // baja al final
    }

    /* ------------------------------------------
       MANEJAR ENVÍO DEL MENSAJE
       ------------------------------------------ */
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const text = input.value.trim();
      if (!text) return;

      addMessage(text, "user");
      input.value = "";

      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: text })
        });

        const data = await res.json();
        addMessage(data.respuesta || "Error de respuesta", "bot");

      } catch (err) {
        addMessage("Error conectando al backend.", "bot");
      }
    });
  </script>

</body>
</html>
"""


# =======================================================
# 5. ENDPOINT PARA MOSTRAR EL WIDGET
# =======================================================
@app.route("/widget")
def widget():
    return render_template_string(WIDGET_HTML)


# =======================================================
# 6. ENDPOINT DEL CHAT (LÓGICA GPT)
# =======================================================
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


# =======================================================
# 7. RUN SERVER (SOLO LOCAL)
# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
