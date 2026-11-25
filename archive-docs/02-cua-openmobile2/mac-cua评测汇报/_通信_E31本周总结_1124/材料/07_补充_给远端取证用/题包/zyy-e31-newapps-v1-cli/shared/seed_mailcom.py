#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 IMAP APPEND 给 mail.com 测试邮箱灌种子邮件。

只从 --creds 读取「账号：」「密码：」。不走 SMTP，不改账号设置。
种子带 X-E31-Seed: 1。--reset 删这种邮件（INBOX 与 Drafts），并清空 Drafts 里其余邮件，再删 Sent 里主题或正文含 E31 的邮件。--clear-residue 只做后两步，不动收件箱。
每次 IMAP 命令后暂停 1 秒，一轮最多处理 8 封。
"""

from __future__ import annotations

import argparse
import email
import email.utils
import imaplib
import inspect
import json
import os
import re
import secrets
import struct
import sys
import time
import zlib
from email.header import Header, decode_header, make_header
from html.parser import HTMLParser
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, getaddresses, make_msgid

HOST = "imap.mail.com"
PORT = 993
PAUSE_SECONDS = 1.0
MAX_BATCH = 8
SCAN_LIMIT = 30
FROM_ADDR = "boss@example.com"
TO_ADDR = "seed-local@example.com"
DESIGN_SENTENCE = "请把附件图缩到 640×480，右下角加文字 E31-标记，存成回复草稿，不要发送"

IMAP4 = imaplib.IMAP4
IMAP4.debug = 0

_LABEL_PREFIX = r"[ \t\u3000]*(?:[-*+][ \t\u3000]*)?"
_ACCOUNT_RE = re.compile(
    rf"(?m)^{_LABEL_PREFIX}账号[ \t\u3000]*[:：][ \t\u3000]*(.+?)[ \t\u3000]*$"
)
_PASSWORD_RE = re.compile(
    rf"(?m)^{_LABEL_PREFIX}密码[ \t\u3000]*[:：][ \t\u3000]*(.+?)[ \t\u3000]*$"
)
_LIST_RE = re.compile(
    r"^\((?P<flags>[^)]*)\)\s+(?P<delim>\"[^\"]*\"|NIL)\s+(?P<name>.+)$"
)

# (want_seen, want_flagged)
ROLE_WANTS = {
    "design": (False, False),
    "attachment": (True, False),
    "flagged": (True, True),
    "unread": (False, False),
    "distractor": (True, False),
}

HEADER_SPECS = (
    "(BODY.PEEK[HEADER.FIELDS (X-E31-SEED)])",
    "(BODY.PEEK[HEADER])",
)
FLAG_SPECS = (
    "(FLAGS BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (X-E31-ROLE X-E31-MARKER X-E31-ATTACH)])",
    "(FLAGS BODY.PEEK[HEADER])",
)


class ImapOpError(RuntimeError):
    pass


class Seed(object):
    def __init__(self, role, subject, body, attachment=None, filename=None):
        self.role = role
        self.subject = subject
        self.body = body
        self.attachment = attachment
        self.filename = filename


def _pause():
    time.sleep(PAUSE_SECONDS)


def _blob(data) -> bytes:
    parts = []

    def walk(item):
        if item is None:
            return
        if isinstance(item, (bytes, bytearray)):
            parts.append(bytes(item))
        elif isinstance(item, str):
            parts.append(item.encode("utf-8", "replace"))
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)

    walk(data)
    return b"\n".join(parts)


def _short(data, limit=300) -> str:
    text = _blob(data).decode("utf-8", "replace")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def scrub_text(obj, secrets) -> str:
    if isinstance(obj, bytes):
        text = obj.decode("utf-8", "replace")
    else:
        text = str(obj)
    for secret in secrets or []:
        if not secret:
            continue
        text = text.replace(secret, "***")
        quoted = secret.replace("\\", "\\\\").replace('"', '\\"')
        if quoted != secret:
            text = text.replace(quoted, "***")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:400]


def emit(key, value, secrets):
    if str(key).lower() in {"password", "passwd", "user", "account", "creds"}:
        return
    text = scrub_text(value, secrets)
    print(f"{key}={text}", flush=True)


def _unquote(value: str) -> str:
    text = value.strip().strip("\u3000")
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        text = text[1:-1].strip()
    return text


def read_creds(path: str):
    try:
        raw = open(path, "rb").read()
    except OSError:
        raise ImapOpError("creds_unreadable")
    text = None
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ImapOpError("creds_unreadable")
    user_m = _ACCOUNT_RE.search(text)
    pass_m = _PASSWORD_RE.search(text)
    if not user_m or not pass_m:
        raise ImapOpError("creds_fields_missing")
    user = _unquote(user_m.group(1))
    password = _unquote(pass_m.group(1))
    if not user or not password:
        raise ImapOpError("creds_fields_missing")
    return user, password


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _row_bytes(width: int, y: int, height: int) -> bytes:
    band = (y * 6) // height
    red = (20 + band * 30) & 255
    green = (80 + band * 15) & 255
    blue = (180 - band * 20) & 255
    left = bytes((red, green, blue))
    right = bytes(((red + 60) & 255, green, blue))
    tile = left * 40 + right * 40
    need = width * 3
    return (tile * (need // len(tile) + 1))[:need]


def make_png(width: int = 800, height: int = 600) -> bytes:
    rows = []
    for y in range(height):
        rows.append(b"\x00" + _row_bytes(width, y, height))
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )


def png_ok(blob: bytes, width: int = 800, height: int = 600) -> bool:
    if not blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    index = 8
    idat = b""
    saw_iend = False
    saw_ihdr = False
    while index + 8 <= len(blob):
        length = struct.unpack(">I", blob[index : index + 4])[0]
        tag = blob[index + 4 : index + 8]
        end = index + 8 + length
        if end + 4 > len(blob):
            return False
        data = blob[index + 8 : end]
        crc = struct.unpack(">I", blob[end : end + 4])[0]
        if (zlib.crc32(tag + data) & 0xFFFFFFFF) != crc:
            return False
        if tag == b"IHDR":
            if length != 13:
                return False
            values = struct.unpack(">IIBBBBB", data)
            if values != (width, height, 8, 2, 0, 0, 0):
                return False
            saw_ihdr = True
        elif tag == b"IDAT":
            idat += data
        elif tag == b"IEND":
            saw_iend = True
        index = end + 4
        if saw_iend:
            break
    if not saw_ihdr or not saw_iend or index != len(blob):
        return False
    try:
        raw = zlib.decompress(idat)
    except zlib.error:
        return False
    return len(raw) == height * (1 + width * 3)


def header_is_seed(blob: bytes) -> bool:
    text = blob.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n[ \t]+", " ", text)
    return re.search(r"(?im)^X-E31-Seed:[ \t]*1[ \t]*$", text) is not None


def header_value(blob: bytes, name: str) -> str:
    text = blob.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n[ \t]+", " ", text)
    match = re.search(rf"(?im)^{re.escape(name)}:[ \t]*(.*)$", text)
    return match.group(1).strip() if match else ""


def parse_flags(blob: bytes) -> set:
    match = re.search(rb"FLAGS \(([^)]*)\)", blob)
    if not match:
        return set()
    inner = match.group(1).decode("ascii", "replace")
    return set(inner.split())


def decode_mime(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)


class _HtmlText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        if data:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = _HtmlText()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        return value
    return "".join(parser.parts)


def message_to_record(raw: bytes) -> dict:
    msg = email.message_from_bytes(raw)
    recipients = []
    for _name, addr in getaddresses(msg.get_all("To", [])):
        if addr:
            recipients.append(addr)
    names = []
    plain_parts = []
    html_parts = []
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename()
        if filename:
            filename = decode_mime(filename)
            if filename not in names:
                names.append(filename)
        disposition = (part.get_content_disposition() or "").lower()
        if disposition == "attachment" or filename:
            continue
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, "replace")
        if part.get_content_type() == "text/plain":
            plain_parts.append(text)
        elif part.get_content_type() == "text/html":
            html_parts.append(html_to_text(text))
    body = "\n".join(plain_parts).strip("\n")
    if not body.strip():
        body = "\n".join(html_parts).strip("\n")
    return {
        "主题": decode_mime(msg.get("Subject", "")),
        "收件人": recipients,
        "正文": body,
        "附件名": names,
    }


def to_crlf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").replace(b"\n", b"\r\n")


def build_raw(seed: Seed, marker: str) -> bytes:
    if marker not in seed.subject or marker not in seed.body:
        raise RuntimeError("marker_missing_in_seed")
    if seed.attachment is None:
        msg = MIMEText(seed.body, "plain", "utf-8")
    else:
        msg = MIMEMultipart("mixed")
        msg.attach(MIMEText(seed.body, "plain", "utf-8"))
        image = MIMEImage(seed.attachment, _subtype="png")
        filename = seed.filename or (marker + ".png")
        image.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(image)
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg["Subject"] = Header(seed.subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="example.com")
    msg["X-E31-Seed"] = "1"
    msg["X-E31-Marker"] = marker
    msg["X-E31-Role"] = seed.role
    msg["X-E31-Attach"] = "1" if seed.attachment is not None else "0"
    raw = to_crlf(msg.as_bytes())
    head = raw.split(b"\r\n\r\n", 1)[0]
    if b"X-E31-Seed: 1" not in head:
        raise RuntimeError("seed_header_missing")
    if ("X-E31-Marker: " + marker).encode("ascii") not in head:
        raise RuntimeError("marker_header_missing")
    if b"\r\nFrom: " + FROM_ADDR.encode("ascii") not in b"\r\n" + head and not head.startswith(
        b"From: " + FROM_ADDR.encode("ascii")
    ):
        if b"From: " + FROM_ADDR.encode("ascii") not in head:
            raise RuntimeError("from_missing")
    return raw


def build_seeds(scenario: str, marker: str, png: bytes) -> list:
    filename = marker + ".png"
    if scenario == "design-request":
        return [
            Seed(
                "design",
                f"请处理设计图 {marker}",
                DESIGN_SENTENCE + "\n" + marker,
                png,
                filename,
            )
        ]
    if scenario == "mixed-inbox":
        return [
            Seed(
                "attachment",
                f"设计稿附件 {marker}",
                f"附件是 800×600 的 PNG，请查收。\n{marker}",
                png,
                filename,
            ),
            Seed(
                "flagged",
                f"请优先看这封 {marker}",
                f"这封需要标星，请优先处理。\n{marker}",
            ),
            Seed(
                "unread",
                f"待处理事项甲 {marker}",
                f"这是未读邮件甲。\n{marker}",
            ),
            Seed(
                "unread",
                f"待处理事项乙 {marker}",
                f"这是未读邮件乙。\n{marker}",
            ),
            Seed(
                "distractor",
                f"茶水间植物养护周报 {marker}",
                f"本周茶水间绿植需要浇水，与设计任务无关。\n{marker}",
            ),
        ]
    return []


def new_marker() -> str:
    return "E31-" + secrets.token_hex(3).upper()


def assert_marker_path(path: str, creds_path: str):
    target = os.path.abspath(path)
    creds = os.path.abspath(creds_path)
    if target == creds or target.endswith("seed_mailcom.py") or "私密账号" in target:
        raise ImapOpError("marker_path_unsafe")
    parent = os.path.dirname(target) or "."
    if not os.path.isdir(parent):
        raise ImapOpError("marker_dir_missing")


def write_marker(path: str, marker: str, creds_path: str):
    assert_marker_path(path, creds_path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(marker + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def self_check():
    signature = inspect.signature(read_drafts)
    if list(signature.parameters)[:2] != ["user", "password"]:
        raise RuntimeError("read_drafts_signature")
    creds_sample = "- 账号：user@example.com\n- 密码：secret-value\n账号：plain@example.com\n密码：other-value\n"
    if _ACCOUNT_RE.search(creds_sample).group(1) != "user@example.com":
        raise RuntimeError("creds_account_re")
    if _PASSWORD_RE.search(creds_sample).group(1) != "secret-value":
        raise RuntimeError("creds_password_re")
    if not header_is_seed(b"X-E31-Seed: 1\r\n"):
        raise RuntimeError("seed_regex")
    if header_is_seed(b"X-E31-Seed: 10\r\n") or header_is_seed(b"Subject: X-E31-Seed: 1\r\n"):
        raise RuntimeError("seed_regex_false_positive")
    sample = b"17 (UID 9 BODY[HEADER.FIELDS (X-E31-SEED)] {16}\r\nX-E31-Seed: 1\r\n\r\n)"
    if not header_is_seed(sample):
        raise RuntimeError("seed_regex_fetch")
    flags_blob = (
        b"1 (FLAGS (\\Seen \\Flagged) BODY[HEADER.FIELDS (X-E31-ROLE)] {24}\r\n"
        b"X-E31-Role: flagged\r\n\r\n)"
    )
    if parse_flags(flags_blob) != {"\\Seen", "\\Flagged"}:
        raise RuntimeError("flag_parse")
    if header_value(flags_blob, "X-E31-Role") != "flagged":
        raise RuntimeError("role_parse")
    png = make_png()
    if not png_ok(png):
        raise RuntimeError("png_invalid")
    marker = "E31-TEST01"
    for scenario, expect in (("design-request", 1), ("mixed-inbox", 5)):
        seeds = build_seeds(scenario, marker, png)
        if len(seeds) != expect or len(seeds) > MAX_BATCH:
            raise RuntimeError("seed_count_" + scenario)
        if scenario == "mixed-inbox":
            roles = [item.role for item in seeds]
            if roles.count("unread") != 2 or roles.count("attachment") != 1:
                raise RuntimeError("mixed_roles")
            if roles.count("flagged") != 1 or roles.count("distractor") != 1:
                raise RuntimeError("mixed_roles")
        for seed in seeds:
            raw = build_raw(seed, marker)
            item = message_to_record(raw)
            if marker not in item["主题"] or marker not in item["正文"]:
                raise RuntimeError("marker_not_in_text")
            if item["收件人"] != [TO_ADDR]:
                raise RuntimeError("recipient_unexpected")
            if seed.filename and not any(marker in name for name in item["附件名"]):
                raise RuntimeError("filename_missing")
            if seed.role == "design" and DESIGN_SENTENCE not in item["正文"]:
                raise RuntimeError("design_sentence_missing")
            encoded = json.dumps(item, ensure_ascii=False)
            if set(json.loads(encoded)) != {"主题", "收件人", "正文", "附件名"}:
                raise RuntimeError("json_shape")
    html_only = (
        b"Subject: E31\r\nMIME-Version: 1.0\r\n"
        b"Content-Type: multipart/alternative; boundary=b\r\n\r\n"
        b"--b\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
        b"\r\n--b\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
        b"<html><body>E31-DRAFT-BODY</body></html>\r\n--b--\r\n"
    )
    if message_to_record(html_only)["正文"].strip() != "E31-DRAFT-BODY":
        raise RuntimeError("html_body")
    if is_e31_text("普通来信") or not is_e31_text("E31落款探针"):
        raise RuntimeError("e31_marker")
    dumped = records_to_dump(
        [{"主题": "E31落款探针", "收件人": ["probe@example.com"], "正文": "— E31", "附件名": []}]
    )
    if "SUBJECT=E31落款探针\n" not in dumped or "BODY=— E31\n" not in dumped:
        raise RuntimeError("dump_shape")


def parse_list_line(line: bytes):
    text = line.decode("utf-8", "replace").strip()
    match = _LIST_RE.match(text)
    if not match:
        return "", ""
    name = match.group("name").strip()
    if len(name) >= 2 and name.startswith('"') and name.endswith('"'):
        name = name[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return match.group("flags"), name


def parse_uids(data) -> list:
    if not data or data[0] is None:
        return []
    raw = data[0]
    if isinstance(raw, bytes):
        raw = raw.decode("ascii", "replace")
    return [item for item in str(raw).split() if item.isdigit()]


def join_uids(uids) -> str:
    clean = []
    for uid in uids:
        text = uid.decode("ascii") if isinstance(uid, bytes) else str(uid)
        if not re.fullmatch(r"\d+", text):
            raise RuntimeError("bad_uid")
        clean.append(text)
    return ",".join(clean)


def chunked(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def extract_message_bytes(fetch_data) -> bytes:
    blobs = []

    def walk(item):
        if isinstance(item, (bytes, bytearray)):
            blobs.append(bytes(item))
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)

    walk(fetch_data)
    candidates = [
        item
        for item in blobs
        if b"\n" in item and (b"Subject:" in item or b"From:" in item or b"MIME-Version:" in item)
    ]
    if candidates:
        return max(candidates, key=len)
    if blobs:
        return max(blobs, key=len)
    return b""


def _exists_count(data) -> int:
    if not data or data[0] is None:
        raise ImapOpError("count_missing")
    raw = data[0]
    if isinstance(raw, bytes):
        raw = raw.decode("ascii", "replace")
    return int(str(raw).split()[0])


def flags_arg(role: str):
    seen, flagged = ROLE_WANTS[role]
    parts = []
    if seen:
        parts.append("\\Seen")
    if flagged:
        parts.append("\\Flagged")
    if not parts:
        return None
    return "(" + " ".join(parts) + ")"


class Imap(object):
    def __init__(self, user: str, password: str):
        self._secrets = [item for item in (user, password) if item]
        self._user = user
        self._password = password
        self.imap = None
        self.caps = []
        self.capset = set()
        self.append_limit = "unspecified"
        self.append_codes = set()
        self.appenduid_seen = 0
        self.append_error = ""
        self.append_fail = 0
        self.append_flag_rejected = 0
        self.append_stuck = 0
        self.delete_blocked = 0
        self._open_and_login()

    def _scrub(self, obj) -> str:
        return scrub_text(obj, self._secrets)

    def _wipe_imap(self, imap):
        if imap is None:
            return
        try:
            imap.debug = 0
        except Exception:
            pass
        log = getattr(imap, "_cmd_log", None)
        if isinstance(log, list):
            for index in range(len(log)):
                log[index] = None
        for attr in ("password", "user"):
            if hasattr(imap, attr):
                try:
                    setattr(imap, attr, "")
                except Exception:
                    pass

    def _open_and_login(self):
        IMAP4.debug = 0
        self.imap = imaplib.IMAP4_SSL(HOST, PORT, timeout=90)
        self.imap.debug = 0
        if getattr(self.imap, "utf8_enabled", False):
            self.imap._mode_ascii()
        _pause()
        try:
            result = self.imap.login(self._user, self._password)
        except Exception as exc:
            self._wipe_imap(self.imap)
            _pause()
            try:
                self.imap.shutdown()
            except Exception:
                pass
            self.imap = None
            raise ImapOpError("login_failed " + self._scrub(exc)) from None
        self._wipe_imap(self.imap)
        _pause()
        if not result or result[0] != "OK":
            raise ImapOpError("login_failed")
        self._load_caps()

    def _load_caps(self):
        greeting = []
        for item in getattr(self.imap, "capabilities", ()) or ():
            if isinstance(item, bytes):
                item = item.decode("ascii", "replace")
            greeting.append(str(item))
        typ, data = self.try_cmd("capability", lambda: self.imap.capability(), retry=False)
        extra = _blob(data).decode("ascii", "replace").split() if typ == "OK" else []
        self.caps = greeting + extra
        self.capset = {item.upper() for item in self.caps}
        self.append_limit = "unspecified"
        for item in self.caps:
            if item.upper().startswith("APPENDLIMIT"):
                self.append_limit = item.split("=", 1)[1] if "=" in item else "present"

    def try_cmd(self, what, fn, retry=True):
        if self.imap is None:
            return "ERR", b""
        try:
            result = fn()
        except imaplib.IMAP4.abort as exc:
            self._wipe_imap(self.imap)
            _pause()
            if retry:
                try:
                    self._reconnect()
                except ImapOpError as err:
                    return "ERR", self._scrub(err).encode("utf-8", "replace")
                return self.try_cmd(what, fn, retry=False)
            return "ERR", self._scrub(exc).encode("utf-8", "replace")
        except (imaplib.IMAP4.error, OSError, TimeoutError) as exc:
            self._wipe_imap(self.imap)
            _pause()
            return "ERR", self._scrub(exc).encode("utf-8", "replace")
        self._wipe_imap(self.imap)
        _pause()
        if not isinstance(result, tuple) or len(result) < 2:
            return "ERR", b"bad response"
        typ = result[0]
        if isinstance(typ, bytes):
            typ = typ.decode("ascii", "replace")
        return str(typ).upper(), result[1]

    def _reconnect(self):
        old = self.imap
        self._wipe_imap(old)
        try:
            if old is not None:
                old.shutdown()
        except Exception:
            pass
        self.imap = None
        self._open_and_login()

    def logout(self):
        imap = self.imap
        self.imap = None
        if imap is None:
            return
        try:
            if getattr(imap, "state", "") != "LOGOUT":
                try:
                    imap.logout()
                except Exception:
                    try:
                        imap.shutdown()
                    except Exception:
                        pass
        finally:
            self._wipe_imap(imap)
            _pause()

    def _selected(self) -> bool:
        return self.imap is not None and getattr(self.imap, "state", "") == "SELECTED"

    def _leave(self):
        if not self._selected():
            return
        if getattr(self.imap, "is_readonly", False):
            self.try_cmd("close", lambda: self.imap.close(), retry=False)
            return
        if "UNSELECT" in self.capset:
            self.try_cmd("unselect", lambda: self.imap.unselect(), retry=False)

    def count(self, mailbox: str) -> int:
        typ, data = self.try_cmd(
            "status",
            lambda: self.imap.status(mailbox, "(MESSAGES)"),
        )
        if typ == "OK":
            match = re.search(rb"MESSAGES\s+(\d+)", _blob(data))
            if match:
                return int(match.group(1))
        typ, data = self.try_cmd(
            "examine",
            lambda: self.imap.select(mailbox, readonly=True),
        )
        if typ != "OK":
            raise ImapOpError("count_failed " + self._scrub(_short(data)))
        number = _exists_count(data)
        self._leave()
        return number

    def find_drafts(self):
        typ, data = self.try_cmd("list", lambda: self.imap.list())
        found = None
        if typ == "OK":
            for raw in data or []:
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                flags, name = parse_list_line(bytes(raw))
                if not name:
                    continue
                if "\\drafts" in flags.lower():
                    return name
                compact = name.lower().replace("\\", "/")
                if compact in {"drafts", "inbox/drafts", "inbox.drafts"}:
                    found = name
        if found:
            return found
        for guess in ("Drafts", "INBOX.Drafts", "INBOX/Drafts"):
            typ, _data = self.try_cmd(
                "examine",
                lambda guess=guess: self.imap.select(guess, readonly=True),
            )
            if typ == "OK":
                self._leave()
                return guess
        return None

    def find_sent(self):
        typ, data = self.try_cmd("list", lambda: self.imap.list())
        found = None
        if typ == "OK":
            for raw in data or []:
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                flags, name = parse_list_line(bytes(raw))
                if not name or name.upper() == "INBOX":
                    continue
                if "\\sent" in flags.lower():
                    return name
                compact = name.lower().replace("\\", "/")
                if compact in {"sent", "inbox/sent", "inbox.sent", "sent messages", "已发送"}:
                    found = name
        if found:
            return found
        for guess in ("Sent", "INBOX.Sent", "INBOX/Sent", "Sent Messages"):
            typ, _data = self.try_cmd(
                "examine",
                lambda guess=guess: self.imap.select(guess, readonly=True),
            )
            if typ == "OK":
                self._leave()
                return guess
        return None

    def _expunge(self, mailbox: str, confirmed: list, preexisting: set, deleted_known: bool) -> dict:
        result = {"deleted": 0, "blocked": 0}
        if not confirmed:
            return result
        # UID EXPUNGE 只删列出的 UID。没有这项能力时，CLOSE 会清掉邮箱里所有 \Deleted。
        precise = "UIDPLUS" in self.capset and "UNSELECT" in self.capset
        extra = preexisting - set(confirmed)
        if not precise and (extra or not deleted_known):
            result["blocked"] = 1
            self.delete_blocked = 1
            return result
        typ, data = self.try_cmd(
            "select",
            lambda: self.imap.select(mailbox, readonly=False),
        )
        if typ != "OK":
            self._leave()
            raise ImapOpError("select_rw_failed " + self._scrub(_short(data)))
        try:
            for group in chunked(confirmed, MAX_BATCH):
                uidset = join_uids(group)
                typ, data = self.try_cmd(
                    "store",
                    lambda uidset=uidset: self.imap.uid("STORE", uidset, "+FLAGS", "(\\Deleted)"),
                    retry=False,
                )
                if typ != "OK":
                    raise ImapOpError("store_failed " + self._scrub(_short(data)))
            if precise:
                for group in chunked(confirmed, MAX_BATCH):
                    uidset = join_uids(group)
                    typ, data = self.try_cmd(
                        "uid_expunge",
                        lambda uidset=uidset: self.imap.uid("EXPUNGE", uidset),
                        retry=False,
                    )
                    if typ != "OK":
                        raise ImapOpError("expunge_failed " + self._scrub(_short(data)))
                self.try_cmd("unselect", lambda: self.imap.unselect(), retry=False)
            else:
                typ, data = self.try_cmd("close", lambda: self.imap.close(), retry=False)
                if typ != "OK":
                    raise ImapOpError("close_failed " + self._scrub(_short(data)))
        except Exception:
            self._leave()
            raise
        result["deleted"] = len(confirmed)
        return result

    def _select_uids(self, mailbox: str, exists: int):
        """只读打开邮箱，返回 (uids, preexisting_deleted, deleted_known)。调用方不再持有选择。"""
        empty = [], set(), False
        if exists <= 0:
            return empty
        typ, data = self.try_cmd(
            "examine",
            lambda: self.imap.select(mailbox, readonly=True),
        )
        if typ != "OK":
            raise ImapOpError("select_failed " + self._scrub(_short(data)))
        try:
            typ, data = self.try_cmd("search", lambda: self.imap.uid("SEARCH", "ALL"))
            if typ != "OK":
                raise ImapOpError("search_failed " + self._scrub(_short(data)))
            uids = sorted(set(parse_uids(data)), key=int)
            if len(uids) > SCAN_LIMIT:
                uids = uids[-SCAN_LIMIT:]
            typ, data = self.try_cmd("search_deleted", lambda: self.imap.uid("SEARCH", "DELETED"))
            deleted_known = typ == "OK"
            preexisting = set(parse_uids(data) if deleted_known else [])
            return uids, preexisting, deleted_known
        finally:
            self._leave()

    def delete_all(self, mailbox: str, exists: int) -> dict:
        result = {"deleted": 0, "scanned": 0, "matched": 0, "blocked": 0, "capped": 0}
        if exists <= 0:
            return result
        uids, preexisting, deleted_known = self._select_uids(mailbox, exists)
        result["scanned"] = len(uids)
        result["capped"] = 1 if exists > SCAN_LIMIT else 0
        result["matched"] = len(uids)
        expunged = self._expunge(mailbox, uids, preexisting, deleted_known)
        result["deleted"] = expunged["deleted"]
        result["blocked"] = expunged["blocked"]
        return result

    def delete_e31(self, mailbox: str, exists: int) -> dict:
        result = {"deleted": 0, "scanned": 0, "matched": 0, "blocked": 0, "capped": 0}
        if exists <= 0:
            return result
        uids, preexisting, deleted_known = self._select_uids(mailbox, exists)
        result["scanned"] = len(uids)
        result["capped"] = 1 if exists > SCAN_LIMIT else 0
        confirmed = []
        if uids:
            typ, data = self.try_cmd(
                "examine",
                lambda: self.imap.select(mailbox, readonly=True),
            )
            if typ != "OK":
                raise ImapOpError("select_failed " + self._scrub(_short(data)))
            try:
                for uid in uids:
                    typ, data = self.try_cmd(
                        "fetch",
                        lambda uid=uid: self.imap.uid("FETCH", uid, "(BODY.PEEK[])"),
                        retry=False,
                    )
                    if typ == "OK" and is_e31_text(_blob(data).decode("utf-8", "replace")):
                        confirmed.append(uid)
            finally:
                self._leave()
        result["matched"] = len(confirmed)
        expunged = self._expunge(mailbox, confirmed, preexisting, deleted_known)
        result["deleted"] = expunged["deleted"]
        result["blocked"] = expunged["blocked"]
        return result

    def clear_agent_residue(self) -> dict:
        """清空草稿箱，并删除已发送里带 E31 的信。不碰收件箱。"""
        summary = {
            "drafts_missing": 0,
            "sent_missing": 0,
            "drafts_deleted": 0,
            "sent_deleted": 0,
            "drafts_after": -1,
            "sent_after": -1,
        }
        drafts_name = self.find_drafts()
        if not drafts_name:
            summary["drafts_missing"] = 1
        else:
            before = self.count(drafts_name)
            info = self.delete_all(drafts_name, before)
            summary["drafts_deleted"] = info["deleted"]
            summary["drafts_blocked"] = info["blocked"]
            summary["drafts_after"] = self.count(drafts_name)
        sent_name = self.find_sent()
        if not sent_name:
            summary["sent_missing"] = 1
        else:
            before = self.count(sent_name)
            info = self.delete_e31(sent_name, before)
            summary["sent_deleted"] = info["deleted"]
            summary["sent_blocked"] = info["blocked"]
            summary["sent_after"] = self.count(sent_name)
        return summary

    def _fetch_first_ok(self, uid: str, specs):
        last_typ, last_data = "ERR", b""
        for spec in specs:
            typ, data = self.try_cmd(
                "fetch",
                lambda uid=uid, spec=spec: self.imap.uid("FETCH", uid, spec),
                retry=False,
            )
            last_typ, last_data = typ, data
            if typ == "OK":
                return spec, _blob(data)
        raise ImapOpError("fetch_failed " + last_typ + " " + self._scrub(_short(last_data)))

    def delete_seed(self, mailbox: str, exists: int) -> dict:
        result = {"deleted": 0, "scanned": 0, "matched": 0, "blocked": 0}
        if exists <= 0:
            return result
        typ, data = self.try_cmd(
            "examine",
            lambda: self.imap.select(mailbox, readonly=True),
        )
        if typ != "OK":
            raise ImapOpError("select_failed " + self._scrub(_short(data)))
        try:
            if exists <= SCAN_LIMIT:
                typ, data = self.try_cmd("search", lambda: self.imap.uid("SEARCH", "ALL"))
            else:
                typ, data = self.try_cmd(
                    "search",
                    lambda: self.imap.uid("SEARCH", "HEADER", "X-E31-Seed", "1"),
                )
            if typ != "OK":
                raise ImapOpError("search_failed " + self._scrub(_short(data)))
            uids = sorted(set(parse_uids(data)), key=int)
            if len(uids) > SCAN_LIMIT:
                uids = uids[-SCAN_LIMIT:]
                result["capped"] = 1
            else:
                result["capped"] = 0
            result["scanned"] = len(uids)
            typ, data = self.try_cmd("search_deleted", lambda: self.imap.uid("SEARCH", "DELETED"))
            deleted_known = typ == "OK"
            preexisting = set(parse_uids(data) if deleted_known else [])
            confirmed = []
            for uid in uids:
                _spec, blob = self._fetch_first_ok(uid, HEADER_SPECS)
                if header_is_seed(blob):
                    confirmed.append(uid)
                    if len(confirmed) >= MAX_BATCH:
                        break
            result["matched"] = len(confirmed)
            extra = preexisting - set(confirmed)
        finally:
            self._leave()
        if not confirmed:
            return result
        expunged = self._expunge(mailbox, confirmed, preexisting, deleted_known)
        result["deleted"] = expunged["deleted"]
        result["blocked"] = expunged["blocked"]
        return result

    def _note_append(self, typ, data):
        text = self._scrub(_short(data))
        for code in re.findall(r"\[([A-Z][A-Z0-9-]*)", text):
            self.append_codes.add(code)
        if b"APPENDUID" in _blob(data).upper():
            self.appenduid_seen += 1
        if typ != "OK" and not self.append_error:
            self.append_error = (str(typ) + " " + text).strip()

    def _append_one(self, mailbox: str, raw: bytes, flags, current: int):
        head = raw.split(b"\r\n\r\n", 1)[0]
        for secret in self._secrets:
            if secret and len(secret) >= 4 and secret.encode("utf-8", "replace") in head:
                raise ImapOpError("refusing_append")
        if b"X-E31-Seed: 1" not in head:
            raise ImapOpError("refusing_append")

        def _do(flag_value):
            return self.imap.append(mailbox, flag_value, time.time(), raw)

        typ, data = self.try_cmd("append", lambda: _do(flags), retry=False)
        self._note_append(typ, data)
        after = self.count(mailbox)
        if after == current + 1:
            return "ok", after
        if typ == "OK":
            after = self.count(mailbox)
            if after == current + 1:
                return "ok", after
            self.append_stuck += 1
            return "fail", after
        if flags and after == current:
            typ2, data2 = self.try_cmd("append", lambda: _do(None), retry=False)
            self._note_append(typ2, data2)
            after2 = self.count(mailbox)
            if after2 == current + 1:
                self.append_flag_rejected += 1
                return "ok_noflags", after2
            if not self.append_error:
                self.append_error = (str(typ2) + " " + self._scrub(_short(data2))).strip()
            return "fail", after2
        return "fail", after

    def append_many(self, mailbox: str, payloads) -> int:
        if len(payloads) > MAX_BATCH:
            raise ImapOpError("too_many")
        current = self.count(mailbox)
        ok = 0
        for raw, flags in payloads:
            status, current = self._append_one(mailbox, raw, flags, current)
            if status.startswith("ok"):
                ok += 1
            else:
                self.append_fail += 1
        return ok

    def fix_flags(self, mailbox: str, marker: str) -> dict:
        stats = {
            "seed_found": 0,
            "flagged": 0,
            "unseen": 0,
            "seen": 0,
            "attachments": 0,
            "attachment_check": "none",
            "flag_fix_fail": 0,
            "scan_capped": 0,
        }
        typ, data = self.try_cmd("select", lambda: self.imap.select(mailbox, readonly=False))
        if typ != "OK":
            raise ImapOpError("select_failed " + self._scrub(_short(data)))
        try:
            typ, data = self.try_cmd(
                "search",
                lambda: self.imap.uid("SEARCH", "HEADER", "X-E31-Marker", marker),
            )
            uids = parse_uids(data) if typ == "OK" else []
            if not uids:
                typ, data = self.try_cmd("search", lambda: self.imap.uid("SEARCH", "ALL"))
                if typ != "OK":
                    raise ImapOpError("search_failed " + self._scrub(_short(data)))
                uids = parse_uids(data)
            uids = sorted(set(uids), key=int)
            if len(uids) > SCAN_LIMIT:
                uids = uids[-SCAN_LIMIT:]
                stats["scan_capped"] = 1
            for uid in uids:
                try:
                    spec, blob = self._fetch_first_ok(uid, FLAG_SPECS)
                except ImapOpError:
                    stats["flag_fix_fail"] += 1
                    continue
                if header_value(blob, "X-E31-Marker") != marker:
                    continue
                role = header_value(blob, "X-E31-Role")
                if role not in ROLE_WANTS:
                    continue
                stats["seed_found"] += 1
                if b"BODYSTRUCTURE" in blob or "BODYSTRUCTURE" in spec:
                    has_attach = b'"PNG"' in blob or b'"png"' in blob
                    stats["attachment_check"] = "bodystructure"
                else:
                    has_attach = header_value(blob, "X-E31-Attach") == "1"
                    if stats["attachment_check"] != "bodystructure":
                        stats["attachment_check"] = "header"
                if has_attach:
                    stats["attachments"] += 1
                current = parse_flags(blob)
                want_seen, want_flagged = ROLE_WANTS[role]
                add = []
                remove = []
                if want_seen and "\\Seen" not in current:
                    add.append("\\Seen")
                if not want_seen and "\\Seen" in current:
                    remove.append("\\Seen")
                if want_flagged and "\\Flagged" not in current:
                    add.append("\\Flagged")
                if not want_flagged and "\\Flagged" in current:
                    remove.append("\\Flagged")
                final = set(current)
                if add or remove:
                    if add:
                        spec_flags = "(" + " ".join(add) + ")"
                        typ, data = self.try_cmd(
                            "store",
                            lambda uid=uid, spec_flags=spec_flags: self.imap.uid(
                                "STORE", uid, "+FLAGS", spec_flags
                            ),
                            retry=False,
                        )
                        if typ != "OK":
                            stats["flag_fix_fail"] += 1
                        else:
                            final.update(add)
                    if remove:
                        spec_flags = "(" + " ".join(remove) + ")"
                        typ, data = self.try_cmd(
                            "store",
                            lambda uid=uid, spec_flags=spec_flags: self.imap.uid(
                                "STORE", uid, "-FLAGS", spec_flags
                            ),
                            retry=False,
                        )
                        if typ != "OK":
                            stats["flag_fix_fail"] += 1
                        else:
                            for flag in remove:
                                final.discard(flag)
                if "\\Seen" in final:
                    stats["seen"] += 1
                else:
                    stats["unseen"] += 1
                if "\\Flagged" in final:
                    stats["flagged"] += 1
        finally:
            self._leave()
        return stats

    def fetch_draft_records(self) -> list:
        name = self.find_drafts()
        if not name:
            return []
        total = self.count(name)
        if total <= 0:
            return []
        typ, data = self.try_cmd("examine", lambda: self.imap.select(name, readonly=True))
        if typ != "OK":
            return []
        records = []
        try:
            typ, data = self.try_cmd("search", lambda: self.imap.uid("SEARCH", "ALL"))
            if typ != "OK":
                return records
            for uid in parse_uids(data):
                typ, data = self.try_cmd(
                    "fetch",
                    lambda uid=uid: self.imap.uid("FETCH", uid, "(BODY.PEEK[])"),
                    retry=False,
                )
                if typ != "OK":
                    continue
                raw = extract_message_bytes(data)
                if raw:
                    records.append(message_to_record(raw))
        finally:
            self._leave()
        return records


def is_e31_text(text: str) -> bool:
    return "E31" in (text or "")


def records_to_dump(records) -> str:
    """把 IMAP 记录收成评分脚本认识的 SUBJECT/BODY/TO/ATTACH 转储。"""
    chunks = []
    for rec in records or []:
        subject = str(rec.get("主题") or "").replace("\r", " ").replace("\n", " ")
        body = str(rec.get("正文") or "").replace("\r", " ").replace("\n", " ")
        raw_to = rec.get("收件人") or []
        if isinstance(raw_to, list):
            to_text = ", ".join(str(item) for item in raw_to)
        else:
            to_text = str(raw_to)
        to_text = to_text.replace("\r", " ").replace("\n", " ")
        raw_names = rec.get("附件名") or []
        if isinstance(raw_names, list):
            attach = ", ".join(str(item) for item in raw_names)
        else:
            attach = str(raw_names)
        attach = attach.replace("\r", " ").replace("\n", " ")
        chunks.append(
            "SUBJECT=%s\nBODY=%s\nTO=%s\nATTACH=%s\n----\n" % (subject, body, to_text, attach)
        )
    return "".join(chunks)


def read_drafts(user, password):
    """读取 Drafts，返回 JSON 字符串。每项含主题、收件人、正文、附件名。"""
    box = Imap(user, password)
    try:
        records = box.fetch_draft_records()
    finally:
        box.logout()
    return json.dumps(records, ensure_ascii=False)


def run(args) -> int:
    self_check()
    actions = bool(args.reset or args.scenario or args.read_drafts or args.clear_residue)
    if args.self_check and not actions:
        print("self_check=ok", flush=True)
        return 0
    if not args.creds:
        print("error=creds_required", file=sys.stderr)
        return 2
    if args.read_drafts and (args.reset or args.scenario):
        print("error=read_drafts_is_separate", file=sys.stderr)
        return 2
    do_reset = bool(args.reset or args.scenario == "empty")
    do_seed = args.scenario in ("design-request", "mixed-inbox")
    if not do_reset and not do_seed and not args.read_drafts and not args.clear_residue:
        print("error=no_action", file=sys.stderr)
        return 2
    if do_seed and not args.marker_file:
        print("error=marker_file_required", file=sys.stderr)
        return 2

    user, password = read_creds(args.creds)
    secrets = [user, password]
    marker = ""
    payloads = []
    png_size = 0
    if do_seed:
        marker = new_marker()
        if not re.fullmatch(r"E31-[A-F0-9]{6}", marker):
            raise ImapOpError("bad_marker")
        png = make_png()
        if not png_ok(png):
            raise ImapOpError("png_invalid")
        png_size = len(png)
        seeds = build_seeds(args.scenario, marker, png)
        if not seeds or len(seeds) > MAX_BATCH:
            raise ImapOpError("bad_scenario_size")
        for seed in seeds:
            payloads.append((build_raw(seed, marker), flags_arg(seed.role)))
        write_marker(args.marker_file, marker, args.creds)

    if args.read_drafts and not do_reset and not do_seed:
        text = read_drafts(user, password)
        if args.count_only:
            items = json.loads(text)
            shape_ok = all(
                isinstance(item, dict) and {"主题", "收件人", "正文", "附件名"} <= set(item)
                for item in items
            )
            emit("drafts_items", len(items), secrets)
            emit("drafts_shape", "ok" if shape_ok else "bad", secrets)
        else:
            sys.stdout.write(text)
            sys.stdout.write("\n")
        return 0

    box = None
    code = 1
    try:
        box = Imap(user, password)
        if args.clear_residue and not do_reset and not do_seed:
            action = "clear-residue"
        elif args.scenario == "empty":
            action = "empty"
        elif do_reset and do_seed:
            action = "reset+" + args.scenario
        elif do_seed:
            action = args.scenario
        else:
            action = "reset"
        inbox_before = box.count("INBOX")
        deleted_inbox = 0
        deleted_drafts = 0
        inbox_scanned = 0
        drafts_scanned = 0
        drafts_missing = 0
        drafts_before = -1
        drafts_after = -1
        scan_capped = 0
        residue = None
        if do_reset:
            inbox_info = box.delete_seed("INBOX", inbox_before)
            deleted_inbox = inbox_info["deleted"]
            inbox_scanned = inbox_info["scanned"]
            scan_capped = max(scan_capped, inbox_info.get("capped", 0))
            drafts_name = box.find_drafts()
            if not drafts_name:
                drafts_missing = 1
            else:
                drafts_before = box.count(drafts_name)
                drafts_info = box.delete_seed(drafts_name, drafts_before)
                deleted_drafts = drafts_info["deleted"]
                drafts_scanned = drafts_info["scanned"]
                scan_capped = max(scan_capped, drafts_info.get("capped", 0))
                drafts_after = box.count(drafts_name)
        if do_reset or args.clear_residue:
            residue = box.clear_agent_residue()
            if residue.get("drafts_blocked") or residue.get("sent_blocked"):
                box.delete_blocked = 1
        appended = 0
        stats = {}
        if do_seed:
            appended = box.append_many("INBOX", payloads)
            stats = box.fix_flags("INBOX", marker)
        inbox_after = box.count("INBOX")
        expected = inbox_before - deleted_inbox + appended
        emit("action", action, secrets)
        emit("server", HOST, secrets)
        emit("port", PORT, secrets)
        emit("pause_seconds", int(PAUSE_SECONDS), secrets)
        emit("max_batch", MAX_BATCH, secrets)
        emit("appendlimit", box.append_limit, secrets)
        emit("uidplus", 1 if "UIDPLUS" in box.capset else 0, secrets)
        emit("unselect", 1 if "UNSELECT" in box.capset else 0, secrets)
        if marker:
            emit("marker", marker, secrets)
            emit("png_bytes", png_size, secrets)
        emit("inbox_before", inbox_before, secrets)
        emit("deleted_inbox", deleted_inbox, secrets)
        emit("deleted_drafts", deleted_drafts, secrets)
        if residue is not None:
            emit("residue_drafts_deleted", residue.get("drafts_deleted", 0), secrets)
            emit("residue_sent_deleted", residue.get("sent_deleted", 0), secrets)
            emit("residue_drafts_after", residue.get("drafts_after", -1), secrets)
            emit("residue_sent_after", residue.get("sent_after", -1), secrets)
            emit("residue_drafts_missing", residue.get("drafts_missing", 0), secrets)
            emit("residue_sent_missing", residue.get("sent_missing", 0), secrets)
        emit("delete_blocked", box.delete_blocked, secrets)
        emit("appended", appended, secrets)
        emit("append_fail", box.append_fail, secrets)
        emit("append_flag_rejected", box.append_flag_rejected, secrets)
        emit("append_stuck", box.append_stuck, secrets)
        emit("appenduid_seen", box.appenduid_seen, secrets)
        emit("append_codes", ",".join(sorted(box.append_codes)) or "none", secrets)
        if box.append_error:
            emit("append_error", box.append_error, secrets)
        emit("inbox_expected", expected, secrets)
        emit("inbox_after", inbox_after, secrets)
        if do_reset:
            emit("drafts_missing", drafts_missing, secrets)
            emit("drafts_before", drafts_before, secrets)
            emit("drafts_after", drafts_after, secrets)
            emit("inbox_scanned", inbox_scanned, secrets)
            emit("inbox_matched", inbox_info["matched"], secrets)
            emit("drafts_scanned", drafts_scanned, secrets)
            emit("drafts_matched", 0 if drafts_missing else drafts_info["matched"], secrets)
            emit("scan_capped", scan_capped, secrets)
        if stats:
            emit("seed_found", stats["seed_found"], secrets)
            emit("flagged", stats["flagged"], secrets)
            emit("unseen", stats["unseen"], secrets)
            emit("seen", stats["seen"], secrets)
            emit("attachments", stats["attachments"], secrets)
            emit("attachment_check", stats["attachment_check"], secrets)
            emit("flag_fix_fail", stats["flag_fix_fail"], secrets)
        code = 0
        if do_seed and appended != len(payloads):
            code = 4
        elif box.delete_blocked:
            code = 6
        elif inbox_after != expected:
            code = 3
        elif residue is not None and residue.get("drafts_after") not in (0, -1):
            code = 7
        elif args.scenario == "mixed-inbox" and (
            stats.get("seed_found") != 5
            or stats.get("flagged") != 1
            or stats.get("unseen") != 2
            or stats.get("attachments") != 1
        ):
            code = 5
    finally:
        if box is not None:
            box.logout()
    return code


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="用 IMAP APPEND 往 mail.com 测试邮箱灌种子邮件（不发信）"
    )
    parser.add_argument("--creds", help="私密账号文件，只读其中的账号与密码两行")
    parser.add_argument("--reset", action="store_true", help="删除带 X-E31-Seed: 1 的邮件，并清草稿箱和已发送里的 E31")
    parser.add_argument(
        "--clear-residue",
        action="store_true",
        help="只清空 Drafts，并删除 Sent 里含 E31 的邮件，不改收件箱",
    )
    parser.add_argument(
        "--scenario",
        choices=("design-request", "mixed-inbox", "empty"),
        help="灌入场景；empty 只做 reset",
    )
    parser.add_argument("--marker-file", help="写入本次随机标记 E31-XXXXXX")
    parser.add_argument("--read-drafts", action="store_true", help="调用 read_drafts")
    parser.add_argument(
        "--count-only",
        action="store_true",
        help="--read-drafts 时只打印封数，不打印正文",
    )
    parser.add_argument("--self-check", action="store_true", help="只做本地自检，不连服务器")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass
    args = parse_args(sys.argv[1:] if argv is None else argv)
    secrets = []
    try:
        if args.creds and (args.reset or args.scenario or args.read_drafts):
            pass
        return run(args)
    except ImapOpError as exc:
        if args.creds:
            try:
                user, password = read_creds(args.creds)
                secrets = [user, password]
            except Exception:
                secrets = []
        print("error=" + scrub_text(exc, secrets), file=sys.stderr)
        return 1
    except Exception as exc:
        if args.creds:
            try:
                user, password = read_creds(args.creds)
                secrets = [user, password]
            except Exception:
                secrets = []
        print("error=" + scrub_text(exc, secrets), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
