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
      height: auto;           /* 🔥 altura natural */
      min-height: 300px;      /* seguridad */
      box-sizing: border-box;
      padding: 10px;
    }

    #messages {
      flex: 1;
      overflow-y: auto;
      max-height: 60vh;       /* 🔥 límite en celular */
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
    const container = document.getElementById("chat-container");

    function resizeParent() {
      const height = document.body.scrollHeight;
      window.parent.postMessage({ widgetHeight: height }, "*");
    }

    function addMessage(text, type) {
      const div = document.createElement("div");
      div.className = type === "user" ? "msg-user" : "msg-bot";
      div.textContent = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
      resizeParent();
    }

    resizeParent();  // 🔥 primera llamada

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

      } catch {
        addMessage("Error conectando al backend.", "bot");
      }

      resizeParent();
    });

    // 🔥 Ajustar si cambia el tamaño del teclado (celular)
    window.addEventListener("resize", resizeParent);
  </script>

</body>
</html>
"""
