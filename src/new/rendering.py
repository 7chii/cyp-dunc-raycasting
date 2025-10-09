import constmath.constants as constants
import pygame as pg
import constmath.functions as functions
import constmath.numerical as numerical
import assets.game_items as game_items

ASCII_CHARS = constants.ASCII_CHARS
_char_surface_cache = {}

def _char_for_color(color):
    r, g, b = color[:3]
    brightness = (r + g + b) / (3 * 255.0)
    idx = int(brightness * (len(ASCII_CHARS) - 1))
    return ASCII_CHARS[max(0, min(idx, len(ASCII_CHARS) - 1))]

def _blit_cached_char(screen, font, ch, color, cell_x, cell_y, CHAR_W, CHAR_H):
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
    """Copia o fundo pre-renderizado."""
    screen.blit(background_surface, (0,0))
def cast_rays_ascii(screen, origin, direction, plane, grid_dict, width, height, font, step=1, see_through=False):
    SHOP_COLORS = {
        4: constants.PROSTBUY,
        5: constants.CAFETERIA,
        6: constants.MILBAY,
    }

    SHOP_NAMES = game_items.SHOP_NAMES

    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    half_h = height // 2

    for cx in range(0, cols, step):
        x_pixel = cx * CHAR_W + CHAR_W // 2
        camera_x = (2 * x_pixel) / width - 1
        ray = constants.Point2(direction.x + plane.x * camera_x,
                               direction.y + plane.y * camera_x)

        dist, side, element, cubicle_hit, shop_hit, stair_hit = run_along_ray(origin, ray, grid_dict)
        if side == -1:
            continue

        safe_dist = dist if dist != 0 else 1e-6
        line_height = height / (safe_dist * 2)
        y_start = max(0, int(half_h - line_height / 2))
        y_end = min(height - 1, int(half_h + line_height / 2))

        wall_color = None
        #parede
        if element == 1:
            wall_color = constants.WALL
            ratio = 1 - (1 / (safe_dist + 1))
            if side == 0:
                wall_color = functions.darken_rgb(wall_color, 50)
            wall_color = functions.darken_rgb(wall_color, ratio * 150)

        # escada
        elif element == 3:
            wall_color = constants.DOOR
            ratio = 1 - (1 / (safe_dist + 1))
            wall_color = functions.darken_rgb(wall_color, ratio * 120)

        # desenhar parede e escada
        if wall_color:
            wall_char = _char_for_color(wall_color)
            for row in range(y_start // CHAR_H, y_end // CHAR_H + 1):
                _blit_cached_char(screen, font, wall_char, wall_color, cx, row, CHAR_W, CHAR_H)

        # lojas
        if shop_hit is not None:
            shop_dist, side, shop_type = shop_hit
            color = SHOP_COLORS.get(shop_type, constants.CUBICLE)
            name = SHOP_NAMES.get(shop_type, "CUBICLE")

            ratio = 1 - (1 / (shop_dist + 1))
            color = functions.darken_rgb(color, ratio * 120)

            cubicle_height = height / (shop_dist * 4)
            y_start_c = max(0, int(half_h - cubicle_height / 2))
            y_end_c = min(height - 1, int(half_h + cubicle_height / 2))

            cubicle_char = _char_for_color(color)
            start_row = y_start_c // CHAR_H
            end_row = y_end_c // CHAR_H
            text_row = (start_row + end_row) // 2

            for row in range(start_row, end_row + 1):
                if row == text_row:
                    continue
                _blit_cached_char(screen, font, cubicle_char, color, cx, row, CHAR_W, CHAR_H)

            if cx % 9 == 0:
                text = name
                text_surf = font.render(text, True, constants.CUBICLE_LINE)
                text_rect = text_surf.get_rect()
                text_rect.centery = text_row * CHAR_H + CHAR_H // 2
                text_rect.centerx = cx * CHAR_W + (7 * CHAR_W) // 2
                screen.blit(text_surf, text_rect)

        # --- cubículos ---
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

            if cx % 7 == 0:
                text = "CUBICLE"
                text_surf = font.render(text, True, constants.CUBICLE_LINE)
                text_rect = text_surf.get_rect()
                text_rect.centery = text_row * CHAR_H + CHAR_H // 2
                text_rect.centerx = cx * CHAR_W + (7 * CHAR_W) // 2
                screen.blit(text_surf, text_rect)

    if see_through:
        for pos, elem in grid_dict.items():
            if elem == 3:  # escada
                dx = pos[0] - origin.x
                dy = pos[1] - origin.y

                inv_det = 1.0 / (plane.x * direction.y - direction.x * plane.y)
                transform_x = inv_det * (direction.y * dx - direction.x * dy)
                transform_y = inv_det * (-plane.y * dx + plane.x * dy)

                if transform_y <= 0:
                    continue

                stair_dist = max(0.1, (dx**2 + dy**2) ** 0.5)
                ray_dir = constants.Point2(dx / stair_dist, dy / stair_dist)
                wall_dist, _, _, _, _, _ = run_along_ray(origin, ray_dir, grid_dict)

                stair_screen_x = int((width / 2) * (1 + transform_x / transform_y))

                ratio = 1 - (1 / (stair_dist + 1))
                color = functions.darken_rgb(constants.DOOR, ratio * 100)

                stair_height_px = height / (stair_dist * 1.8)
                stair_width_px = stair_height_px * 0.5

                y_start_s = max(0, int(half_h - stair_height_px / 2))
                y_end_s = min(height - 1, int(half_h + stair_height_px / 2))

                center_cx = max(0, min(cols - 1, stair_screen_x // CHAR_W))
                half_width_cx = max(1, int(stair_width_px // (2 * CHAR_W)))
                left_cx = max(0, center_cx - half_width_cx)
                right_cx = min(cols - 1, center_cx + half_width_cx)

                stair_char = "█" 

                for cx in range(left_cx, right_cx + 1):
                    for row in range(y_start_s // CHAR_H, y_end_s // CHAR_H + 1):
                        _blit_cached_char(screen, font, stair_char, color, cx, row, CHAR_W, CHAR_H)

def draw_enemies_ascii(screen, player, enemies, grid_dict, width, height, font, see_through_walls=False):
    CHAR_W, CHAR_H = font.size("A")
    cols = width // CHAR_W
    rows = height // CHAR_H
    half_h = height // 2
    if enemies:

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
                wall_dist, _, _, _, _, _= run_along_ray(player.xy, ray_dir, grid_dict)
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
            wall_dist, _, _, _, _, _ = run_along_ray(player.xy, ray_dir, grid_dict)
            if wall_dist < item_dist:
                continue

        item_screen_x = int((width / 2) * (1 + transform_x / transform_y))
        center_cx = max(0, min(cols - 1, item_screen_x // CHAR_W))

        scale = 0.2 / item_dist
        item_size_px = max(CHAR_H, min(int(height * scale), CHAR_H * 2))

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

def run_along_ray(start, ray_dir, grid_dict, see_through=False):
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

    cubicle_hit = None
    stair_hit = None
    max_iter = 200
    shop_hit = None

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

        if element in (4, 5, 6):  # lojas
            dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
            shop_hit = (dist, side, element)
            return dist, side, element, cubicle_hit, shop_hit, stair_hit

        if element == 2:  # cubic
            if cubicle_hit is None:
                dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
                cubicle_hit = (dist, side, 2)

        elif element == 3: #escadas
            if stair_hit is None:
                dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
                stair_hit = (dist, side, 3)
                if not see_through:
                    return dist, side, element, cubicle_hit, shop_hit, stair_hit

        if element == 1:  # parede
            dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
            return dist, side, element, cubicle_hit, shop_hit, stair_hit

    return float("inf"), -1, -1, cubicle_hit, shop_hit, stair_hit

def find_free_position_with_exit(grid_dict, player_pos):
    max_x = max(x for x, _ in grid_dict.keys()) + 1
    max_y = max(y for _, y in grid_dict.keys()) + 1

    px, py = int(player_pos.x), int(player_pos.y)

    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = px + dx, py + dy
        if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
            return nx + 0.5, ny + 0.5

    return px + 0.5, py + 0.5