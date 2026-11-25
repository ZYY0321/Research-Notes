import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(os.path.expanduser('~/Desktop/e31-newapps'), exist_ok=True)
        pdf_path = os.path.expanduser('~/Desktop/e31-newapps/ps-2-6-open-pdf-seed.pdf')
        pdf_content = b"""%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n4 0 obj<</Length 44>>stream\nBT /F1 24 Tf 100 700 Td (Test PDF) Tj ET\nendstream endobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000217 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n310\n%%EOF\n"""
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
