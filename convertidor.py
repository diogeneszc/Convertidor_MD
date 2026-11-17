import os
import base64
import zipfile
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from markitdown import MarkItDown

# 1. Cargar la API Key desde .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró GEMINI_API_KEY en el archivo .env")

# 2. Adaptador de Gemini para documentos e imágenes individuales
class AdaptadorGemini:
    def __init__(self, key):
        self.client = genai.Client(
            api_key=key,
            http_options={'api_version': 'v1beta'}
        )
        self.chat = self
        self.completions = self

    def create(self, model, messages, **kwargs):
        contenidos = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                contenidos.append(content)
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        contenidos.append(item["text"])
                    elif item.get("type") == "image_url":
                        url = item["image_url"]["url"]
                        header, b64_data = url.split(",", 1)
                        mime_type = header.split(";")[0].replace("data:", "")
                        contenidos.append(
                            types.Part.from_bytes(
                                data=base64.b64decode(b64_data),
                                mime_type=mime_type
                            )
                        )

        respuesta = self.client.models.generate_content(
            model=model,
            contents=contenidos
        )

        class Mensaje:
            content = respuesta.text
        class Opcion:
            message = Mensaje()
        class Respuesta:
            choices = [Opcion()]
        return Respuesta()
# NOTA: Se puede cambiar el modelo de Gemini según la necesidad:
# gemini-2.5-flash los analice con mayor precisión antes de pasárselos a Claude Code
# gemini-flash-lite-latest utiliza menos tokens y es más rápido, pero puede perder detalles en imágenes complejas
md = MarkItDown(
    llm_client=AdaptadorGemini(api_key),
    llm_model="gemini-flash-lite-latest"
)

# 3. Filtros para limpiar proyectos .zip y ahorrar tokens
CARPETAS_IGNORADAS = {
    "node_modules", ".git", ".svn", ".hg", "target", "build", "dist", "out",
    ".next", ".nuxt", "__pycache__", ".pytest_cache", "venv", "env", ".venv",
    ".idea", ".vscode", "coverage", ".gradle", ".mvn", "bin", "obj"
}

ARCHIVOS_IGNORADOS = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock",
    "Cargo.lock", ".DS_Store", "Thumbs.db", ".env", ".env.local",
    ".env.development", ".env.production"
}

EXTENSIONES_IGNORADAS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
    ".mp4", ".mp3", ".wav", ".avi", ".mov", ".pdf", ".zip", ".rar", ".7z",
    ".tar", ".gz", ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".war",
    ".pyc", ".pyo", ".o", ".a", ".woff", ".woff2", ".ttf", ".eot", ".db", ".sqlite"
}

MAPA_LENGUAJES = {
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "jsx", ".ts": "typescript", ".tsx": "tsx",
    ".java": "java", ".py": "python", ".c": "c", ".h": "c",
    ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp", ".cs": "csharp",
    ".go": "go", ".rs": "rust", ".php": "php", ".rb": "ruby",
    ".html": "html", ".htm": "html", ".css": "css", ".scss": "scss",
    ".sql": "sql", ".json": "json", ".xml": "xml",
    ".yml": "yaml", ".yaml": "yaml", ".properties": "properties",
    ".sh": "bash", ".bash": "bash", ".bat": "batch", ".ps1": "powershell",
    ".md": "markdown", ".toml": "toml", ".ini": "ini", ".gradle": "groovy"
}

def generar_arbol_directorio(rutas):
    arbol = {}
    for ruta in rutas:
        partes = ruta.split("/")
        actual = arbol
        for parte in partes:
            actual = actual.setdefault(parte, {})

    lineas = []
    def recorrer(nodo, prefijo=""):
        items = list(nodo.items())
        for i, (nombre, hijos) in enumerate(items):
            es_ultimo = (i == len(items) - 1)
            conector = "└── " if es_ultimo else "├── "
            lineas.append(f"{prefijo}{conector}{nombre}")
            if hijos:
                extension = "    " if es_ultimo else "│   "
                recorrer(hijos, prefijo + extension)

    recorrer(arbol)
    return "\n".join(lineas)

