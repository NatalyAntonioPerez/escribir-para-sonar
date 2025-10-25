# Asistente académico — Escribir para soñar (WEB, institucional)

## Despliegue (Render / Railway)
1) Sube esta carpeta a un repo (GitHub) o conéctala directamente.
2) Variables de entorno:
   - OPENAI_API_KEY = sk-proj-...
   - ADMIN_KEY      = (tu clave secreta)
3) Build: `pip install -r requirements.txt`
4) Start: `gunicorn app:app`
5) Modo admin: abre la URL con `?admin=TU_CLAVE` (se guarda en cookie).

/data contiene tus documentos (por ejemplo, tesis.txt). `Reindexar` solo aparece en modo admin.
