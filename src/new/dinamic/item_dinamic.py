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

# grades/símbolos
grades = game_items.grades


def generate_weapon(name, level):
    """
    Gera uma arma com progressão baseada no nível (1-50)
    """
    # -------- Progressão de marca --------
    # níveis baixos -> marcas fracas, níveis altos -> marcas poderosas
    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = item_companies_values[company]

    # -------- Progressão de grades --------
    # níveis baixos -> poucas grades, níveis altos -> mais grades
    min_grades = 0
    if level >= 5:
        min_grades = 1
    if level >= 20:
        min_grades = 2
    if level >= 30:
        min_grades = 3
    if level >= 40:
        min_grades = 4

    # max_grades escalando com level, mas garantindo que seja pelo menos min_grades
    max_grades = max(min(level // 15, 4), min_grades)
    # até 4 símbolos
    num_grades = random.randint(min_grades, max_grades)
    grade_symbols = "-".join(random.choices(grades, k=num_grades))

    # -------- Nome completo --------
    full_name = f"{company}-{name}"
    if grade_symbols:
        full_name += f"-{grade_symbols}"

    # -------- Base damage --------
    base_dmg = equipable_items_hand_dmg[name]
    damage = int(base_dmg * multiplier)

    # -------- Efeitos dos grades --------
    effects = {
        "extra_accuracy": grade_symbols.count("ω") * 0.1,  # 10% menos chance de errar por '+'
        "stun_chance": grade_symbols.count("σ") * 0.15,   # 15% chance de stunar por 'S'
        "force_unequip": grade_symbols.count("α") > 0,    # se houver OP, força desequip
        "hp_multiplier": 1 + grade_symbols.count("β") * 0.2  # * aumenta HP em 20%
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
    Gera um consumível com progressão baseada no nível (1–50).
    Usa empresas para escalar o valor dos efeitos.
    """
    if name not in game_items.usable_items:
        raise ValueError(f"{name} não é um item consumível válido!")

    # -------- Progressão de empresas --------
    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = item_companies_values[company]

    # -------- Valores base do item --------
    base_effects = game_items.usable_items_values[name].copy()

    # multiplica valores conforme empresa e level
    scaled_effects = {}
    for k, v in base_effects.items():
        scaled_effects[k] = int(v * multiplier * (1 + level * 0.05))  # escala com level também

    # -------- Nome completo --------
    full_name = f"{company}-{name}"

    item_obj = {
        "name": full_name,
        "effects": scaled_effects,
        "level": level
    }

    generated_items[full_name] = item_obj
    return item_obj

def generate_prosthetic(name: str, level: int):
    """
    Gera uma prótese com efeitos baseados no tipo, empresa e grades.
    """
    if name not in equipable_prosthetics:
        raise ValueError(f"{name} não é uma prótese válida!")

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

    # -------- Nome --------
    full_name = f"{company}-{name}"
    if grade_symbols:
        full_name += f"-{grade_symbols}"

    # -------- Efeitos --------
    base_effects = equipable_prosthetics_data[name].copy()
    scaled_effects = {}

    for k, v in base_effects.items():
        scaled_effects[k] = round(v * multiplier * (1 + level * 0.05), 3)

    # efeitos extras dos grades
    if "ω" in grade_symbols:
        scaled_effects["resilience"] = scaled_effects.get("resilience", 0) + 0.2
    if "σ" in grade_symbols:
        scaled_effects["regen"] = scaled_effects.get("regen", 0) + 0.1
    if "α" in grade_symbols:
        scaled_effects["speed"] = scaled_effects.get("speed", 0) + 0.05
    if "β" in grade_symbols:
        scaled_effects["focus"] = scaled_effects.get("focus", 0) + 0.05

    prosthetic_obj = {
        "name": full_name,
        "effects": scaled_effects,
        "level": level
    }

    generated_prosthetics[full_name] = prosthetic_obj
    return prosthetic_obj


# -------- Exemplo: gerar tudo --------
for lvl in range(1, 51):
    for weapon_name in equipable_items_hand:
        generate_weapon(weapon_name, lvl)
    for prosthetic_name in equipable_prosthetics:
        generate_prosthetic(prosthetic_name, lvl)

