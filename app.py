from flask import Flask, request, jsonify, render_template_string
import os
from openai import OpenAI
from flask_cors import CORS
import time

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
# WIDGET HTML
# -------------------------------------------

WIDGET_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>ChatGPT Blogger</title>

  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: Arial;
      background: #f5f5f5;
    }

    #chat-container {
      display: flex;
      flex-direction: column;
      height: auto;
      min-height: 300px;
      box-sizing: border-box;
      padding: 10px;
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

    .img-message {
      max-width: 100%;
      border-radius: 10px;
      margin: 8px 0;
    }
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
    let THREAD_ID = null;

    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const sendBtn = document.getElementById("send-btn");
    const messages = document.getElementById("messages");

    sendBtn.disabled = true;
    input.disabled = true;
    messages.innerHTML = "<em>Iniciando chat…</em>";

    async function initThread() {
      try {
        const res = await fetch("/thread", { method: "POST" });
        const data = await res.json();
        THREAD_ID = data.thread_id;

        sendBtn.disabled = false;
        input.disabled = false;
        messages.innerHTML = "";
      } catch (e) {
        messages.innerHTML = "<b>No se pudo iniciar el chat.</b>";
      }
    }

    initThread();

    function resizeParent() {
      const height = document.body.scrollHeight;
      window.parent.postMessage({ widgetHeight: height }, "*");
    }

    function addMessage(content, type) {
      const div = document.createElement("div");
      div.className = type === "user" ? "msg-user" : "msg-bot";

      if (type === "image") {
        const img = document.createElement("img");
        img.src = content;
        img.className = "img-message";
        div.appendChild(img);
      } else {
        div.textContent = content;
      }

      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
      resizeParent();
    }

    resizeParent();

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!THREAD_ID) return;

      const text = input.value.trim();
      if (!text) return;

      addMessage(text, "user");
      input.value = "";

      // Detectar imagen
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
            addMessage(imgData.image_url, "image");
          } else {
            addMessage("No pude generar la imagen.", "bot");
          }

        } catch {
          addMessage("Error generando la imagen.", "bot");
        }

        resizeParent();
        return;
      }

      // Chat normal
      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: text, thread_id: THREAD_ID })
        });

        const data = await res.json();

        messages.innerHTML = "";
        data.history.forEach(msg => {
          addMessage(msg.text, msg.role === "user" ? "user" : "bot");
        });

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

# -------------------------------------------
# RENDER DEL WIDGET
# -------------------------------------------
@app.route("/widget")
def widget():
    return render_template_string(WIDGET_HTML)


# -------------------------------------------
# CREAR THREAD
# -------------------------------------------
@app.route("/thread", methods=["POST"])
def create_thread():
    try:
        thread = client.beta.threads.create()
        return jsonify({"thread_id": thread.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -------------------------------------------
# CHAT CON HISTORIAL
# -------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")
    thread_id = data.get("thread_id")

    if not thread_id:
        return jsonify({"error": "Falta thread_id"}), 400

    try:
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            model="gpt-4o-mini"
        )

        while True:
            check = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if check.status == "completed":
                break
            time.sleep(0.2)

        messages_list = client.beta.threads.messages.list(thread_id=thread_id)

        history = []
        for m in messages_list.data[::-1]:
            if m.role in ["user", "assistant"]:
                content = m.content[0].text.value if hasattr(m.content[0], "text") else ""
                history.append({"role": m.role, "text": content})

        return jsonify({"history": history})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -------------------------------------------
# IMAGEN
# -------------------------------------------
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

        if thread_id:
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="assistant",
                content=f"[Imagen generada]({url})"
            )

        return jsonify({"image_url": url})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -------------------------------------------
# RUN LOCAL
# -------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
