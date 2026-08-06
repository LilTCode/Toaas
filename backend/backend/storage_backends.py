"""Custom Django storage backends.

Vercel Functions run on a read-only filesystem, so Django's default
FileSystemStorage cannot accept uploads in production. VercelBlobStorage sends
uploads to Vercel Blob instead and serves them from the Blob CDN.

Enabled automatically in backend/settings.py whenever BLOB_READ_WRITE_TOKEN is
present in the environment; local development keeps using the filesystem.
"""

import os
import posixpath
from urllib.parse import urljoin, urlparse

import vercel_blob
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from vercel_blob.errors import BlobRequestError


@deconstructible
class VercelBlobStorage(Storage):
    """Store uploaded files in Vercel Blob.

    The full blob URL is what gets saved to the model field, so templates and
    API responses can use the value directly with no extra lookups. `url()`
    therefore just returns the stored name when it is already absolute.
    """

    def __init__(self, token=None, base_path=""):
        self._token = token or os.getenv("BLOB_READ_WRITE_TOKEN", "")
        self.base_path = base_path.strip("/")

    @property
    def token(self):
        if not self._token:
            raise ImproperlyConfigured(
                "BLOB_READ_WRITE_TOKEN is not set. Attach a Blob store to the "
                "Vercel project, or unset it locally to use filesystem storage."
            )
        return self._token

    def _options(self, **extra):
        return {"token": self.token, **extra}

    def _full_path(self, name):
        name = name.lstrip("/")
        return posixpath.join(self.base_path, name) if self.base_path else name

    # Django writes uploads through _save and expects the stored name back.
    def _save(self, name, content):
        content.open()
        try:
            data = content.read()
        finally:
            content.close()
        if not isinstance(data, bytes):
            data = bytes(data)

        result = vercel_blob.put(
            self._full_path(name),
            data,
            self._options(addRandomSuffix="true"),
        )
        return result["url"]

    def _open(self, name, mode="rb"):
        if "w" in mode:
            raise ValueError("VercelBlobStorage does not support opening files for writing.")
        import requests

        response = requests.get(self.url(name), timeout=30)
        response.raise_for_status()
        return ContentFile(response.content, name=name)

    def url(self, name):
        if not name:
            return ""
        # Names are stored as absolute blob URLs by _save.
        if urlparse(name).scheme in ("http", "https"):
            return name
        base = os.getenv("BLOB_PUBLIC_BASE_URL", "")
        if base:
            return urljoin(base.rstrip("/") + "/", self._full_path(name))
        return self._full_path(name)

    def exists(self, name):
        # Uploads use addRandomSuffix, so names never collide and Django does
        # not need a pre-write existence check. Reporting False avoids a
        # network round trip on every save.
        return False

    def size(self, name):
        return self._head(name).get("size", 0)

    def delete(self, name):
        if not name:
            return
        try:
            vercel_blob.delete(self.url(name), self._options())
        except BlobRequestError:
            # Already gone, or never made it to the store. Django's contract
            # for delete() is "not an error if it does not exist".
            pass

    def get_modified_time(self, name):
        from django.utils.dateparse import parse_datetime

        return parse_datetime(self._head(name).get("uploadedAt", "")) or None

    def _head(self, name):
        return vercel_blob.head(self.url(name), self._options())

    def get_available_name(self, name, max_length=None):
        # Vercel Blob adds its own random suffix, so Django's dedup loop
        # (which calls exists() repeatedly) is unnecessary.
        return name
