
import os
from flask import Flask, render_template, request, jsonify, make_response
from utils.rag import RAGBase
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
ADMIN_KEY = os.getenv("ADMIN_KEY","")

@app.route('/data/<path:filename>')
def bloquear_archivos(filename):
    return "Acceso denegado.", 403

rag = RAGBase(data_dir=DATA_DIR, cache_dir=CACHE_DIR)
rag.build()

def is_admin():
    if ADMIN_KEY and request.args.get("admin") == ADMIN_KEY:
        return True
    if ADMIN_KEY and request.cookies.get("admin") == ADMIN_KEY:
        return True
    return False

@app.route("/")
def index():
    resp = make_response(render_template("index.html", admin=is_admin()))
    if ADMIN_KEY and request.args.get("admin") == ADMIN_KEY:
        resp.set_cookie("admin", ADMIN_KEY, httponly=True, samesite="Lax")
    return resp

@app.route("/chat", methods=["POST"])
def chat():
    data=request.get_json(force=True)
    q=(data.get("pregunta") or "").strip()
    short=bool(data.get("short"))
    if not q: return jsonify({"respuesta":"Por favor, escribe tu pregunta."})
    try:
        a=rag.answer(q, short=short)
    except Exception as e:
        a=f"Ocurrió un error: {e}"
    return jsonify({"respuesta":a})

@app.route("/reindex", methods=["POST"])
def reindex():
    if not is_admin():
        return jsonify({"ok":False,"msg":"No autorizado"}), 403
    rag.build()
    return jsonify({"ok":True,"msg":"Reindexado con éxito"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
