from flask import Flask, request, jsonify, render_template_string
import os
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------
# 🔥 PERMITIR QUE SE EMBEBA EN IFRAME (Blogger, etc.)
# ---------------------------------------------------
@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

# ---------------------------------------------------
# 🔥 HTML DEL CHAT (para /widget)
# ---------------------------------------------------
WIDGET_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>ChatGPT Blogger</title>
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f5f5f5;
    }
    #chat-container {
      height: 100vh;
      display: flex;
      flex-direction: column;
      padding: 10px;
      box-sizing: border-box;
    }
    #messages {
      flex: 1;
      overflow-y: auto;
      border: 1px solid #ddd;
      padding: 8px;
      background: #ffffff;
      border-radius: 8px;
      font-size: 14px;
    }
    .msg-user {
      text-align: right;
      margin: 6px 0;
      color: #0b7285;
      white-space: pre-wrap;
    }
    .msg-bot {
      text-align: left;
      margin: 6px 0;
      color: #343a40;
      white-space: pre-wrap;
    }
    #form {
      display: flex;
      gap: 8px;
      margin-top: 8px;
    }
    #input {
      flex: 1;
      padding: 8px;
      border-radius: 6px;
      border: 1px solid #ccc;
      font-size: 14px;
    }
    #send-btn {
      padding: 8px 14px;
      border-radius: 6px;
      border: none;
      background: #0d6efd;
      color: white;
      font-weight: 600;
      cursor: pointer;
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
    const form = document.getEle
