import constmath.constants as constants
equipable_items_hand = ("knife", "hammer", "chainsaw")
equipable_items_hand_dmg = {
            "knife": 3,
            "hammer": 4,
            "chainsaw": 10
        }

usable_items = ("ecig", "healthjuice", "parteehard")
usable_items_values = {
    "ecig":{"H":1},
    "healthjuice":{"H":10},
    "parteehard":{"D":2}
}

#multiplicadores de valor para itens equipaveis/consumiveis/proteses
item_companies = ("megacorp", "n3kst", "wyutani", "generic")
item_companies_values= {
    "megacorp":2,
    "n3kst":10,
    "wyutani":7,
    "generic":1
}
#Adjacent processing unit
equipable_prosthetics = ("arm", "leg", "eye", "skin", "APU")
equipable_prosthetics_data = {
    "arm":{"nt":1}, #mais um turno para o jogador a cada braco instalado
    "leg":{"sp":0.02}, #aumento base de velocidade
    "eye":{"sc":1}, #define quais objetos sao visiveis no scan, 1 -> armas, 2-> armas e proteses, 3->armas e proteses + info de grades
    "skin":{"df":0.3}, #30% de bloqueio de dano base
    "APU":{"hk":0.2} #20% diminuicao no tempo de hacks base
}

boss_names = ("reeve", "patrick", "tristram", "preston", "adam", "ed")
boss_surnames = ("bateman", "gildenberg", "smith", "hayes", "smasher")
#grades = ("+", "s", "op", "*")
grades = ("Ω", "Σ", "α", "β")

enemy_seniority = ("junior", "midlevel", "senior")
enemy_position = ("hr_defense", "medical_defense", "corporate_defense")
enemy_job = ("sergeant", "captain")

#multiplicador do multiplicador de marcas

status_effects = ("Paralysis", "Angry", "Sad", "Anxious")

