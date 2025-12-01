# =======================================================
#  CHATGPT RENDER + BLOGGER WIDGET
#  Backend Flask con Threads, Historial e Imagenes
#  Autor: Daniel + ChatGPT (2025)
# =======================================================

from flask import Flask, request, jsonify, render_template_string
import os
from openai import OpenAI
from flask_cors import CORS
import time

# -------------------------------------------
# CONFIGURACIÓN BASE
# -------------------------------------------
app = Flask(__name__)
CORS(app)

# Cliente oficial OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------
# PERMITIR IFRAME (para que Blogger pueda mostrar el widget)
# -------------------------------------------
@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response


# -------------------------------------------
# ENDPOINTS BÁSICOS DE TEST
# -------------------------------------------
@app.route("/")
def root():
    return "Backend funcionando wey!"


@app.route("/hola")
def hola():
    return jsonify({"msg": "Render funciona wey!"})


# =======================================================
#  WIDGET HTML (Frontend que se incrusta en Blogger)
#  Incluye: sidebar izquierda (favoritos + historial) y chat a la derecha
# =======================================================
WIDGET_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>ChatGPT Blogger</title>

  <style>
    /* ------------------------------
       ESTILOS GENERALES
    ------------------------------ */

    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      background: #f5f5f5;
    }

    /* Layout principal: sidebar + chat */
    #layout {
      display: flex;
      flex-direction: row;
      gap: 10px;
      padding: 10px;
      box-sizing: border-box;
    }

    /* ------------------------------
       SIDEBAR IZQUIERDA
    ------------------------------ */

    #sidebar {
      width: 28%;
      min-width: 180px;
      max-width: 260px;
      background: #ffffff;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 10px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      max-height: 85vh;
      overflow-y: auto;
    }

    .sidebar-title {
      font-size: 14px;
      font-weight: bold;
      margin-bottom: 6px;
    }

    .sidebar-box {
      border-radius: 6px;
      padding: 6px;
      margin-bottom: 12px;
      font-size: 13px;
      background: #fafafa;
      border: 1px solid #e5e5e5;
    }

    #favorites-list .favorite-item,
    #history-list .history-item {
      padding: 6px;
      border-radius: 4px;
      margin-bottom: 4px;
      cursor: pointer;
    }

    #favorites-list .favorite-item {
      background: #fff3cd;
      border: 1px solid #ffeeba;
    }

    #favorites-list .favorite-item:hover {
      background: #ffe8a1;
    }

    #history-list .history-item {
      background: #f8f9fa;
      border: 1px solid #e2e3e5;
    }

    #history-list .history-item:hover {
      background: #e2e6ea;
    }

    /* ------------------------------
       CONTENEDOR DE CHAT (DERECHA)
    ------------------------------ */

    #chat-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: auto;
      min-height: 300px;
      box-sizing: border-box;
    }

    #messages {
      flex: 1;
      overflow-y: auto;
      max-height: 60vh;
      background: white;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 10px;
      margin-bottom: 10px;
    }

    .msg-user {
      text-align: right;
      margin: 5px 0;
      color: #0b7285;
      white-space: pre-wrap;
    }

    .msg-bot {
      text-align: left;
      margin: 5px 0;
      color: #333;
      white-space: pre-wrap;
    }

    /* Imagen generada */
    .img-message {
      max-width: 100%;
      border-radius: 10px;
      margin: 8px 0;
    }

    #form {
      display: flex;
      gap: 10px;
      height: 45px;
      flex-shrink: 0;
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

    /* ------------------------------
       RESPONSIVE (CELULAR)
    ------------------------------ */
    @media (max-width: 720px) {
      #layout {
        flex-direction: column;
      }
      #sidebar {
        width: 100%;
        max-width: 100%;
      }
      #chat-container {
        width: 100%;
      }
    }
  </style>
</head>

