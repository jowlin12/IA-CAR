import json
import easyocr
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import re
from typing import Tuple, Dict, Any

def validate_plate(text: str) -> bool:
    """
    Valida si el texto tiene formato de placa vehicular.
    Ejemplos válidos: ABC123, AB123CD, etc.
    """
    # Ajusta este patrón según el formato de placas de tu país
    plate_pattern = r'^[A-Z]{2,3}\d{3,4}[A-Z]{0,2}$'
    return bool(re.match(plate_pattern, text.replace(' ', '')))

def detect_vehicle_type(image: np.ndarray) -> str:
    """
    Detecta el tipo de vehículo basado en características de la imagen.
    Por ahora retorna un valor por defecto, pero aquí podrías integrar
    un modelo de clasificación de vehículos.
    """
    # TODO: Implementar detección real del tipo de vehículo
    return "Automóvil"

def detect_vehicle_brand(image: np.ndarray) -> str:
    """
    Detecta la marca del vehículo basado en características de la imagen.
    Por ahora retorna un valor por defecto, pero aquí podrías integrar
    un modelo de reconocimiento de marcas.
    """
    # TODO: Implementar detección real de la marca
    return "No detectada"

def process_image(image_url: str) -> Tuple[str, str, str]:
    """
    Procesa la imagen y retorna la placa, marca y tipo de vehículo.
    """
    try:
        # Descargar y verificar la imagen
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Verificar el tipo de contenido
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError('La URL no corresponde a una imagen válida')
            
        # Abrir la imagen
        image = Image.open(BytesIO(response.content))
        image_np = np.array(image)
        
        # Inicializar OCR
        reader = easyocr.Reader(['es', 'en'])
        
        # Detectar texto en la imagen
        results = reader.readtext(image_np)
        
        # Buscar la placa entre los resultados
        plate = "No detectada"
        for _, text, confidence in results:
            text = text.upper().replace(' ', '')
            if validate_plate(text) and confidence > 0.5:
                plate = text
                break
        
        # Detectar marca y tipo
        brand = detect_vehicle_brand(image_np)
        vehicle_type = detect_vehicle_type(image_np)
        
        return plate, brand, vehicle_type
        
    except requests.RequestException as e:
        raise ValueError(f"Error al obtener la imagen: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error al procesar la imagen: {str(e)}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Manejador principal de la función serverless.
    """
    # Verificar método HTTP
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Método no permitido. Use POST.',
                'status': 'error'
            })
        }
    
    try:
        # Obtener URL de la imagen del body
        body = json.loads(event['body'])
        image_url = body.get('url')
        
        if not image_url:
            raise ValueError('URL de imagen no proporcionada')
        
        # Procesar la imagen
        plate, brand, vehicle_type = process_image(image_url)
        
        # Retornar resultados
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'data': {
                    'placa': plate,
                    'marca': brand,
                    'tipo': vehicle_type
                }
            })
        }
        
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'error'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Error interno del servidor',
                'status': 'error'
            })
        }
