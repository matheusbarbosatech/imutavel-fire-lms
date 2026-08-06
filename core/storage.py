import os
import uuid
from django.core.files.storage import Storage
from django.core.files.base import File
from supabase import create_client
from django.conf import settings

class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self.bucket = settings.SUPABASE_BUCKET

    def _generate_path(self, name):
        ext = name.split('.')[-1]
        return f"uploads/{uuid.uuid4().hex}.{ext}"

    def _save(self, name, content):
        path = self._generate_path(name)
        content.seek(0)
        self.client.storage.from_(self.bucket).upload(
            path=path,
            file=content.read(),
            file_options={"content-type": content.content_type}
        )
        return path

    def _open(self, name, mode='rb'):
        content = self.client.storage.from_(self.bucket).download(name)
        return File(content)

    def url(self, name):
        res = self.client.storage.from_(self.bucket).create_signed_url(name, 3600)
        return res['signedURL']

    def exists(self, name):
        try:
            self.client.storage.from_(self.bucket).info(name)
            return True
        except:
            return False

    def delete(self, name):
        self.client.storage.from_(self.bucket).remove([name])