<body>

  <div id="layout">

    <!-- ===================== -->
    <!--  SIDEBAR IZQUIERDA   -->
    <!-- ===================== -->
    <div id="sidebar">
      <div class="sidebar-section">
        <div class="sidebar-title">⭐ Favoritos</div>
        <div id="favorites-list" class="sidebar-box">
          <em>Vacío por ahora</em>
        </div>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-title">🕒 Historial</div>
        <div id="history-list" class="sidebar-box">
          <em>Sin mensajes aún</em>
        </div>
      </div>
    </div>

    <!-- ===================== -->
    <!--  CONTENEDOR DEL CHAT -->
    <!-- ===================== -->
    <div id="chat-container">

      <!-- Área donde se pintan los mensajes -->
      <div id="messages"></div>

      <!-- Formulario de envío -->
      <form id="form">
        <input id="input" autocomplete="off" placeholder="Escribe tu mensaje..." />
        <button id="send-btn" type="submit">Enviar</button>
      </form>

    </div>

  </div>

  <!-- ---------------------------------------------------
       LÓGICA DEL CHAT (Frontend)
  ----------------------------------------------------- -->
  <script>
    let THREAD_ID = null;

    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const sendBtn = document.getElementById("send-btn");
    const messages = document.getElementById("messages");

    const historyListDiv = document.getElementById("history-list");
    const favoritesListDiv = document.getElementById("favorites-list");

    // Arrays para historial y favoritos (en memoria)
    let sidebarHistory = [];
    let favorites = [];

    // Estado inicial
    sendBtn.disabled = true;
    input.disabled = true;
    messages.innerHTML = "<em>Iniciando chat…</em>";

    // --------------------------------------------
    // CREAR THREAD (conversación con OpenAI)
    // --------------------------------------------
    async function initThread() {
      try {
        const res = await fetch("/thread", { method: "POST" });
        const data = await res.json();
        THREAD_ID = data.thread_id;

        sendBtn.disabled = false;
        input.disabled = false;
        messages.innerHTML = "";
        renderSidebar();
      } catch (e) {
        messages.innerHTML = "<b>No se pudo iniciar el chat.</b>";
      }
    }

    initThread();

    // --------------------------------------------
    // Ajuste automático del iframe en Blogger
    // --------------------------------------------
    function resizeParent() {
      const height = document.body.scrollHeight;
      window.parent.postMessage({ widgetHeight: height }, "*");
    }

    // --------------------------------------------
    // Pinta un mensaje en la ventana del chat
    // --------------------------------------------
    function addMessage(content, type) {
      const div = document.createElement("div");
      div.className = type === "user" ? "msg-user" : "msg-bot";
      div.textContent = content;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
      resizeParent();
    }

    // --------------------------------------------
    // Renderizar sidebar (historial + favoritos)
    // --------------------------------------------
    function renderSidebar() {
      // Favoritos
      favoritesListDiv.innerHTML = "";
      if (favorites.length === 0) {
        favoritesListDiv.innerHTML = "<em>Vacío por ahora</em>";
      } else {
        favorites.forEach((text, idx) => {
          const item = document.createElement("div");
          item.className = "favorite-item";
          item.textContent = text;
          favoritesListDiv.appendChild(item);
        });
      }

      // Historial
      historyListDiv.innerHTML = "";
      if (sidebarHistory.length === 0) {
        historyListDiv.innerHTML = "<em>Sin mensajes aún</em>";
      } else {
        sidebarHistory.forEach((text, idx) => {
          const item = document.createElement("div");
          item.className = "history-item";
          item.textContent = text;

          // Al hacer clic en un elemento del historial -> agregarlo a favoritos
          item.onclick = () => {
            if (!favorites.includes(text)) {
              favorites.push(text);
              renderSidebar();
            }
          };

          historyListDiv.appendChild(item);
        });
      }

      resizeParent();
    }

    resizeParent();

    // --------------------------------------------
    // MANEJAR ENVÍO DEL CHAT
    // --------------------------------------------
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!THREAD_ID) return;

      const text = input.value.trim();
      if (!text) return;

      // Pintamos mensaje del usuario
      addMessage(text, "user");
      input.value = "";

      // Añadimos al historial (sidebar)
      const resumen = text.length > 60 ? text.slice(0, 57) + "..." : text;
      sidebarHistory.push(resumen);
      renderSidebar();

      // --------------------------------------------
      // DETECTAR SI EL USUARIO QUIERE IMAGEN
      // --------------------------------------------
      const wantsImage =
        text.toLowerCase().includes("imagen") ||
        text.toLowerCase().includes("crea") ||
        text.toLowerCase().includes("dibuja") ||
        text.toLowerCase().includes("genera") ||
        text.toLowerCase().includes("haz una imagen");

      if (wantsImage) {
        addMessage("Generando imagen…", "bot");

        try {
          const imgRes = await fetch("/image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: text, thread_id: THREAD_ID })
          });

          const imgData = await imgRes.json();

          if (imgData.image_url) {
            const imgDiv = document.createElement("div");
            imgDiv.className = "msg-bot";
            const img = document.createElement("img");
            img.src = imgData.image_url;
            img.className = "img-message";
            imgDiv.appendChild(img);
            messages.appendChild(imgDiv);
            messages.scrollTop = messages.scrollHeight;
          } else {
            addMessage("No pude generar la imagen.", "bot");
          }

        } catch {
          addMessage("Error generando la imagen.", "bot");
        }

        resizeParent();
        return;
      }

      // --------------------------------------------
      // CHAT NORMAL (texto)
      // --------------------------------------------
      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: text, thread_id: THREAD_ID })
        });

        const data = await res.json();

        messages.innerHTML = "";
        sidebarHistory = [];

        // Renderizar todo el historial que devuelve el backend
        (data.history || []).forEach(msg => {
          addMessage(msg.text, msg.role === "user" ? "user" : "bot");
          if (msg.role === "user") {
            const resumenMsg = msg.text.length > 60 ? msg.text.slice(0, 57) + "..." : msg.text;
            sidebarHistory.push(resumenMsg);
          }
        });

        renderSidebar();

      } catch {
        addMessage("Error conectando al backend.", "bot");
      }

      resizeParent();
    });

    window.addEventListener("resize", resizeParent);
  </script>

