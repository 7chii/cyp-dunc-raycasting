import random
import assets.game_objects as game_objects
import assets.game_items as game_items
import constmath.constants as constants

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

        # Cria o inimigo
        enemy = game_objects.Enemy((x + 0.5, y + 0.5), name=f"enemy{i+1}", hp=hp, weapon=weapon)
        enemies.append(enemy)

    return enemies
