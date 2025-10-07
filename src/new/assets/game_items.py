import constmath.constants as constants
equipable_items_hand = ("knife", "hammer", "chainsaw")
equipable_items_hand_dmg = {
            "knife": 3,
            "hammer": 4,
            "chainsaw": 10
        }
cuttable_items = ("knife", "chainsaw")

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
#Adjacent processing unit (APU)
equipable_prosthetics = ("arm", "leg", "eye", "skin", "apu")
equipable_prosthetics_data = {
    "arm":{"nt":1}, #mais um turno para o jogador a cada braco instalado
    "leg":{"uq":0.3}, #dim chance de unequip do jogador
    "eye":{"sc":1}, #define quantos objetos sao visiveis no scan
    "skin":{"df":0.3}, #dim chance de stun e reducao de dano
    "apu":{"hk":0.2} #20% diminuicao no tempo de hacks base
}

boss_names = ("reeve", "patrick", "tristram", "preston", "adam", "ed")
boss_surnames = ("bateman", "gildenberg", "smith", "hayes", "smasher")

grades = ("ω", "σ", "α", "β")

enemy_seniority = ("junior", "midlevel", "senior")
enemy_position = ("hr_defense", "medical_defense", "corporate_defense")
enemy_job = ("sergeant", "captain")


status_effects = ("Paralysis", "Angry", "Sad", "Anxious")
shop_names = ("PROSTBUY", "CAFETERIA", "MILBAY" )
SHOP_NAMES = {
        4: "PROSTBUY",
        5: "CAFETERIA",
        6: "MILBAY",
    }