</body>
</html>
"""

# =======================================================
#  ENDPOINT: RENDERIZAR WIDGET HTML
# =======================================================
@app.route("/widget")
def widget():
    return render_template_string(WIDGET_HTML)


# =======================================================
#  ENDPOINT: CREAR THREAD (inicia conversación)
# =======================================================
@app.route("/thread", methods=["POST"])
def create_thread():
    try:
        thread = client.beta.threads.create()
        return jsonify({"thread_id": thread.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =======================================================
#  ENDPOINT: CHAT CON HISTORIAL (Threads API)
# =======================================================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")
    thread_id = data.get("thread_id")

    if not thread_id:
        return jsonify({"error": "Falta thread_id"}), 400

    try:
        # Añadir mensaje del usuario al thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )

        # Ejecutar el modelo
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            model="gpt-4o-mini"
        )

        # Esperar respuesta
        while True:
            check = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if check.status == "completed":
                break
            time.sleep(0.2)

        # Obtener historial completo
        messages_list = client.beta.threads.messages.list(thread_id=thread_id)

        history = []
        for m in messages_list.data[::-1]:
            if m.role in ["user", "assistant"]:
                content = m.content[0].text.value if hasattr(m.content[0], "text") else ""
                history.append({"role": m.role, "text": content})

        return jsonify({"history": history})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =======================================================
#  ENDPOINT: GENERACIÓN DE IMÁGENES
# =======================================================
@app.route("/image", methods=["POST"])
def image():
    data = request.get_json()
    prompt = data.get("prompt", "")
    thread_id = data.get("thread_id")

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
        url = result.data[0].url

        # Guardar referencia de imagen en el historial
        if thread_id:
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="assistant",
                content=f"[Imagen generada]({url})"
            )

        return jsonify({"image_url": url})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =======================================================
#  EJECUCIÓN LOCAL (solo debug)
# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
