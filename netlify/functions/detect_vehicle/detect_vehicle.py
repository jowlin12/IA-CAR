# netlify/functions/detect_vehicle/detect_vehicle.py
import json
import easyocr
import requests
from PIL import Image
from io import BytesIO
import numpy as np

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
        
        # Inicializar OCR
        reader = easyocr.Reader(['es'])
        
        # Detectar texto
        results = reader.readtext(np.array(image))
        placa = results[0][1] if results else "No detectada"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'placa': placa,
                'marca': 'Detección de marca no implementada',
                'tipo': 'Detección de tipo no implementada'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
