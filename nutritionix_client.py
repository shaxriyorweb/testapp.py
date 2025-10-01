# nutritionix_client.py
import os
import requests


APP_ID = os.getenv('NUTRITIONIX_APP_ID')
APP_KEY = os.getenv('NUTRITIONIX_APP_KEY')
BASE = 'https://trackapi.nutritionix.com/v2'
HEADERS = {
'x-app-id': APP_ID,
'x-app-key': APP_KEY,
'Content-Type': 'application/json'
}




def search_common_food(query):
"""Search instant endpoint to find common food matches."""
url = f"{BASE}/search/instant"
params = {'query': query, 'branded': 'false', 'common': 'true'}
r = requests.get(url, headers=HEADERS, params=params, timeout=10)
r.raise_for_status()
return r.json()




def get_nutrients_for_item_natural(text_query):
"""Use natural/nutrients endpoint to get nutritional breakdown for a natural language query like '1 serving rice'"""
url = f"{BASE}/natural/nutrients"
payload = {'query': text_query}
r = requests.post(url, headers=HEADERS, json=payload, timeout=15)
r.raise_for_status()
return r.json()
