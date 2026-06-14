"""Google Drive/Docs helper for agents and scripts.

Reads and writes the team Drive using the existing service-account key — NO
OAuth, no browser flow. Point $GOOGLE_APPLICATION_CREDENTIALS at the SA JSON
(falls back to ~/secrets/drive-sa.json) and the SA must be shared on the
team folder / docs.

CLI:
    python3 -m core.drive list            # names + IDs in the team folder
    python3 -m core.drive read Updates    # export a doc (by name or ID) as text
    python3 -m core.drive append "<text>" # append a timestamped block to "Updates"
"""
from __future__ import annotations

import os
import sys
import io
import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Shared team folder (CLAUDE.md §3 "shared Google Drive").
TEAM_FOLDER_ID = "1NyfQ7-vjreLQ0o7cUYNnABVpkNlKpOM5"
SCOPES = ["https://www.googleapis.com/auth/drive"]
_DEFAULT_KEY = os.path.expanduser("~/secrets/drive-sa.json")

GDOC_MIME = "application/vnd.google-apps.document"

_drive = None
_docs = None


def _creds():
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or _DEFAULT_KEY
    if not os.path.exists(key_path):
        raise FileNotFoundError(
            f"service-account key not found at {key_path!r}; set "
            "$GOOGLE_APPLICATION_CREDENTIALS to the Drive SA JSON"
        )
    return service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)


def _client():
    """Return a cached Drive v3 service built from the SA key."""
    global _drive
    if _drive is None:
        _drive = build("drive", "v3", credentials=_creds(), cache_discovery=False)
    return _drive


def _docs_client():
    """Return a cached Docs v1 service (shares the Drive SA creds/scope)."""
    global _docs
    if _docs is None:
        _docs = build("docs", "v1", credentials=_creds(), cache_discovery=False)
    return _docs


def list_team_files(folder_id: str = TEAM_FOLDER_ID) -> list[dict]:
    """List {id, name, mimeType} for every file in the team folder."""
    svc = _client()
    files: list[dict] = []
    page_token = None
    while True:
        resp = (
            svc.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                orderBy="name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def _resolve(name_or_id: str) -> dict:
    """Resolve a name (matched in the team folder, case-insensitive) or a raw
    file ID to a {id, name, mimeType} dict."""
    files = list_team_files()
    # exact (case-insensitive) name match first
    for f in files:
        if f["name"].lower() == name_or_id.lower():
            return f
    # then an ID match within the folder
    for f in files:
        if f["id"] == name_or_id:
            return f
    # otherwise assume it is a raw ID anywhere the SA can see
    meta = (
        _client()
        .files()
        .get(fileId=name_or_id, fields="id, name, mimeType", supportsAllDrives=True)
        .execute()
    )
    return meta


def read_doc(name_or_id: str) -> str:
    """Resolve a name (e.g. "Updates") or ID and return its text. Google Docs
    are exported as text/plain; other types are downloaded and decoded."""
    f = _resolve(name_or_id)
    svc = _client()
    if f["mimeType"] == GDOC_MIME:
        data = (
            svc.files()
            .export(fileId=f["id"], mimeType="text/plain")
            .execute()
        )
        return data.decode("utf-8") if isinstance(data, bytes) else data
    # Other Google-apps types (sheets/slides) can't be get_media'd; export them.
    if f["mimeType"].startswith("application/vnd.google-apps"):
        data = svc.files().export(fileId=f["id"], mimeType="text/plain").execute()
        return data.decode("utf-8") if isinstance(data, bytes) else data
    # Regular binary/text file: download bytes and decode.
    buf = io.BytesIO()
    req = svc.files().get_media(fileId=f["id"], supportsAllDrives=True)
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8", errors="replace")


def append_to_updates(text: str, doc_name: str = "Updates") -> str:
    """Append a timestamped block to the "Updates" doc via the Docs API.
    Returns the doc ID written to."""
    f = _resolve(doc_name)
    if f["mimeType"] != GDOC_MIME:
        raise ValueError(f"{doc_name!r} is not a Google Doc (mimeType={f['mimeType']})")
    docs = _docs_client()
    doc = docs.documents().get(documentId=f["id"]).execute()
    # End-of-body insertion index: last structural element's endIndex - 1
    # (you cannot insert at/after the final newline).
    content = doc.get("body", {}).get("content", [])
    end_index = content[-1].get("endIndex", 1) if content else 1
    insert_at = max(1, end_index - 1)

    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    block = f"\n\n--- {stamp} ---\n{text}\n"
    docs.documents().batchUpdate(
        documentId=f["id"],
        body={"requests": [{"insertText": {"location": {"index": insert_at}, "text": block}}]},
    ).execute()
    return f["id"]


def _main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "list":
        for f in list_team_files():
            print(f"{f['id']}\t{f['mimeType']}\t{f['name']}")
        return 0
    if cmd == "read":
        if len(argv) < 2:
            print("usage: python3 -m core.drive read <name_or_id>", file=sys.stderr)
            return 2
        print(read_doc(argv[1]))
        return 0
    if cmd == "append":
        if len(argv) < 2:
            print("usage: python3 -m core.drive append \"<text>\"", file=sys.stderr)
            return 2
        doc_id = append_to_updates(argv[1])
        print(f"appended to Updates ({doc_id})")
        return 0
    print(f"unknown command {cmd!r}; use list | read | append", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
