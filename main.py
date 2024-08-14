from datetime import datetime
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.responses import JSONResponse
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import logging
import aiohttp
import os
import requests
from google_drive_upload import GoogleDriveManager
from dotenv import load_dotenv

app = FastAPI()

class WebhookChallenge(BaseModel):
    hub_mode: str
    hub_challenge: str
    hub_verify_token: str

load_dotenv()
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
TOKENADMIN = os.getenv('TOKENADMIN')

# Crear una instancia de GoogleDriveManager
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly",
          "https://www.googleapis.com/auth/drive.file"]

drive_manager = GoogleDriveManager(credentials_path="credentials.json", token_path="token.json", scopes=SCOPES)

# Dictionary to store images temporarily until a captioned image is received
pending_images = {}

import io

async def download_image(media_id, phone_number_id):
    url = f"https://graph.facebook.com/v18.0/{media_id}?phone_number_id={phone_number_id}"
    headers = {"Authorization": f"Bearer {TOKENADMIN}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        image_url = data.get("url")
        
        if image_url:
            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()
            
            # Guardar el contenido de la imagen en memoria
            image_content = io.BytesIO(image_response.content)
            return image_content
        else:
            print("No se pudo obtener la URL de descarga de la imagen.")
            return None
    except Exception as e:
        print(f"Error al descargar la imagen: {e}")
        return None


@app.get("/webhook")
async def webhook_get(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("WEBHOOK_VERIFIED")
        return Response(content=challenge, status_code=HTTP_200_OK)
    else:
        logging.info("VERIFICATION_FAILED")
        return Response(content="Verification failed", status_code=HTTP_403_FORBIDDEN)

@app.post("/webhook")
async def handle_webhook(request: Request):
    logging.info("Incoming webhook message:")
    logging.info(await request.json())

    body = await request.json()
    message = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]

    if message.get("type") == "image":
        media_id = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("image", {}).get("id")
        business_phone_number_id = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
        media_caption = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("image", {}).get("caption")
        
        if media_caption:
            image_content = await download_image(media_id, business_phone_number_id)
            if image_content:
                folder_id = await drive_manager.create_drive_folder(media_caption)
                await drive_manager.upload_file(image_content, folder_id, f"{media_id}.jpg")
        else:
            pending_images[media_id] = {
                "phone_number_id": business_phone_number_id
            }
        
        if pending_images and media_caption:
            for media_id, metadata in pending_images.items():
                image_content = await download_image(media_id, metadata["phone_number_id"])
                if image_content:
                    await drive_manager.upload_file(image_content, folder_id, f"{media_id}.jpg")
            pending_images.clear()
        
        async with aiohttp.ClientSession() as session:
            url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
            headers = {"Authorization": f"Bearer {TOKENADMIN}"}
            data = {
                "messaging_product": "whatsapp",
                "to": message.get("from"),
                "text": {"body": "Subiendo tu archivo..."},
                "context": {"message_id": message.get("id")}
            }
            
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    mensaje_confirmacion = {
                        "messaging_product": "whatsapp",
                        "to": message.get("from"),
                        "text": {"body": "¡Archivo subido exitosamente!"},
                        "context": {"message_id": message.get("id")}
                    }
                    await session.post(url, json=mensaje_confirmacion, headers=headers)
                    return JSONResponse(content={"message": "Response sent successfully"})
                else:
                    return JSONResponse(content={"message": "Failed to send response"}, status_code=response.status)
        
    return JSONResponse(content={"message": "No text message found"})
