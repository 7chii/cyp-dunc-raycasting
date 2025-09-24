import random
import assets.game_objects as game_objects
import assets.game_items as game_items
import constmath.constants as constants
import dinamic.item_dinamic as item_dinamic
import random
from collections import deque

def generate_random_grid(width: int, height: int, wall_chance: float = 0.2) -> list[list[int]]:
    """
    Gera uma grid com paredes aleatórias, garantindo que todos os espaços vazios estejam conectados.
    0 = espaço livre
    1 = parede
    """
    # Passo 1: gerar grid com paredes
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                row.append(1)  # parede nas bordas
            else:
                row.append(1 if random.random() < wall_chance else 0)
        grid.append(row)

    # Passo 2: função para achar componentes conectados
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

    # Passo 3: encontrar todas as regiões de espaços livres
    all_regions = []
    seen = set()
    for y in range(height):
        for x in range(width):
            if grid[y][x] == 0 and (x, y) not in seen:
                region = bfs((x, y))
                all_regions.append(region)
                seen |= region

    # Se só existe uma região, já está conectado
    if len(all_regions) <= 1:
        return grid

    # Passo 4: manter a maior região como principal
    main_region = max(all_regions, key=len)
    other_regions = [r for r in all_regions if r != main_region]

    # Passo 5: conectar regiões menores à maior
    for region in other_regions:
        # escolhe um ponto da região atual e um da região principal
        rx, ry = random.choice(list(region))
        mx, my = random.choice(list(main_region))

        # faz um "túnel reto" até conectar
        cx, cy = rx, ry
        while (cx, cy) != (mx, my):
            if cx < mx: cx += 1
            elif cx > mx: cx -= 1
            elif cy < my: cy += 1
            elif cy > my: cy -= 1
            grid[cy][cx] = 0  # abre caminho

        # atualiza a região principal
        main_region |= region

    return grid


def generate_enemies_distributed(num_enemies, grid_dict, level, min_distance=2):
    """
    Gera inimigos distribuídos pelo mapa.
    - Progressão de símbolos, dano e HP até o nível 50.
    - Se o level for múltiplo de 5: cria apenas 1 boss.
    - Caso contrário: gera inimigos normais distribuídos.
    """
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

        # garante que max_grades >= min_grades
        if max_grades < min_grades:
            max_grades = min_grades

        num_grades = random.randint(min_grades, max_grades)



        grade_symbols = "-".join(random.choices(game_items.grades, k=num_grades))
        boss_name = f"{boss_name}-{grade_symbols}"

        # HP base escalado com o nível + extra por símbolos
        boss_hp_base = int(50 + level**1.8)  # crescimento rápido, mas controlado
        boss_hp = boss_hp_base + num_grades * 100 
        chosen = random.choice(game_items.equipable_items_hand)
        boss_weapon = item_dinamic.generate_weapon(chosen, level)
        boss_chance = 0.9

        boss = game_objects.Enemy((x + 0.5, y + 0.5), boss_chance, name=boss_name, hp=boss_hp, weapon=boss_weapon)
        boss.is_boss = True  

        # Progressão de dano extra: até +8 por símbolo no final
        damage_per_symbol = min(2 + level // 10, 8)
        boss.extra_damage = num_grades * damage_per_symbol

        enemies.append(boss)
        return enemies

    # -------- Normal Enemies --------
    for i in range(num_enemies):
        if not free_positions:
            break  

        pos = random.choice(free_positions)
        x, y = pos

        free_positions = [
            p for p in free_positions
            if abs(p[0]-x) > min_distance or abs(p[1]-y) > min_distance
        ]

        # HP base escalado com nível

        chosen = random.choice(game_items.equipable_items_hand)
        weapon = item_dinamic.generate_weapon(chosen, level)
        weapon = weapon["name"]
        chance = random.random()
        seniority = random.choice(game_items.enemy_seniority)
        position = random.choice(game_items.enemy_position)
        job = random.choice(game_items.enemy_job)

        base_name = f"{seniority}-{position}-{job}-{i}"

        # Progressão de símbolos: até 4 no nível 50
        max_grades = min(level // 15, 4)
        min_grades = 0
        if level >= 5:
            min_grades = 1
        if level >= 20:
            min_grades = 2
        if level >= 30:
            min_grades = 3
        if level>= 40:
            min_grades = 4
        if max_grades < min_grades:
            max_grades = min_grades

        num_grades = random.randint(min_grades, max_grades)
        name = base_name
        if num_grades > 0:
            grade_symbols = "-".join(random.choices(game_items.grades, k=num_grades))
            name = f"{base_name}-{grade_symbols}"
        else:
            name = base_name




        # HP extra por símbolo
        hp_base = int(20 + level**1.5 + random.randint(0, 30))  
        hp = hp_base + num_grades * 25  # cada símbolo dá +25 HP # cada símbolo adiciona +5 HP

        enemy = game_objects.Enemy((x + 0.5, y + 0.5), chance, name=name, hp=hp, weapon=weapon)

        # Dano extra progressivo
        damage_per_symbol = min(1 + level // 12, 5)
        enemy.extra_damage = num_grades * damage_per_symbol
        enemy.parse_grades()
        enemies.append(enemy)

    return enemies