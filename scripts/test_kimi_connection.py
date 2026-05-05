import os
from src.kimi_client import KimiK2Client
import logging

logging.basicConfig(level=logging.INFO)

def test_kimi_connectivity():
    print("Iniciando validación de Kimi API...")
    try:
        client = KimiK2Client()
        messages = [{"role": "user", "content": "Hola Kimi, ¿estás operativo?"}]
        response = client.chat_completion(messages)
        
        if response:
            print("Conexión Exitosa. Respuesta recibida:")
            print(response)
        else:
            print("Error: No se recibió respuesta de Kimi.")
    except Exception as e:
        print(f"Error crítico durante la prueba: {e}")

if __name__ == "__main__":
    test_kimi_connectivity()
