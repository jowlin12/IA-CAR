# Estructura del proyecto:
# 
# car-detection-api/
# ├── netlify.toml
# ├── requirements.txt
# ├── runtime.txt
# └── netlify/
#     └── functions/
#         ├── detect_vehicle/
#         │   ├── detect_vehicle.py
#         │   └── requirements.txt
#         └── __init__.py

# netlify/functions/detect_vehicle/detect_vehicle.py
from http.client import responses
import json
import easyocr
import torch
from PIL import Image
import requests
from io import BytesIO
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification

def init_models():
    # Modelo para OCR
    reader = easyocr.Reader(['es'])
    
    # Modelo para detección de marca y tipo de vehículo
    processor = AutoImageProcessor.from_pretrained("nvidia/mit-b0")
    model = AutoModelForImageClassification.from_pretrained("nvidia/mit-b0")
    
    return reader, processor, model

def process_plate(reader, image):
    results = reader.readtext(np.array(image))
    if not results:
        return ""
    return max(results, key=lambda x: x[2])[1]

def classify_vehicle(processor, model, image):
    inputs = processor(image, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits.softmax(1)
        
    pred_class = model.config.id2label[probs.argmax().item()]
    marca, tipo = pred_class.split(" ", 1) if " " in pred_class else (pred_class, "Desconocido")
    return marca, tipo

def handler(event, context):
    # Verificar método HTTP
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Método no permitido'})
        }
    
    try:
        # Obtener URL de la imagen del body
        body = json.loads(event['body'])
        image_url = body.get('url')
        
        if not image_url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'URL de imagen no proporcionada'})
            }
        
        # Descargar imagen
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        
        # Inicializar modelos
        reader, processor, model = init_models()
        
        # Procesar imagen
        placa = process_plate(reader, image)
        marca, tipo = classify_vehicle(processor, model, image)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'placa': placa,
                'marca': marca,
                'tipo': tipo
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
