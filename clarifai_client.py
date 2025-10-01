clarifai_client.py
import base64
import os
import requests


CLARIFAI_API_KEY = os.getenv('CLARIFAI_API_KEY')
CLARIFAI_MODEL_ID = 'food-item-recognition' # Clarifai food model


CLARIFAI_API_URL = f'https://api.clarifai.com/v2/models/{CLARIFAI_MODEL_ID}/outputs'


HEADERS = {
'Authorization': f'Key {CLARIFAI_API_KEY}',
'Content-Type': 'application/json'
}




def identify_food_from_bytes(image_bytes, max_concepts=5):
"""Rasm baytlarini Clarifai ga yuboradi va topilgan tushunchalar (food labels) ro'yxatini qaytaradi.
Natija: list of (name,confidence)
"""
b64 = base64.b64encode(image_bytes).decode('utf-8')
payload = {
"inputs": [
{"data": {"image": {"base64": b64}}}
]
}
r = requests.post(CLARIFAI_API_URL, headers=HEADERS, json=payload, timeout=30)
r.raise_for_status()
j = r.json()
concepts = []
try:
outputs = j['outputs'][0]
for c in outputs['data'].get('concepts', [])[:max_concepts]:
concepts.append((c.get('name'), c.get('value')))
except Exception:
pass
return concepts
