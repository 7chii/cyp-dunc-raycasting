import random
import assets.game_items as game_items 
generated_weapons = {}

equipable_items_hand = game_items.equipable_items_hand
equipable_items_hand_dmg = game_items.equipable_items_hand_dmg

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
        "extra_accuracy": grade_symbols.count("+") * 0.1,  # 10% menos chance de errar por '+'
        "stun_chance": grade_symbols.count("S") * 0.15,   # 15% chance de stunar por 'S'
        "force_unequip": grade_symbols.count("OP") > 0,    # se houver OP, força desequip
        "hp_multiplier": 1 + grade_symbols.count("*") * 0.2  # * aumenta HP em 20%
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

# -------- Exemplo: gerar armas para todos os níveis --------
for lvl in range(1, 51):
    for weapon_name in equipable_items_hand:
        generate_weapon(weapon_name, lvl)
