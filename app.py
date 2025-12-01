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
# WIDGET HTML COMPLETO — CORREGIDO
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
      font-family: Arial;
      background: #f5f5f5;
      height: 100vh;
      overflow: hidden; /* evitar scr*
