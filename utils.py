# utils.py


def pretty_food_text(nutrition_json):
foods = nutrition_json.get('foods', [])
if not foods:
return None
f = foods[0]
name = f.get('food_name')
calories = f.get('nf_calories')
serving_qty = f.get('serving_qty')
serving_unit = f.get('serving_unit')
prot = f.get('nf_protein')
carbs = f.get('nf_total_carbohydrate')
fat = f.get('nf_total_fat')
text = (f"Taom: {name}\nPorsiya: {serving_qty} {serving_unit}\n"
f"Kaloriya: {calories} kcal\nProtein: {prot} g\nKarbonhidrat: {carbs} g\nYog': {fat} g")
return text
