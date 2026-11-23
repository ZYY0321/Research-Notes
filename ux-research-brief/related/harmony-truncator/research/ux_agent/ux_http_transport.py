"""Transport-only bridge for Node fetch TLS failures; request arrives through stdin."""
import json
import sys

import requests

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
request = json.load(sys.stdin)
try:
    response = requests.post(
        request['url'], headers=request['headers'],
        data=request['body'].encode('utf-8'), timeout=120,
    )
    print(json.dumps({'status': response.status_code, 'body': response.text}))
except requests.RequestException as error:
    print(json.dumps({'error': type(error).__name__}))
