import os
import dropbox
from django.conf import settings
from dropbox.exceptions import ApiError

DROPBOX_TOKEN = getattr(settings, "DROPBOX_TOKEN", None)
DROPBOX_FOLDER = '/OpenData BACKUP'

if not DROPBOX_TOKEN:
    raise ValueError("Please set the DROPBOX_TOKEN environment variable")

def upload_to_dropbox(file_path):
    """
    Upload a local file to Dropbox and return its shared link.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    dest_path = f"{DROPBOX_FOLDER}/{os.path.basename(file_path)}"

    try:
        # Upload file
        with open(file_path, 'rb') as f:
            dbx.files_upload(f.read(), dest_path, mode=dropbox.files.WriteMode.overwrite)

        # Check for existing shared links
        links = dbx.sharing_list_shared_links(path=dest_path, direct_only=True).links
        if links:
            shared_link = links[0].url
        else:
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(dest_path)
            shared_link = shared_link_metadata.url

        return {
            'dropbox_path': dest_path,
            'shared_link': shared_link
        }

    except ApiError as e:
        raise RuntimeError(f"Dropbox API error: {e}")
