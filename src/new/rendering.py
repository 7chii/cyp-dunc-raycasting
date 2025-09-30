import constmath.constants as constants
import pygame as pg
import constmath.functions as functions
import constmath.numerical as numerical

ASCII_CHARS = constants.ASCII_CHARS  # string, ex: " .:-=+*#%@"

# cache global de superfícies (char, cor) -> Surface
_char_surface_cache = {}

def _char_for_color(color):
    """Escolhe caractere por brilho da cor (r,g,b)."""
    r, g, b = color[:3]
    brightness = (r + g + b) / (3 * 255.0)
    idx = int(brightness * (len(ASCII_CHARS) - 1))
    return ASCII_CHARS[max(0, min(idx, len(ASCII_CHARS) - 1))]

def _blit_cached_char(screen, font, ch, color, cell_x, cell_y, CHAR_W, CHAR_H):
    """Desenha caractere na grade usando cache de superfícies."""
    key = (ch, color)
    if key not in _char_surface_cache:
        _char_surface_cache[key] = font.render(ch, True, color)
    surf = _char_surface_cache[key]
    screen.blit(surf, (cell_x * CHAR_W, cell_y * CHAR_H))

def clear_screen(screen):
    screen.fill((0,0,0))

def draw_fps(screen, font, clock, half_w):
    text = font.render(f"fps={int(clock.get_fps())}", False, (255,0,0))
    screen.blit(text, (half_w,0))

def draw_level_number(screen, font, level, width_minus_100):
    text = font.render(f"f={level}", False, (255,0,0))
    screen.blit(text, (width_minus_100,0))

def pre_render_background(font, width, height):
    """Pré-renderiza teto e chão como um único Surface."""
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    rows = height // CHAR_H
    half_row = rows // 2

    floor_char = _char_for_color(constants.FLOOR)
    ceil_char = _char_for_color(constants.CEILING)

    surf = pg.Surface((cols * CHAR_W, rows * CHAR_H))
    for cy in range(rows):
        for cx in range(cols):
            if cy >= half_row:
                _blit_cached_char(surf, font, floor_char, constants.FLOOR, cx, cy, CHAR_W, CHAR_H)
            else:
                _blit_cached_char(surf, font, ceil_char, constants.CEILING, cx, cy, CHAR_W, CHAR_H)
    return surf

def draw_floor_and_ceiling_ascii(screen, background_surface):
    """Copia o fundo pré-renderizado."""
    screen.blit(background_surface, (0,0))

