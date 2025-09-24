import constmath.constants as constants
import pygame as pg
import constmath.functions as functions
import constmath.numerical as numerical

def clear_screen(screen):
    screen.fill((0,0,0))

ASCII_CHARS = constants.ASCII_CHARS  # string, ex: " .:-=+*#%@"

def _char_for_color(color):
    """Escolhe caractere por brilho da cor (r,g,b)."""
    r, g, b = color[:3]
    brightness = (r + g + b) / (3 * 255.0)
    idx = int(brightness * (len(ASCII_CHARS) - 1))
    return ASCII_CHARS[max(0, min(idx, len(ASCII_CHARS) - 1))]

def _blit_char(screen, font, ch, color, cell_x, cell_y, CHAR_W, CHAR_H):
    """Desenha caractere na grade (cell coords), mantendo cor."""
    surf = font.render(ch, True, color)
    screen.blit(surf, (cell_x * CHAR_W, cell_y * CHAR_H))

def clear_screen(screen):
    screen.fill((0,0,0))

def draw_fps(screen, font, clock, half_w):
    text = font.render(f"fps={int(clock.get_fps())}", False, (255,0,0))
    screen.blit(text, (half_w,0))
    
def draw_level_number(screen, font, level, width_minus_100):
    text = font.render(f"f={level}", False, (255,0,0))
    screen.blit(text, (width_minus_100,0))

def draw_floor_and_ceiling_ascii(screen, font, width, height):
    """Desenha teto e chão em caracteres (usa constants.CEILING/FLOOR cores)."""
    # determina tamanho de célula em pixels a partir da fonte (assume monoespaçado)
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    rows = height // CHAR_H
    half_row = rows // 2

    floor_char = _char_for_color(constants.FLOOR)
    ceil_char = _char_for_color(constants.CEILING)

    for cy in range(rows):
        for cx in range(cols):
            if cy >= half_row:
                _blit_char(screen, font, floor_char, constants.FLOOR, cx, cy, CHAR_W, CHAR_H)
            else:
                _blit_char(screen, font, ceil_char, constants.CEILING, cx, cy, CHAR_W, CHAR_H)

