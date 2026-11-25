import os, sys, subprocess, time
from PIL import Image, ImageDraw
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

CLEAR_PASSES = 2
CLEAR_SYNC_SECONDS = 12
CLEAR_MAIL_SCRIPT = 'tell application "Mail"\n    set deletedCount to 0\n    set draftNames to {"Drafts", "草稿", "草稿箱"}\n    set sentNames to {"Sent", "Sent Messages", "Sent Items", "已发送", "已发送邮件", "发件箱"}\n    set seenText to "|"\n    set candidates to {}\n    repeat with acc in accounts\n        repeat with n in draftNames\n            try\n                set end of candidates to mailbox (n as string) of acc\n            end try\n        end repeat\n        repeat with n in sentNames\n            try\n                set end of candidates to mailbox (n as string) of acc\n            end try\n        end repeat\n        try\n            repeat with mb in mailboxes of acc\n                set boxName to name of mb as string\n                set takeIt to false\n                if draftNames contains boxName then set takeIt to true\n                if sentNames contains boxName then set takeIt to true\n                if boxName contains "Draft" or boxName contains "draft" or boxName contains "草稿" then set takeIt to true\n                if boxName begins with "Sent" or boxName begins with "sent" then set takeIt to true\n                if boxName contains "已发送" or boxName contains "发件箱" then set takeIt to true\n                if takeIt then set end of candidates to mb\n            end repeat\n        end try\n    end repeat\n    repeat with n in draftNames\n        try\n            set end of candidates to mailbox (n as string)\n        end try\n    end repeat\n    repeat with n in sentNames\n        try\n            set end of candidates to mailbox (n as string)\n        end try\n    end repeat\n    set seq to 0\n    repeat with mb in candidates\n        set seq to seq + 1\n        set marker to ""\n        try\n            set marker to (id of mb) as string\n        end try\n        if marker is "" then\n            try\n                set marker to "box" & seq & "-" & (name of mb as string)\n            end try\n        end if\n        if marker is not "" then\n            if seenText contains ("|" & marker & "|") then\n            else\n                set seenText to seenText & marker & "|"\n                set ids to {}\n                try\n                    set hits to messages of mb whose subject contains "E31"\n                    repeat with m in hits\n                        try\n                            set end of ids to (id of m)\n                        end try\n                    end repeat\n                on error\n                    try\n                        repeat with m in messages of mb\n                            try\n                                if (subject of m as string) contains "E31" then set end of ids to (id of m)\n                            end try\n                        end repeat\n                    end try\n                end try\n                repeat with mid in ids\n                    try\n                        set midVal to contents of mid\n                        delete (first message of mb whose id is midVal)\n                        set deletedCount to deletedCount + 1\n                    end try\n                end repeat\n            end if\n        end if\n    end repeat\n    delay 8\n    return deletedCount as string\nend tell\n'


def run_osascript(script, timeout=60):
    try:
        proc = subprocess.run(
            ["osascript", "-"],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return None, type(exc).__name__
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "osascript_failed").strip()
        return None, err[:300]
    return proc.stdout, None


def clear_e31_mail():
    total = 0
    for attempt in range(1, CLEAR_PASSES + 1):
        text, err = run_osascript(CLEAR_MAIL_SCRIPT, timeout=60)
        deleted = None
        if err:
            sys.stderr.write("e31-mail-clear attempt=%s error=%s\n" % (attempt, err))
        else:
            lines = (text or "").strip().splitlines()
            raw = lines[-1].strip() if lines else ""
            try:
                deleted = int(raw)
            except ValueError:
                sys.stderr.write("e31-mail-clear attempt=%s bad=%s\n" % (attempt, raw[:80]))
            else:
                total += deleted
        shown = "error" if deleted is None else str(deleted)
        sys.stdout.write("e31-mail-clear attempt=%s deleted=%s\n" % (attempt, shown))
        sys.stdout.flush()
        time.sleep(CLEAR_SYNC_SECONDS)
    sys.stdout.write("e31-mail-clear total=%s\n" % total)
    sys.stdout.flush()
    return total


class Setup(BaseSetup):
    def run(self, context):
        base_dir = os.path.expanduser("~/Desktop/e31-newapps")
        os.makedirs(base_dir, exist_ok=True)
        
        img_path = os.path.join(base_dir, "signature-image.png")
        img = Image.new("RGB", (48, 48), color=(70, 130, 180))
        draw = ImageDraw.Draw(img)
        draw.rectangle([4, 4, 44, 44], outline=(255, 255, 255), width=2)
        img.save(img_path)
        
        instructions_path = os.path.join(base_dir, "mail-2-5-instructions.txt")
        with open(instructions_path, "w", encoding="utf-8") as f:
            f.write("签名文字内容：Best regards, E31 Team\n")
            f.write("\n操作要求：\n")
            f.write("1. 在 Mail 的偏好设置-签名中新建或编辑签名\n")
            f.write("2. 将 signature-image.png 拖入右侧签名预览区\n")
            f.write("3. 在签名中保留上述文字内容\n")
            f.write("4. 新建邮件，主题为 Test Draft - E31，保存草稿\n")
        
        proc = subprocess.run(["open", "-a", "Mail"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        mail_cleared = clear_e31_mail()
        return {"status": "completed", "state": {"mail_cleared": mail_cleared}}
