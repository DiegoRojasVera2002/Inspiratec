from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from dotenv import load_dotenv
from openai import OpenAI
import os
import cv2
import numpy as np
import base64
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Definir el diseño de la UI en KV language
kv = '''
#:kivy 2.0.0

<CameraScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        
        Label:
            text: '¡Cámara Mágica! 📸'
            font_size: '24sp'
            size_hint_y: 0.1
            color: 0.31, 0.80, 0.77, 1  # Color turquesa
            
        Camera:
            id: camera
            resolution: (640, 480)
            play: True
            size_hint_y: 0.6
            
        Button:
            text: '¡Tomar Foto! 📸'
            size_hint_y: 0.15
            font_size: '20sp'
            background_color: 0.31, 0.80, 0.77, 1  # Color turquesa
            on_press: root.capture()
            
        Label:
            id: status_label
            text: ''
            size_hint_y: 0.15
            text_size: self.size
            halign: 'center'
            valign: 'middle'
            color: 0.31, 0.80, 0.77, 1  # Color turquesa

<ResultScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        
        Label:
            text: '¡Tu foto mágica! ✨'
            font_size: '24sp'
            size_hint_y: 0.1
            color: 0.31, 0.80, 0.77, 1
            
        Image:
            id: captured_image
            size_hint_y: 0.5
            
        ScrollView:
            size_hint_y: 0.25
            Label:
                id: description_label
                text: ''
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                halign: 'center'
                color: 0.31, 0.80, 0.77, 1
                
        BoxLayout:
            size_hint_y: 0.15
            spacing: 10
            
            Button:
                text: '📸 Nueva Foto'
                font_size: '18sp'
                background_color: 0.31, 0.80, 0.77, 1
                on_press: root.take_new_photo()
                
            Button:
                text: '💾 Guardar'
                font_size: '18sp'
                background_color: 0.31, 0.80, 0.77, 1
                on_press: root.save_photo()
'''

class CameraScreen(Screen):
    def capture(self):
        camera = self.ids.camera
        timestr = datetime.now().strftime("%Y%m%d_%H%M%S")
        camera.export_to_png(f"IMG_{timestr}.png")
        self.manager.get_screen('result').set_image(f"IMG_{timestr}.png")
        self.manager.current = 'result'

class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_image_path = None
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def set_image(self, image_path):
        self.current_image_path = image_path
        self.ids.captured_image.source = image_path
        self.analyze_image(image_path)

    def analyze_image(self, image_path):
        try:
            self.ids.description_label.text = "🤔 Analizando la imagen..."
            
            # Leer y codificar la imagen
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Obtener descripción de OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe esta imagen de forma divertida y amigable para niños. Usa un lenguaje alegre y simple."
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
            
            self.ids.description_label.text = response.choices[0].message.content
            
        except Exception as e:
            self.ids.description_label.text = f"¡Ups! Algo salió mal: {str(e)}"

    def take_new_photo(self):
        if self.current_image_path and os.path.exists(self.current_image_path):
            os.remove(self.current_image_path)
        self.manager.current = 'camera'

    def save_photo(self):
        if not self.current_image_path:
            return
        
        # Aquí puedes implementar la lógica para guardar la foto en una ubicación específica
        timestr = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_path = f"saved_photo_{timestr}.png"
        os.rename(self.current_image_path, new_path)
        self.ids.description_label.text += "\n\n¡Foto guardada! 💾"

class CameraMagicaApp(App):
    def build(self):
        # Cargar el diseño KV
        Builder.load_string(kv)
        
        # Crear el administrador de pantallas
        sm = ScreenManager()
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ResultScreen(name='result'))
        
        return sm

if __name__ == '__main__':
    CameraMagicaApp().run()