def cast_rays_ascii(screen, origin, direction, plane, grid_dict, width, height, font, step=1):
    """
    Raycast, mas agrupado por colunas de caracteres.
    Desenha paredes como blocos de caracteres coloridos.
    """
    assert step >= 1
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    rows = height // CHAR_H
    half_h = height // 2

    # vamos percorrer colunas de caracteres (cx)
    for cx in range(cols):
        # pixel x no centro da coluna
        x_pixel = cx * CHAR_W + CHAR_W // 2
        camera_x = (2 * x_pixel) / width - 1
        ray = constants.Point2(direction.x + plane.x * camera_x,
                               direction.y + plane.y * camera_x)

        dist, side, element = run_along_ray(origin, ray, grid_dict)
        if side == -1:
            continue

        safe_dist = dist if dist != 0 else 1e-6

        color = constants.WALL
        # escurece por distância
        ratio = 1 - (1 / (safe_dist + 1))
        if side == 0:
            color = functions.darken_rgb(color, 50)
        color = functions.darken_rgb(color, ratio * 150)

        # calc do tamanho da linha em pixels (mantive sua fórmula)
        line_height = height / (safe_dist * 2)
        y_start = max(0, int((half_h - line_height / 2)))
        y_end = min(height - 1, int((half_h + line_height / 2)))

        # converte para linhas de caracteres
        start_row = max(0, y_start // CHAR_H)
        end_row = min(rows - 1, y_end // CHAR_H)

        wall_char = _char_for_color(color)

        # desenha caracteres da parede na coluna cx
        for row in range(start_row, end_row + 1):
            _blit_char(screen, font, wall_char, color, cx, row, CHAR_W, CHAR_H)

        # opcional: desenhar teto/solo da mesma coluna caso queira, mas já fazemos antes
        # (mantivemos draw_floor_and_ceiling_ascii para pintar fundo)

def draw_enemies_ascii(screen, player, enemies, grid_dict, width, height, font, see_through_walls=False):
    """
    Desenha inimigos como caracteres coloridos na grade.
    Mantemos projeção para posição/altura e convertemos para células.
    """
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    rows = height // CHAR_H
    half_h = height // 2

    enemies_sorted = sorted(
        enemies, 
        key=lambda e: (e.x - player.x) ** 2 + (e.y - player.y) ** 2, 
        reverse=True
    )

    for enemy in enemies_sorted:
        rel_x = enemy.x - player.x
        rel_y = enemy.y - player.y

        inv_det = 1.0 / (player.plane.x * player.direction.y - player.direction.x * player.plane.y)
        transform_x = inv_det * (player.direction.y * rel_x - player.direction.x * rel_y)
        transform_y = inv_det * (-player.plane.y * rel_x + player.plane.x * rel_y)

        if transform_y <= 0:
            continue

        enemy_dist = (rel_x**2 + rel_y**2) ** 0.5
        if not see_through_walls:
            ray_dir = constants.Point2(rel_x / enemy_dist, rel_y / enemy_dist)
            wall_dist, _, _ = run_along_ray(player.xy, ray_dir, grid_dict)
            if wall_dist < enemy_dist:
                continue

        # posição em pixels e tamanho (como antes)
        enemy_screen_x = int((width / 2) * (1 + transform_x / transform_y))

        # tamanho baseado na distância real (enemy_dist), não no transform_y
        if enemy_dist > 0:
            scale = enemy.size / enemy_dist
        else:
            scale = enemy.size

        enemy_height_px = int(height * scale)
        enemy_width_px = enemy_height_px  # mantém quadrado

        # limite para não ocupar a tela inteira
        max_size = min(width, height) // 2
        enemy_height_px = min(enemy_height_px, max_size)
        enemy_width_px = min(enemy_width_px, max_size)

        # converte para células
        center_cx = max(0, min(cols - 1, enemy_screen_x // CHAR_W))
        half_width_cx = max(1, enemy_width_px // (2 * CHAR_W))

        left_cx = max(0, center_cx - half_width_cx)
        right_cx = min(cols - 1, center_cx + half_width_cx)

        top_py = half_h - enemy_height_px // 2
        bottom_py = half_h + enemy_height_px // 2
        top_row = max(0, top_py // CHAR_H)
        bottom_row = min(rows - 1, bottom_py // CHAR_H)

        # caractere escolhido pelo brilho
        ch = _char_for_color(enemy.color)
        if(enemy.is_boss):
            color = constants.BOSS
        else:
            color = enemy.color

        # desenha bloco 2D de caracteres
        for cy in range(left_cx, right_cx + 1):
            for ry in range(top_row, bottom_row + 1):
                _blit_char(screen, font, ch, color, cy, ry, CHAR_W, CHAR_H)
                
def draw_items_ascii(screen, player, dropped_items, grid_dict, width, height, font, see_through_walls=False):
    """
    Desenha os itens no chão como pequenos quadrados coloridos (ASCII).
    dropped_items = [(x, y, item_name), ...]
    """
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    rows = height // CHAR_H
    half_h = height // 2

    # ordena por distância (mais longe primeiro, para sobreposição correta)
    items_sorted = sorted(
        dropped_items,
        key=lambda d: (d[0] - player.x) ** 2 + (d[1] - player.y) ** 2,
        reverse=True
    )

    for (ix, iy, item_name) in items_sorted:
        rel_x = ix - player.x
        rel_y = iy - player.y

        # transforma para coords de câmera
        inv_det = 1.0 / (player.plane.x * player.direction.y - player.direction.x * player.plane.y)
        transform_x = inv_det * (player.direction.y * rel_x - player.direction.x * rel_y)
        transform_y = inv_det * (-player.plane.y * rel_x + player.plane.x * rel_y)

        if transform_y <= 0:
            continue

        item_dist = (rel_x**2 + rel_y**2) ** 0.5
        if not see_through_walls:
            ray_dir = constants.Point2(rel_x / item_dist, rel_y / item_dist)
            wall_dist, _, _ = run_along_ray(player.xy, ray_dir, grid_dict)
            if wall_dist < item_dist:
                continue

        # posição horizontal na tela
        item_screen_x = int((width / 2) * (1 + transform_x / transform_y))

        # tamanho pequeno, independente do item
        scale = 0.2 / item_dist  # menor que inimigos
        item_size_px = int(height * scale)
        item_size_px = max(CHAR_H, min(item_size_px, CHAR_H * 2))  # mantém mínimo/limite

         # converte para células
        center_cx = max(0, min(cols - 1, item_screen_x // CHAR_W))

        # posiciona próximo ao chão
        base_line = int(height * 0.9)  # altura da base (90% da tela)
        top_py = base_line - item_size_px
        bottom_py = base_line

        top_row = max(0, top_py // CHAR_H)
        bottom_row = min(rows - 1, bottom_py // CHAR_H)


        # caractere e cor do item
        ch = _char_for_color(constants.ITEMS)
        color = constants.ITEMS

        # desenha quadradinho de caracteres
        for cy in range(center_cx - 1, center_cx + 2):
            if 0 <= cy < cols:
                for ry in range(top_row, bottom_row + 1):
                    _blit_char(screen, font, ch, color, cy, ry, CHAR_W, CHAR_H)



# ---------- fim do bloco ASCII ----------
def run_along_ray(start, ray_dir, grid_dict):
    INF = float("inf")

    delta_dist_x = INF if ray_dir.x == 0 else abs(1 / ray_dir.x)
    delta_dist_y = INF if ray_dir.y == 0 else abs(1 / ray_dir.y)

    int_map_x, int_map_y = int(start.x), int(start.y)

    if numerical.is_below(ray_dir.x, 0):
        step_x = -1
        side_dist_x = (start.x - int_map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (int_map_x + 1.0 - start.x) * delta_dist_x

    if numerical.is_below(ray_dir.y, 0):
        step_y = -1
        side_dist_y = (start.y - int_map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (int_map_y + 1.0 - start.y) * delta_dist_y

    max_iter = 100
    while max_iter > 0:
        max_iter -= 1
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            int_map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            int_map_y += step_y
            side = 1

        element = grid_dict.get((int_map_x, int_map_y), -1)
        if element != 0:
            break
    else:
        return float("inf"), -1, -1

    if side == 0:
        perp_dist = side_dist_x - delta_dist_x
    else:
        perp_dist = side_dist_y - delta_dist_y

    return perp_dist, side, element

def find_free_position_with_exit(grid_dict, player_pos):
        max_x = max(x for x, _ in grid_dict.keys()) + 1
        max_y = max(y for _, y in grid_dict.keys()) + 1

        px, py = int(player_pos.x), int(player_pos.y)

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = px + dx, py + dy
            if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
                return nx + 0.5, ny + 0.5

        return px + 0.5, py + 0.5