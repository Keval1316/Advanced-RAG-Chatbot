import os
from typing import Optional, Dict, Any, List
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def check_health(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    # --- Authentication ---
    def register(self, email: str, username: str, password: str) -> Dict[str, Any]:
        try:
            r = requests.post(
                f"{self.base_url}/auth/register",
                json={"email": email, "username": username, "password": password},
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": f"Connection error: {str(e)}"}}

    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        try:
            r = requests.post(
                f"{self.base_url}/auth/login",
                json={"username_or_email": username_or_email, "password": password},
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": f"Connection error: {str(e)}"}}

    def get_me(self, token: str) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/users/me", headers=self._headers(token), timeout=5)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    # --- Knowledge Bases ---
    def list_knowledge_bases(self, token: str) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/knowledge-bases/", headers=self._headers(token), timeout=5)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def create_knowledge_base(self, token: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        try:
            r = requests.post(
                f"{self.base_url}/knowledge-bases/",
                json={"name": name, "description": description},
                headers=self._headers(token),
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def delete_knowledge_base(self, token: str, kb_id: str) -> Dict[str, Any]:
        try:
            r = requests.delete(f"{self.base_url}/knowledge-bases/{kb_id}", headers=self._headers(token), timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    # --- Documents ---
    def list_documents(self, token: str, kb_id: str) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/documents/kb/{kb_id}", headers=self._headers(token), timeout=5)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def upload_document(self, token: str, kb_id: str, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        try:
            files = {"file": (filename, file_bytes, content_type)}
            data = {"knowledge_base_id": kb_id}
            r = requests.post(
                f"{self.base_url}/documents/upload",
                files=files,
                data=data,
                headers=self._headers(token),
                timeout=60
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def delete_document(self, token: str, doc_id: str) -> Dict[str, Any]:
        try:
            r = requests.delete(f"{self.base_url}/documents/{doc_id}", headers=self._headers(token), timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    # --- Chat & Conversations ---
    def list_conversations(self, token: str, kb_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/chat/conversations"
            params = {"kb_id": kb_id} if kb_id else {}
            r = requests.get(url, params=params, headers=self._headers(token), timeout=5)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def get_messages(self, token: str, conv_id: str) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/chat/conversations/{conv_id}/messages", headers=self._headers(token), timeout=5)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def send_message(self, token: str, kb_id: str, message: str, conv_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            payload = {
                "knowledge_base_id": kb_id,
                "message": message,
                "conversation_id": conv_id
            }
            r = requests.post(f"{self.base_url}/chat/message", json=payload, headers=self._headers(token), timeout=60)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

    def delete_conversation(self, token: str, conv_id: str) -> Dict[str, Any]:
        try:
            r = requests.delete(f"{self.base_url}/chat/conversations/{conv_id}", headers=self._headers(token), timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}


api_client = APIClient()
