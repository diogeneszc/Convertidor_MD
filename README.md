# Conversor Híbrido a Markdown (MarkItDown + Gemini)

Herramienta en Python diseñada para transformar documentos, imágenes y proyectos completos comprimidos en `.zip` a archivos **Markdown (`.md`)** limpios y estructurados, listos para usarse como contexto en asistentes de programación como **Claude Code** reduciendo al máximo el consumo de tokens.

## Características principales

* **Empaquetado inteligente de proyectos (`.zip`):**
  * Procesa el archivo comprimido directamente en memoria sin extraer carpetas temporales.
  * Filtra automáticamente directorios pesados y archivos innecesarios (`node_modules`, `.git`, `target`, `dist`, `build`, `__pycache__`, `venv`, `package-lock.json`, `.env` y archivos binarios/multimedia).
  * Genera un **árbol de directorios** al inicio del documento, incluye cada archivo con su ruta relativa y su bloque de código correspondiente, y calcula un aproximado de tokens generados.
  * No consume cuota de la API de Gemini al procesar archivos `.zip`.
* **Conversión de documentos e imágenes:**
  * Utiliza **Microsoft MarkItDown** conectado al SDK oficial de **Google Gemini (`google-genai`)** para convertir `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.html`, `.jpeg` y `.png`.
  * Extrae texto mediante OCR y describe interfaces, diagramas técnicos o capturas de pantalla directamente en **español**.

## Requisitos previos

* **Python 3.10** o superior.
* **Git** instalado.
* Una **API Key de Google AI Studio** (gratuita en [aistudio.google.com](https://aistudio.google.com/)).

## Instalación y configuración

1. **Clonar el repositorio y entrar a la carpeta:**
   ```bash
   git clone [https://github.com/tu-usuario/conversor-md.git](https://github.com/tu-usuario/conversor-md.git)
   cd conversor-md
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv env
   ```
   * **Windows (Git Bash):**
     ```bash
     source env/Scripts/activate
     ```
   * **Windows (CMD):**
     ```cmd
     env\Scripts\activate.bat
     ```
   * **Linux / macOS:**
     ```bash
     source env/bin/activate
     ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la API Key de Gemini:**
   Crea un archivo `.env` a partir de la plantilla incluida:
   ```bash
   cp .env.example .env
   ```
   Abre el archivo `.env` y reemplaza el valor con tu clave real:
   ```env
   GEMINI_API_KEY="AQ.TuClaveDeGoogleAIStudioAqui"
   ```

## Modo de uso

1. Ejecuta el programa una primera vez (o crea manualmente las carpetas) para generar los directorios de trabajo, y coloca tus archivos dentro de la carpeta **`entrada/`**:
   * **Proyectos completos:** súbelos comprimidos en formato `.zip`.
   * **Documentos o capturas:** súbelos en `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.png` o `.jpeg`.
2. Con el entorno virtual `(env)` activo en la terminal, ejecuta:
   ```bash
   python convertidor.py
   ```
3. Revisa la carpeta **`salida/`**:
   * Los proyectos `.zip` se guardarán como `nombre_proyecto.md`.
   * Los documentos e imágenes individuales se guardarán como `nombre_archivo.md`.

## Estructura del proyecto

```text
conversor_MD/
├── entrada/           # Carpeta local donde se colocan los archivos a convertir (ignorada por Git)
├── salida/            # Carpeta local donde se guardan los .md generados (ignorada por Git)
├── .env               # Variables de entorno con tu API Key local (ignorada por Git)
├── .env.example       # Plantilla de configuración de variables de entorno
├── .gitignore         # Reglas de exclusión para Git
├── convertidor.py     # Script principal de conversión híbrida
├── README.md          # Documentación e instructivo de uso
└── requirements.txt   # Lista de dependencias de Python
```