def procesar_zip_proyecto(ruta_zip: Path, carpeta_salida: Path):
    archivos_validos = []
    omitidos = 0

    with zipfile.ZipFile(ruta_zip, "r") as zf:
        for info in sorted(zf.infolist(), key=lambda x: x.filename):
            if info.is_dir():
                continue

            ruta_relativa = info.filename.replace("\\", "/")
            partes = ruta_relativa.split("/")
            nombre_archivo = partes[-1]
            extension = Path(nombre_archivo).suffix.lower()

            # Filtrar carpetas basura, archivos lock/.env y binarios
            if any(p in CARPETAS_IGNORADAS for p in partes[:-1]):
                omitidos += 1
                continue
            if nombre_archivo in ARCHIVOS_IGNORADOS or extension in EXTENSIONES_IGNORADAS:
                omitidos += 1
                continue

            raw_bytes = zf.read(info.filename)
            # Detectar si es un archivo binario no listado
            if b"\x00" in raw_bytes[:1024]:
                omitidos += 1
                continue

            try:
                contenido = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                contenido = raw_bytes.decode("latin-1", errors="replace")

            archivos_validos.append((ruta_relativa, extension, nombre_archivo, contenido.rstrip()))

    if not archivos_validos:
        print(f"  [AVISO] No se encontraron archivos de código válidos dentro de {ruta_zip.name}")
        return

    # Construir el documento Markdown optimizado para IA
    secciones = [
        f"# Contexto del Proyecto: {ruta_zip.stem}\n",
        "## Estructura de Archivos\n",
        "```text",
        generar_arbol_directorio([r[0] for r in archivos_validos]),
        "```\n",
        "## Archivos del Proyecto\n"
    ]

    for ruta_relativa, extension, nombre_archivo, contenido in archivos_validos:
        lenguaje = "dockerfile" if nombre_archivo == "Dockerfile" else MAPA_LENGUAJES.get(extension, "")
        secciones.append(f"### `{ruta_relativa}`")
        # Se usan 4 comillas invertidas para evitar conflictos con bloques ``` internos en README.md
        secciones.append(f"````{lenguaje}")
        secciones.append(contenido)
        secciones.append("````\n")

    resultado_final = "\n".join(secciones)
    ruta_destino = carpeta_salida / f"{ruta_zip.stem}_proyecto.md"

    with open(ruta_destino, "w", encoding="utf-8") as f:
        f.write(resultado_final)

    tokens_estimados = len(resultado_final) // 4
    print(f"  [OK] Proyecto empaquetado en: {ruta_destino}")
    print(f"       -> Archivos incluidos: {len(archivos_validos)} | Omitidos: {omitidos} | Tokens aprox.: ~{tokens_estimados:,}")

# 4. Ejecución principal
carpeta_entrada = Path("entrada")
carpeta_salida = Path("salida")
carpeta_entrada.mkdir(exist_ok=True)
carpeta_salida.mkdir(exist_ok=True)

def convertir_todos_los_archivos():
    archivos = [f for f in carpeta_entrada.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not archivos:
        print("La carpeta 'entrada' está vacía.")
        return

    print(f"Se encontraron {len(archivos)} archivo(s). Iniciando conversión...\n")

    for archivo in archivos:
        print(f"Procesando: {archivo.name} ...")
        try:
            if archivo.suffix.lower() == ".zip":
                procesar_zip_proyecto(archivo, carpeta_salida)
            else:
                resultado = md.convert(
                    str(archivo),
                    llm_prompt=(
                        "Analiza esta imagen y responde estrictamente en español. "
                        "Transcribe todo el texto visible con exactitud. Si es un diseño UI, "
                        "captura de pantalla o diagrama técnico, describe su estructura, "
                        "componentes y lógica de forma clara en formato Markdown."
                    )
                )
                ruta_destino = carpeta_salida / f"{archivo.stem}.md"
                with open(ruta_destino, "w", encoding="utf-8") as f:
                    f.write(resultado.text_content)
                print(f"  [OK] Guardado en: {ruta_destino}")
        except Exception as e:
            print(f"  [ERROR] No se pudo convertir {archivo.name}: {e}")

    print("\n¡Proceso finalizado!")

if __name__ == "__main__":
    convertir_todos_los_archivos()