def cast_rays_ascii(screen, origin, direction, plane, grid_dict, width, height, font, step=1, see_through=False):
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    half_h = height // 2

    for cx in range(0, cols, step):
        x_pixel = cx * CHAR_W + CHAR_W // 2
        camera_x = (2 * x_pixel) / width - 1
        ray = constants.Point2(direction.x + plane.x * camera_x,
                               direction.y + plane.y * camera_x)

        # percorre o raio e retorna parede e cubículo
        dist, side, element, cubicle_hit = run_along_ray(origin, ray, grid_dict)

        if side == -1:
            continue

        # --- detectar porta ---
        # percorre o mesmo raio e pega a primeira porta (valor 3)
        door_dist, _, _ = None, None, None
        for step_dist in range(1, 50):  # checar até 50 unidades à frente
            check_x = int(origin.x + ray.x * step_dist)
            check_y = int(origin.y + ray.y * step_dist)
            if grid_dict.get((check_x, check_y), 0) == 3:
                door_dist = step_dist
                break

        # decide o que desenhar primeiro
        wall_color = None
        line_height = None
        y_start = None
        y_end = None
        wall_char = None

        safe_dist = dist if dist != 0 else 1e-6
        line_height = height / (safe_dist * 2)
        y_start = max(0, int(half_h - line_height / 2))
        y_end = min(height - 1, int(half_h + line_height / 2))

        # parede normal
        if element == 1:
            wall_color = constants.WALL
            ratio = 1 - (1 / (safe_dist + 1))
            if side == 0:
                wall_color = functions.darken_rgb(wall_color, 50)
            wall_color = functions.darken_rgb(wall_color, ratio * 150)

        # porta: desenhar se mais próxima que a parede ou see_through=True
        if door_dist is not None and (door_dist < safe_dist or see_through):
            door_color = (200, 150, 0)
            ratio = 1 - (1 / (door_dist + 1))
            door_color = functions.darken_rgb(door_color, ratio * 50)
            door_line_height = height / (door_dist * 2)
            door_y_start = max(0, int(half_h - door_line_height / 2))
            door_y_end = min(height - 1, int(half_h + door_line_height / 2))
            door_char = _char_for_color(door_color)

            for row in range(door_y_start // CHAR_H, door_y_end // CHAR_H + 1):
                _blit_cached_char(screen, font, door_char, door_color, cx, row, CHAR_W, CHAR_H)

        # desenha parede
        if wall_color:
            wall_char = _char_for_color(wall_color)
            for row in range(y_start // CHAR_H, y_end // CHAR_H + 1):
                _blit_cached_char(screen, font, wall_char, wall_color, cx, row, CHAR_W, CHAR_H)

        # cubículos continuam iguais
        if cubicle_hit is not None:
            c_dist, _, _ = cubicle_hit
            safe_dist_c = c_dist if c_dist != 0 else 1e-6
            color = constants.CUBICLE
            ratio = 1 - (1 / (safe_dist_c + 1))
            color = functions.darken_rgb(color, ratio * 120)

            cubicle_height = height / (safe_dist_c * 4)
            y_start = int(half_h)
            y_end = min(height - 1, int(half_h + cubicle_height))

            cubicle_char = _char_for_color(color)
            start_row = y_start // CHAR_H
            end_row = y_end // CHAR_H
            text_row = (start_row + end_row) // 2

            for row in range(start_row, end_row + 1):
                if row == text_row:
                    continue
                _blit_cached_char(screen, font, cubicle_char, color, cx, row, CHAR_W, CHAR_H)

            # escreve "CUBICLE" uma vez
            if cx % 7 == 0:
                text = "CUBICLE"
                text_surf = font.render(text, True, constants.CUBICLE_LINE)
                text_rect = text_surf.get_rect()
                text_rect.centery = text_row * CHAR_H + CHAR_H // 2
                text_rect.centerx = cx * CHAR_W + (7 * CHAR_W) // 2
                screen.blit(text_surf, text_rect)




def draw_enemies_ascii(screen, player, enemies, grid_dict, width, height, font, see_through_walls=False):
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
            wall_dist, _, _, _= run_along_ray(player.xy, ray_dir, grid_dict)
            if wall_dist < enemy_dist:
                continue

        enemy_screen_x = int((width / 2) * (1 + transform_x / transform_y))
        scale = enemy.size / enemy_dist if enemy_dist > 0 else enemy.size
        enemy_height_px = min(int(height * scale), min(width, height) // 2)
        enemy_width_px = enemy_height_px

        center_cx = max(0, min(cols - 1, enemy_screen_x // CHAR_W))
        half_width_cx = max(1, enemy_width_px // (2 * CHAR_W))

        left_cx = max(0, center_cx - half_width_cx)
        right_cx = min(cols - 1, center_cx + half_width_cx)

        top_py = half_h - enemy_height_px // 2
        bottom_py = half_h + enemy_height_px // 2
        top_row = max(0, top_py // CHAR_H)
        bottom_row = min(rows - 1, bottom_py // CHAR_H)

        ch = _char_for_color(enemy.color)
        color = constants.BOSS if enemy.is_boss else enemy.color

        for cy in range(left_cx, right_cx + 1):
            for ry in range(top_row, bottom_row + 1):
                _blit_cached_char(screen, font, ch, color, cy, ry, CHAR_W, CHAR_H)

def draw_items_ascii(screen, player, dropped_items, grid_dict, width, height, font, see_through_walls=False):
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    half_h = height // 2

    items_sorted = sorted(
        dropped_items,
        key=lambda d: (d[0] - player.x) ** 2 + (d[1] - player.y) ** 2,
        reverse=True
    )

    for (ix, iy, item_name) in items_sorted:
        rel_x = ix - player.x
        rel_y = iy - player.y

        inv_det = 1.0 / (player.plane.x * player.direction.y - player.direction.x * player.plane.y)
        transform_x = inv_det * (player.direction.y * rel_x - player.direction.x * rel_y)
        transform_y = inv_det * (-player.plane.y * rel_x + player.plane.x * rel_y)
        if transform_y <= 0:
            continue

        item_dist = (rel_x**2 + rel_y**2) ** 0.5
        if not see_through_walls:
            ray_dir = constants.Point2(rel_x / item_dist, rel_y / item_dist)
            wall_dist, _, _, _ = run_along_ray(player.xy, ray_dir, grid_dict)
            if wall_dist < item_dist:
                continue

        # posição horizontal na tela
        item_screen_x = int((width / 2) * (1 + transform_x / transform_y))
        center_cx = max(0, min(cols - 1, item_screen_x // CHAR_W))

        # escala do item pelo depth
        scale = 0.2 / item_dist
        item_size_px = max(CHAR_H, min(int(height * scale), CHAR_H * 2))

        # --- posição vertical corrigida: projeta como sprite, mas com offset para o chão ---
        sprite_screen_y = int((height / 2) + (height / transform_y) * 0.25)

        top_py = sprite_screen_y - item_size_px
        bottom_py = sprite_screen_y
        top_row = max(0, top_py // CHAR_H)
        bottom_row = min((height - 1) // CHAR_H, bottom_py // CHAR_H)

        ch = _char_for_color(constants.ITEMS)
        color = constants.ITEMS

        for cy in range(center_cx - 1, center_cx + 2):
            if 0 <= cy < cols:
                for ry in range(top_row, bottom_row + 1):
                    _blit_cached_char(screen, font, ch, color, cy, ry, CHAR_W, CHAR_H)


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

    cubicle_hit = None  # salva primeira colisão de cubículo

    max_iter = 200
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

        if element == 2 and cubicle_hit is None:
            # salva cubículo mas continua andando
            dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
            cubicle_hit = (dist, side, 2)

        if element == 1:  # parede sólida → para
            dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
            return dist, side, 1, cubicle_hit

    return float("inf"), -1, -1, cubicle_hit


def find_free_position_with_exit(grid_dict, player_pos):
    max_x = max(x for x, _ in grid_dict.keys()) + 1
    max_y = max(y for _, y in grid_dict.keys()) + 1

    px, py = int(player_pos.x), int(player_pos.y)

    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = px + dx, py + dy
        if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
            return nx + 0.5, ny + 0.5

    return px + 0.5, py + 0.5
