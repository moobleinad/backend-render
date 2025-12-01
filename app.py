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
import json

# -------------------------------------------
# CONFIGURACIÓN BASE
# -------------------------------------------
app = Flask(__name__)
CORS(app)

# Cliente oficial OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =======================================================
# FUNCIONES PARA LEER Y GUARDAR HISTORIAL DE THREADS
# =======================================================
DB_PATH = "threads_db.json"

def load_threads():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("threads", [])

def save_threads(threads):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"threads": threads}, f, indent=2, ensure_ascii=False)

def add_thread_to_db(thread_id, title="Nueva conversación"):
    threads = load_threads()
    threads.append({
        "thread_id": thread_id,
        "title": title,
        "favorite": False
    })
    save_threads(threads)


# -------------------------------------------
# PERMITIR IFRAME
# -------------------------------------------
@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response


# -------------------------------------------
# ENDPOINTS BÁSICOS
# -------------------------------------------
@app.route("/")
def root():
    return "Backend funcionando wey!"

@app.route("/hola")
def hola():
    return jsonify({"msg": "Render funciona wey!"})


# =======================================================
#  WIDGET HTML
# =======================================================
WIDGET_HTML = """REEMPLAZO COMPLETO TAL CUAL PUSISTE ARRIBA..."""


# =======================================================
#  ENDPOINT: RENDERIZAR WIDGET HTML
# =======================================================
@app.route("/widget")
def widget():
    return render_template_string(WIDGET_HTML)


# =======================================================
#  ENDPOINT: CREAR THREAD (SOLO ESTA VERSIÓN)
#     + Guarda thread_id en threads_db.json
# =======================================================
@app.route("/thread", methods=["POST"])
def create_thread():
    try:
        thread = client.beta.threads.create()
        add_thread_to_db(thread.id)
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
#  EJECUCIÓN LOCAL
# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
