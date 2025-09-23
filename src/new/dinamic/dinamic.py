import random
import assets.game_objects as game_objects
import assets.game_items as game_items
import constmath.constants as constants

def generate_random_grid(width: int, height: int, wall_chance: float = 0.2) -> list[list[int]]:
    """
    Gera uma grid com paredes aleatórias.
    wall_chance = probabilidade (0.0–1.0) de um espaço interno virar parede.
    """
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                row.append(1)  # parede nas bordas
            else:
                row.append(1 if random.random() < wall_chance else 0)
        grid.append(row)
    return grid

def generate_enemies_distributed(num_enemies, grid_dict, min_distance=2):
    """
    Gera inimigos distribuídos pelo mapa, evitando aglomeração.
    grid_dict: dicionário {(x, y): 0 ou 1}, onde 0 = espaço livre
    min_distance: distância mínima entre inimigos
    """
    enemies = []
    free_positions = [pos for pos, val in grid_dict.items() if val == 0]  # pega todas posições livres

    for i in range(num_enemies):
        if not free_positions:
            break  # sem mais posições livres

        # Escolhe uma posição aleatória entre as livres
        pos = random.choice(free_positions)
        x, y = pos

        # Remove posições próximas para evitar aglomeração
        free_positions = [
            p for p in free_positions
            if abs(p[0]-x) > min_distance or abs(p[1]-y) > min_distance
        ]

        # HP aleatório
        hp = random.randint(5, 20)

        # Arma aleatória
        weapon = random.choice(game_items.equipable_items_hand)
        chance = random.random()
        seniority = random.choice(game_items.enemy_seniority)
        position = random.choice(game_items.enemy_position)
        job = random.choice(game_items.enemy_job)
        name = f"{seniority}-{position}-{job}-{i}"
        # Cria o inimigo
        enemy = game_objects.Enemy((x + 0.5, y + 0.5), chance, name=name, hp=hp, weapon=weapon)
        enemies.append(enemy)

    return enemies
