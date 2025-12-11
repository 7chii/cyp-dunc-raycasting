import random
import assets.game_items as game_items
import assets.game_objects as game_objects 
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


def parse_weapon_grades(symbols: list):
    chance_to_hit = 0.01
    stun_chance = 0
    force_unequip = 0.0
    extra_dmg = 0
    for sym in symbols:
                        if sym == "ω":
                            chance_to_hit += 0.2
                            extra_dmg += 20
                        elif sym == "σ":
                            stun_chance += 0.2 
                            extra_dmg += 20
                        elif sym == "α":
                            force_unequip += 0.1
                            extra_dmg += 20
                        elif sym =="β":
                            extra_dmg +=100
    return chance_to_hit, stun_chance, force_unequip, extra_dmg

def generate_weapon(name: str, level: int):
    """
    Gera uma arma com progressão e compatível com get_damage().
    Retorna um dicionário contendo informações completas da arma.
    """
    import random

    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = game_items.item_companies_values.get(company, 1.0)

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
    num_grades = random.randint(min_grades, max_grades)

    symbols = random.choices(game_items.grades, k=num_grades)  # ex: ["ω", "σ"]
    grade_symbols_str = "-".join(symbols)

    full_name = f"{company}-{name}"
    if symbols:
        full_name += f"-{grade_symbols_str}"

    base_dmg = game_items.equipable_items_hand_dmg.get(name, 1)
    dmg = base_dmg

    dmg *= multiplier

    chance_to_hit, stun_chance, force_unequip, extra_dmg = parse_weapon_grades(symbols)
    dmg += extra_dmg

    base_price = 4000
    rarity_bonus = 1 + num_grades * 0.3
    level_bonus = 1 + level * 0.15
    price = int(base_price * level_bonus * multiplier * rarity_bonus)


    weapon_obj = {
        "name": full_name,
        "damage": int(dmg),
        "effects": {
            "chance_to_hit": chance_to_hit,
            "stun_chance": stun_chance,
            "force_unequip": force_unequip,
            "extra_dmg": extra_dmg
        },
        "price": price
    }

    if "generated_weapons" in globals():
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

    base_price = 1400
    rarity_bonus = 1 + num_grades * 0.3
    level_bonus = 1 + level * 0.15
    price = int(base_price * level_bonus * multiplier * rarity_bonus)


    item_obj = {
        "name": full_name,
        "price":price
    }

    generated_items[full_name] = item_obj
    return item_obj
def generate_prosthetic(name: str, level: int):
    """
    Gera uma protese com efeitos baseados no tipo, empresa e grades.
    """
    if name not in equipable_prosthetics:
        raise ValueError(f"{name} not a valid prosthetic!")

    if level < 10:
        possible_companies = ["generic", "megacorp"]
    elif level < 25:
        possible_companies = ["generic", "megacorp", "n3kst"]
    else:
        possible_companies = ["megacorp", "n3kst", "wyutani"]

    company = random.choice(possible_companies)
    multiplier = item_companies_values[company]

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



    base_price = 7000
    rarity_bonus = 1 + num_grades * 0.3
    level_bonus = 1 + level * 0.15
    price = int(base_price * level_bonus * multiplier * rarity_bonus)


    prosthetic_obj = {
        "name": full_name,
        "price": price
    }

    generated_prosthetics[full_name] = prosthetic_obj
    return prosthetic_obj

for lvl in range(1, 51):
    for weapon_name in equipable_items_hand:
        generate_weapon(weapon_name, lvl)
    for prosthetic_name in equipable_prosthetics:
        generate_prosthetic(prosthetic_name, lvl)
