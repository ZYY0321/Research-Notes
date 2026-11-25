"""Seed files for zyy-e31-nologin-v1 setup. No grading rules."""
from __future__ import annotations

import base64
import os
import secrets
import string

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def alphabet_token(prefix, length=6):
    alphabet = string.ascii_uppercase + string.digits
    return prefix + "".join(secrets.choice(alphabet) for _ in range(length))


def write_text(path, text):
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def pdf_bytes(token):
    stream = ("BT /F1 24 Tf 72 700 Td (%s) Tj ET\n" % token).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    blob = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0]
    for index, body in enumerate(objects, 1):
        offsets.append(len(blob))
        blob += ("%d 0 obj\n" % index).encode("ascii") + body + b"\nendobj\n"
    xref_at = len(blob)
    blob += ("xref\n0 %d\n" % (len(objects) + 1)).encode("ascii")
    blob += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        blob += ("%010d 00000 n \n" % offset).encode("ascii")
    blob += (
        "trailer << /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref_at)
    ).encode("ascii")
    return blob


def plain_rtf(text):
    body = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    body = body.replace("\n", "\\\n")
    return ("{\\rtf1\\ansi\\ansicpg936\n" + body + "\n}").encode("latin1")


def apply(seeds, marker, today):
    seed_token = alphabet_token("SEED-")
    photo_name = ""
    for item in seeds:
        kind = item["kind"]
        path = os.path.expanduser(item["path"])
        parent = path if kind == "bundle" else os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if kind == "text":
            text = item["text"].replace("{marker}", marker).replace("{today}", today)
            write_text(path, text)
        elif kind == "rtf":
            text = item["text"].replace("{marker}", marker).replace("{today}", today)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as handle:
                handle.write(plain_rtf(text))
        elif kind == "pdf":
            with open(path, "wb") as handle:
                handle.write(pdf_bytes(seed_token))
            if item.get("token_file"):
                write_text(item["token_file"], seed_token + "\n")
        elif kind == "png":
            photo_name = item.get("name_pattern", "e31-photo-{marker}.png").replace("{marker}", marker)
            dest = os.path.join(path, photo_name) if item.get("as_dir") else path
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as handle:
                handle.write(PNG_1X1)
            if item.get("name_file"):
                write_text(item["name_file"], photo_name + "\n")
        elif kind == "bundle":
            os.makedirs(path, exist_ok=True)
            for name in item["names"]:
                write_text(os.path.join(path, name), name + "\n")
            store = os.path.join(path, ".DS_Store")
            if os.path.lexists(store):
                os.remove(store)
        else:
            raise ValueError("unknown seed %s" % kind)
    return {"seed_token": seed_token, "photo_name": photo_name}
