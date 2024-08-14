import os
import io
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from starlette.exceptions import HTTPException

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly",
          "https://www.googleapis.com/auth/drive.file"]

class GoogleDriveManager:
    def __init__(self, credentials_path: str, token_path: str, scopes: list):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes
        self.creds = None
        self.authenticate()
        
    def authenticate(self):
        """Authenticates with Google Drive API."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                self.creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(self.creds.to_json())
        print("Authentication successful!")

    async def upload_file(self, file_content: io.BytesIO, folder_id: str, file_name: str):
        """Uploads a file to Google Drive."""
        self.authenticate()
        service = build("drive", "v3", credentials=self.creds)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaIoBaseUpload(file_content, mimetype='image/jpeg', resumable=True)
        try:
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print('File ID: %s' % file.get('id'))
        except HttpError as error:
            logging.error(f"An error occurred while uploading file to Google Drive: {error}")
            raise HTTPException(status_code=403, detail="Failed to upload file to Google Drive")

    async def create_drive_folder(self, folder_name: str):
        """Creates a folder in Google Drive."""
        self.authenticate()
        service = build("drive", "v3", credentials=self.creds)
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        try:
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            print(f'Folder ID: {folder.get("id")}')
            return folder.get("id")
        except HttpError as error:
            logging.error(f"An error occurred while creating folder in Google Drive: {error}")
            raise HTTPException(status_code=403, detail="Failed to create folder in Google Drive")
