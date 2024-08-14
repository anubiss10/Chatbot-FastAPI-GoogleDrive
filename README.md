# ChatBot-Whatsapp-Python-FastApi

**ChatBot-Whatsapp-Python-FastApi** es una aplicación que integra un chatbot con WhatsApp utilizando Python y FastAPI. Este proyecto facilita la comunicación automatizada con los usuarios de WhatsApp mediante un servicio de chatbot que maneja mensajes entrantes y salientes.

## Características

- **Integración con la API de WhatsApp Business:** Permite enviar y recibir mensajes a través de WhatsApp.
- **Manejo de mensajes:** El bot puede responder a mensajes de texto e imágenes.
- **Almacenamiento en Google Drive:** Las imágenes recibidas se pueden almacenar en Google Drive.
- **Autenticación y manejo de tokens:** Usa credenciales de Google Drive para autenticación y manejo de tokens.

## Requisitos

- Python 3.7 o superior
- FastAPI
- Uvicorn
- aiohttp
- requests
- google-auth
- google-auth-oauthlib
- google-api-python-client
- python-dotenv

## Instalación

1. **Clona el repositorio:**

```bash
git clone https://github.com/anubiss10/ChatBot-Whatsapp-Python-FastApi.git
cd ChatBot-Whatsapp-Python-FastApi
```
2. **Crea un entorno virtual y actívalo:**

  ```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```
3. **Instala las dependencias:**

```bash
pip install -r requirements.txt
```
4. **Copia el archivo .env.example a .env y completa con tus credenciales:**

```bash
cp .env.example .env
```
Asegúrate de proporcionar valores para VERIFY_TOKEN, TOKENADMIN, y la configuración para Google Drive (incluyendo credentials.json y token.json).

## Uso
**Ejecuta la aplicación con Uvicorn:**

```bash
uvicorn main:app --reload
```
Esto iniciará el servidor en http://127.0.0.1:8000.

## Configura el webhook en la API de WhatsApp:

## Asegúrate de que tu endpoint de webhook esté accesible desde la web y configura la URL de webhook en la API de WhatsApp Business.

## Endpoints
# GET /webhook
Verifica la configuración del webhook. Responde con un desafío para confirmar la suscripción.

** Parámetros:**
```
hub.mode: Modo de la suscripción.
hub.verify_token: Token de verificación.
hub.challenge: Desafío de verificación.
```
Respuesta:
```
200 OK: Verificación exitosa.
403 Forbidden: Verificación fallida.
```
# POST /webhook
Maneja los mensajes entrantes desde WhatsApp. Procesa los mensajes de texto e imágenes, y los sube a Google Drive si es necesario.

Cuerpo de la solicitud:

```json

{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "type": "image",
                "from": "PHONE_NUMBER",
                "image": {
                  "id": "MEDIA_ID",
                  "caption": "CAPTION"
                }
              }
            ],
            "metadata": {
              "phone_number_id": "PHONE_NUMBER_ID"
            }
          }
        }
      ]
    }
  ]
}
```
Respuesta:
```
200 OK: Mensaje procesado con éxito.
403 Forbidden: Error al procesar el mensaje.
```
**Configuración de Google Drive**
Asegúrate de tener las siguientes credenciales y archivos:

**credentials.json**: Archivo de credenciales de Google Drive.
**token.json**: Archivo de tokens de acceso y refresco.
