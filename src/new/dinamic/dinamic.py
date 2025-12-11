import random
import assets.game_objects as game_objects
import assets.game_items as game_items
import constmath.constants as constants
import dinamic.item_dinamic as item_dinamic
import random
from collections import deque

def generate_random_grid(width: int, height: int, wall_chance: float = 0.2, cubicle_chance: float = 0.05, saferoom=False) -> list[list[int]]:
    """
    Gera uma grid com paredes random, garantindo que todos os espaços vazios fiquem junsto.
    0 = chao
    1 = parede
    """
    # gerar grid com paredes

    grid = []
    if saferoom:

        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    row.append(1)
                else:
                    row.append(0)
            grid.append(row)

        possible_positions = [
            (x, y)
            for x in range(2, width - 3)
            for y in range(2, height - 3)
        ]
        random.shuffle(possible_positions)

        shop_values = [4, 5, 6]
        for shop in shop_values:
            for pos in possible_positions:
                x, y = pos
                if grid[y][x] == 0 and grid[y+1][x] == 0 and grid[y][x+1] == 0 and grid[y+1][x+1] == 0:
                    grid[y][x] = shop
                    grid[y+1][x] = shop
                    grid[y][x+1] = shop
                    grid[y+1][x+1] = shop
                    break
    else:
        for y in range(height):
            row = []
            for x in range(width):
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    row.append(1)  # borda sempre parede
                else:
                    if random.random() < wall_chance:
                        row.append(1)
                    else:
                        # 5% de chance de cubiculo
                        row.append(2 if random.random() < cubicle_chance else 0)
            grid.append(row)

        #func para achar componentes conectados
        def bfs(start):
            q = deque([start])
            visited = {start}
            while q:
                cx, cy = q.popleft()
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if grid[ny][nx] == 0 and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            q.append((nx, ny))
            return visited

        #  encontrar todos os espaços livres
        all_regions = []
        seen = set()
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0 and (x, y) not in seen:
                    region = bfs((x, y))
                    all_regions.append(region)
                    seen |= region

        # Se so um espaco livre
        if len(all_regions) <= 1:
            return grid

        #  manter o maior espaco como principal
        main_region = max(all_regions, key=len)
        other_regions = [r for r in all_regions if r != main_region]

        # conectar espacos menores a maiores
        for region in other_regions:
            # escolhe um ponto da sala atual e um do espaco principal
            rx, ry = random.choice(list(region))
            mx, my = random.choice(list(main_region))

            # faz um caminho ate conectar
            cx, cy = rx, ry
            while (cx, cy) != (mx, my):
                if cx < mx: cx += 1
                elif cx > mx: cx -= 1
                elif cy < my: cy += 1
                elif cy > my: cy -= 1
                grid[cy][cx] = 0  # abre caminho

            # atualiza a sala principal
            main_region |= region
    return grid

import random

