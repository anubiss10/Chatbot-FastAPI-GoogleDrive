from datetime import datetime
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND,HTTP_403_FORBIDDEN
from starlette.responses import JSONResponse

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import logging
import aiohttp
from google_drive_upload import GoogleDriveManager
app = FastAPI()

class WebhookChallenge(BaseModel):
    hub_mode: str
    hub_challenge: str
    hub_verify_token: str

VERIFY_TOKEN = "12345"
TOKENADMIN = "EAALRJqqqhLsBO6NvpJoo06WLjXJrSdxdeL4Nj4YgQrSkg96YfwOE79oPkXnj5r9aKY7Lryyw2hjXVz2EKZBDYhOKMOA31EuE8CdeseYkeFZARXGuKgAs0GAywg8lstN4jj7osnIojeKi5ve30YZBJQNfhWtErqTiTXKhMyPJ7t1G39ZAA1LIb2QuMJxZAZBGstcods8fuPX63zfD1qHrsZD"
# Crear una instancia de GoogleDriveManager
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly",
          "https://www.googleapis.com/auth/drive.file"]

drive_manager = GoogleDriveManager(credentials_path="credentials.json", token_path="token.json", scopes=SCOPES)

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

    
async def download_image(image_url, file_name):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                image_data = await response.read()
                with open(file_name, "wb") as f:
                    f.write(image_data)
                logging.info("Image downloaded successfully.")
            else:
                logging.error("Failed to download image")
                
@app.post("/webhook")
async def handle_webhook(request: Request):
    logging.info("Incoming webhook message:")
    logging.info(await request.json())

    body = await request.json()
    message = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]

    if message.get("type") == "image":
        business_phone_number_id = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
        message_id = message.get("id")  # Captura el message_id
        print("Message ID:", message_id)  # Mostrar el message_id en la consola

        async with aiohttp.ClientSession() as session:
            url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
            headers = {"Authorization": f"Bearer {TOKENADMIN}"}
            data = {
                "messaging_product": "whatsapp",
                "to": message.get("from"),
                "text": {"body": "Okay, dame unos segundos para subir tu archivo"},
                "context": {"message_id": message.get("id")}
            }
            
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    # La primera solicitud POST fue exitosa, ahora realizamos la segunda solicitud GET
                    graph_url2 = f"https://graph.facebook.com/v19.0/{message_id}/"
                    headers2 = {"Authorization": f"Bearer {TOKENADMIN}"}
                    
                    async with session.get(graph_url2, headers=headers2) as response2:
                        if response2.status == 200:
                            graph_response = await response2.json()
                            image_url = graph_response.get("url")  # Obtiene la URL de la imagen

                            # Descarga la imagen utilizando la URL obtenida
                            await download_image(image_url, f"descargas/{message_id}.jpg")

                            return JSONResponse(content={"message": "Webhook handled successfully"})
                        else:
                            return JSONResponse(content={"message": "Failed to get image URL"}, status_code=response2.status)
                else:
                    return JSONResponse(content={"message": "Failed to send response"}, status_code=response.status)
                
    return JSONResponse(content={"message": "Webhook handled successfully"})
