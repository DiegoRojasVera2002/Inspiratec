from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import base64
import os
import uuid
import time

# Cargar variables de entorno
load_dotenv()

# Crear los directorios necesarios si no existen
os.makedirs("static", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app = FastAPI(title="¡Ven para aprender con Letro! 📸")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/audio", StaticFiles(directory="audio"), name="audio")
templates = Jinja2Templates(directory="templates")

# Inicializar OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze-image/")
async def analyze_image(file: UploadFile = File(...)):
    try:
        # Leer el archivo
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")
        
        # Obtener descripción de la imagen usando GPT-4 Vision
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Eres Letro, un amigable asistente infantil peruano muy entusiasta. 
                            Al identificar el objeto en la imagen, responde en este formato exacto:

                            objeto_detectado: **[nombre del objeto]**
                            descripcion: **[breve descripción de uso simple]**

                            Por ejemplo:
                            objeto_detectado: **cartera**
                            descripcion: **guardar dinero y tarjetas**

                            Usa palabras comunes en Perú y mantén todo simple."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=150
        )
        
        description = response.choices[0].message.content.strip()
        print("Descripción generada:", description)
        
        # Extraer objeto y descripción
        import re
        objeto = re.search(r'objeto_detectado: \*\*(.*?)\*\*', description)
        descripcion = re.search(r'descripcion: \*\*(.*?)\*\*', description)
        
        objeto = objeto.group(1) if objeto else "objeto"
        descripcion = descripcion.group(1) if descripcion else "describir el objeto"
        
        # Texto para el audio
        audio_text = f"¡Encontraste un {objeto}! {descripcion}"
        
        # Generar audio
        try:
            audio_filename = f"audio_{uuid.uuid4()}.mp3"
            audio_path = os.path.join("audio", audio_filename)
            
            audio_response = client.audio.speech.create(
                model="tts-1",
                voice="fable",
                input=audio_text
            )
            
            # Guardar el audio directamente usando stream_to_file
            audio_response.stream_to_file(audio_path)
            
            print(f"Audio generado en: {audio_path}")
            
            return {
                "objeto": f"**{objeto}**",
                "descripcion": f"**{descripcion}**",
                "audio_url": f"/audio/{audio_filename}"
            }
            
        except Exception as audio_error:
            print(f"Error generando audio: {str(audio_error)}")
            raise
            
    except Exception as e:
        print(f"Error procesando imagen: {str(e)}")
        return {
            "error": True,
            "description": "¡Ups! Algo salió mal. ¡Intenta de nuevo!"
        }

# Limpiar archivos de audio antiguos periódicamente
@app.on_event("startup")
async def cleanup_old_files():
    try:
        audio_dir = "audio"
        current_time = time.time()
        for filename in os.listdir(audio_dir):
            if filename.startswith("audio_"):
                file_path = os.path.join(audio_dir, filename)
                if os.path.getctime(file_path) < current_time - 3600:  # 1 hora
                    os.remove(file_path)
    except Exception as e:
        print(f"Error durante la limpieza de archivos: {str(e)}")