def add_exit_door(grid_dict):
    """
    Escolhe uma parede de fora random (q tem caminho livre adjacente) 
    e troca por uma porta (3) no dict da grid.
    """
    xs = [x for x, y in grid_dict.keys()]
    ys = [y for x, y in grid_dict.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    candidates = []

    # verifica topo e base
    for xi in range(min_x + 1, max_x):
        if grid_dict.get((xi, min_y), 0) == 1 and any(grid_dict.get((xi + dx, min_y + dy), 1) == 0 for dx, dy in [(0,1),(1,0),(-1,0)]):
            candidates.append((xi, min_y))
        if grid_dict.get((xi, max_y), 0) == 1 and any(grid_dict.get((xi + dx, max_y + dy), 1) == 0 for dx, dy in [(0,-1),(1,0),(-1,0)]):
            candidates.append((xi, max_y))

    # verifica esquerda e direita
    for yi in range(min_y + 1, max_y):
        if grid_dict.get((min_x, yi), 0) == 1 and any(grid_dict.get((min_x + dx, yi + dy), 1) == 0 for dx, dy in [(1,0),(0,1),(0,-1)]):
            candidates.append((min_x, yi))
        if grid_dict.get((max_x, yi), 0) == 1 and any(grid_dict.get((max_x + dx, yi + dy), 1) == 0 for dx, dy in [(-1,0),(0,1),(0,-1)]):
            candidates.append((max_x, yi))

    if not candidates:
        raise ValueError("external wall path inaccessible.")

    x, y = random.choice(candidates)
    grid_dict[(x, y)] = 3  # define porta
    return x, y


def generate_enemies_distributed(num_enemies, grid_dict, level, min_distance=2):
    enemies = []
    free_positions = [pos for pos, val in grid_dict.items() if val == 0]

    # -------- Boss Spawn --------
    if level % 5 == 0:
        if not free_positions:
            return enemies
        pos = random.choice(free_positions)
        x, y = pos

        # Nome do boss
        boss_name = f"{random.choice(game_items.boss_names)}-{random.choice(game_items.boss_surnames)}"

        max_grades = min(level // 15, 4)
        min_grades = 0
        if level >= 5:
            min_grades = 1
        if level >= 20:
            min_grades = 2
        if level >= 30:
            min_grades = 3
        if level >= 40:
            min_grades = 4

        if max_grades < min_grades:
            max_grades = min_grades

        num_grades = random.randint(min_grades, max_grades)



        grade_symbols = "-".join(random.choices(game_items.grades, k=num_grades))
        boss_name = f"{boss_name}-{grade_symbols}"

        
        boss_hp_base = int(50 + level**1.8) 
        boss_hp = boss_hp_base + num_grades * 100 
        chosen = random.choice(game_items.equipable_items_hand)
        boss_weapon = item_dinamic.generate_weapon(chosen, level)
        boss_weapon = boss_weapon['name']
        boss_chance = 0.0

        boss = game_objects.Enemy((x + 0.5, y + 0.5), boss_chance, name=boss_name, hp=boss_hp, weapon=boss_weapon, is_boss=True)
        boss.is_boss = True
        num_prostheses = random.randint(1, min(3, level // 15 + 1))  
        for _ in range(num_prostheses):
            prost_type = random.choice(game_items.equipable_prosthetics)
            prosthetic = item_dinamic.generate_prosthetic(prost_type, level)
            boss.install_prosthetic(prosthetic)


        damage_per_symbol = min(2 + level // 10, 8)
        boss.extra_damage = num_grades * damage_per_symbol

        enemies.append(boss)
        return enemies

    # -------- inimigos nomrais --------
    for i in range(num_enemies):
        if not free_positions:
            break  

        pos = random.choice(free_positions)
        x, y = pos

        free_positions = [
            p for p in free_positions
            if abs(p[0]-x) > min_distance or abs(p[1]-y) > min_distance
        ]


        chosen = random.choice(game_items.equipable_items_hand)
        weapon = item_dinamic.generate_weapon(chosen, level)
        weapon = weapon["name"]
        chance = random.random()
        seniority = random.choice(game_items.enemy_seniority)
        position = random.choice(game_items.enemy_position)
        job = random.choice(game_items.enemy_job)

        base_name = f"{seniority}-{position}-{job}-{i}"

        max_grades = min(level // 15, 4)
        min_grades = 0
        symbolVal = 1
        if level >= 5:
            min_grades = 1
            symbolVal = 7
        if level >= 20:
            min_grades = 2
            symbolVal = 10
        if level >= 30:
            min_grades = 3
            symbolVal = 30
        if level>= 40:
            min_grades = 4
            symbolVal = 50
        if max_grades < min_grades:
            max_grades = min_grades

        num_grades = random.randint(min_grades, max_grades)
        name = base_name
        if num_grades > 0:
            grade_symbols = "-".join(random.choices(game_items.grades, k=num_grades))
            name = f"{base_name}-{grade_symbols}"
        else:
            name = base_name




        hp_base = 5 + level * 3 
        hp_base += random.randint(0, 3)

        hp = hp_base + num_grades * symbolVal

        enemy = game_objects.Enemy((x + 0.5, y + 0.5), chance, name=name, hp=hp, weapon=weapon)

        damage_per_symbol = min(1 + level // 12, 5)
        enemy.extra_damage = num_grades * damage_per_symbol
        enemy.parse_grades()
        num_prostheses = random.randint(0, min(3, level // 15 + 1)) 
        for _ in range(num_prostheses):
            prost_type = random.choice(game_items.equipable_prosthetics)
            prosthetic = item_dinamic.generate_prosthetic(prost_type, level)
            enemy.install_prosthetic(prosthetic)
        enemies.append(enemy)

    return enemies

def generate_shop_inventory(level: int) -> dict:
    """
    Gera o inventario das lojas
    """

    inventory = {"weapons": [], "prosthetics": [], "items": []}

    num_items = random.randint(4, 8)
    num_prosthetics = random.randint(4, 8)
    num_weapons = random.randint(4, 7)

    for num in range(num_weapons):
        weapon_name = random.choice(game_items.equipable_items_hand)
        weapon_obj = item_dinamic.generate_weapon(weapon_name, level)
        inventory["weapons"].append(weapon_obj)
    for num in range(num_prosthetics):
        prost_name = random.choice(game_items.equipable_prosthetics)
        prost_obj = item_dinamic.generate_prosthetic(prost_name, level)
        inventory["prosthetics"].append(prost_obj)

    usable_names = list(game_items.usable_items)
    for num in range(num_items):
        item_name = random.choice(usable_names)
        item_obj = item_dinamic.generate_item(item_name, level)
        inventory["items"].append(item_obj)

    return inventory
