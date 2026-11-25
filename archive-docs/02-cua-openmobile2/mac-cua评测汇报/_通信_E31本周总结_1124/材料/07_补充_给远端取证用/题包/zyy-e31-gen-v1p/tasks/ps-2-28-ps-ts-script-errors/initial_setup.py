import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        desktop = os.path.expanduser('~/Desktop/e31-newapps')
        os.makedirs(desktop, exist_ok=True)
        script_path = os.path.join(desktop, 'script-error.jsx')
        script_content = '''// Create a new document with text layer
var doc = app.documents.add(800, 600, 72, "New Document", NewDocumentMode.RGB);
var textLayer = doc.artLayers.add();
textLayer.kind = LayerKind.TEXT;
var textItem = textLayer.textItme;
textItem.contents = "Sample Text";
textItem.size = 36;
'''
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'ps-2-28-ps-ts-script-errors.txt')
        if os.path.lexists(out_path):
            os.remove(out_path)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
