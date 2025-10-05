import random
import assets.game_items as game_items 
generated_weapons = {}
generated_items = {}
generated_prosthetics = {}

equipable_items_hand = game_items.equipable_items_hand
equipable_items_hand_dmg = game_items.equipable_items_hand_dmg
equipable_prosthetics = game_items.equipable_prosthetics
equipable_prosthetics_data = game_items.equipable_prosthetics_data
# marcas
item_companies = game_items.item_companies
item_companies_values = game_items.item_companies_values

# grades
grades = game_items.grades


def generate_weapon(name, level):
    """
    Gera uma arma com progressão baseada no nível (1-50)
    """
    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = item_companies_values[company]

    min_grades = 0
    if level >= 5:
        min_grades = 1
    if level >= 20:
        min_grades = 2
    if level >= 30:
        min_grades = 3
    if level >= 40:
        min_grades = 4

    max_grades = max(min(level // 15, 4), min_grades)
    # até 4 símbolos
    num_grades = random.randint(min_grades, max_grades)
    grade_symbols = "-".join(random.choices(grades, k=num_grades))

    # -------- nome --------
    full_name = f"{company}-{name}"
    if grade_symbols:
        full_name += f"-{grade_symbols}"

    # -------- base dmg --------
    base_dmg = equipable_items_hand_dmg[name]
    damage = int(base_dmg * multiplier)

    # -------- efeitos dos grades --------
    effects = {
        "extra_accuracy": grade_symbols.count("ω") * 0.1,  # 10% menos chance de errar por 'ω'
        "stun_chance": grade_symbols.count("σ") * 0.15,   # 15% chance de stunar por 'σ'
        "force_unequip": grade_symbols.count("α") > 0,    # se houver α, força desequip
        "hp_multiplier": 1 + grade_symbols.count("β") * 0.2  # β aumenta HP em 20%
    }

    weapon_obj = {
        "name": full_name,
        "damage": damage,
        "effects": effects,
        "level": level
    }

    # salva no dicionário
    generated_weapons[full_name] = weapon_obj
    return weapon_obj

def generate_item(name: str, level: int):
    """
    Gera um item com prog baseada no level atual (1–50).
    Usa empresas para escalar o valor dos efeitos.
    Agora tb adiciona grades (ω, σ, α, β) ao nome e efeitos extras.
    """
    if name not in game_items.usable_items:
        raise ValueError(f"{name} not a valid item!")

    # -------- Progressão de empresas --------
    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = item_companies_values[company]

    # -------- Grades --------
    min_grades = 0
    if level >= 15:
        min_grades = 1
    if level >= 35:
        min_grades = 2

    max_grades = max(min(level // 20, 2), min_grades)
    num_grades = random.randint(min_grades, max_grades)
    grade_symbols = "-".join(random.choices(grades, k=num_grades))

    full_name = f"{company}-{name}"
    if grade_symbols:
        full_name += f"-{grade_symbols}"

    item_obj = {
        "name": full_name
    }

    generated_items[full_name] = item_obj
    return item_obj
def generate_prosthetic(name: str, level: int):
    """
    Gera uma protese com efeitos baseados no tipo, empresa e grades.
    """
    if name not in equipable_prosthetics:
        raise ValueError(f"{name} not a valid prosthetic!")

    # -------- Progressão de empresas --------
    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = item_companies_values[company]

    # -------- grades --------
    min_grades = 0
    if level >= 15:
        min_grades = 1
    if level >= 35:
        min_grades = 2

    max_grades = max(min(level // 20, 2), min_grades)
    num_grades = random.randint(min_grades, max_grades)
    grade_symbols = "-".join(random.choices(grades, k=num_grades))

    # -------- nome --------
    full_name = f"{company}-{name}"
    if grade_symbols:
        full_name += f"-{grade_symbols}"



    prosthetic_obj = {
        "name": full_name
    }

    generated_prosthetics[full_name] = prosthetic_obj
    return prosthetic_obj

for lvl in range(1, 51):
    for weapon_name in equipable_items_hand:
        generate_weapon(weapon_name, lvl)
    for prosthetic_name in equipable_prosthetics:
        generate_prosthetic(prosthetic_name, lvl)

