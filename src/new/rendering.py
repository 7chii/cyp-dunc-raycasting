import constmath.constants as constants
import pygame as pg
import constmath.functions as functions
import constmath.numerical as numerical

def clear_screen(screen):
    screen.fill((0,0,0))

def draw_floor(screen, width, height):
    pg.draw.rect(screen, constants.FLOOR, (0, height//2, width, height//2))

def draw_ceiling(screen, width, height):
    pg.draw.rect(screen, constants.CEILING, (0,0,width,height//2))

def draw_fps(screen, font, clock, half_w):
    text = font.render(f"fps={int(clock.get_fps())}", False, (255,0,0))
    screen.blit(text, (half_w,0))
    
def draw_level_number(screen, font, level, width_minus_100):
    text = font.render(f"f={level}", False, (255,0,0))
    screen.blit(text, (width_minus_100,0))

def cast_rays(screen, origin, direction, plane, grid_dict, width, height, step=1):
    assert step >= 1
    half_h = height // 2

    for x in range(0, width, step):
        camera_x = (2 * x) / width - 1
        ray = constants.Point2(
            direction.x + plane.x * camera_x,
            direction.y + plane.y * camera_x,
        )

        dist, side, element = run_along_ray(origin, ray, grid_dict)
        if side == -1:
            continue

        safe_dist = dist if dist != 0 else 1e-6

        color = constants.WALL
        ratio = 1 - (1 / (safe_dist + 1))
        if side == 0:
            color = functions.darken_rgb(color, 50)
        color = functions.darken_rgb(color, ratio * 150)

        line_height = height / (safe_dist * 2)
        y_start = max(0, int((half_h - line_height / 2)))
        y_end = min(height - 1, int((half_h + line_height / 2)))

        pg.draw.line(screen, color, (x, y_start), (x, y_end))
def draw_enemies(screen, player, enemies, grid_dict, width, height, see_through_walls=False):
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

        if not see_through_walls:
            enemy_dist = (rel_x**2 + rel_y**2) ** 0.5
            ray_dir = constants.Point2(rel_x / enemy_dist, rel_y / enemy_dist)
            wall_dist, _, _ = run_along_ray(player.xy, ray_dir, grid_dict)
            if wall_dist < enemy_dist:
                continue

        enemy_screen_x = int((width / 2) * (1 + transform_x / transform_y))

        enemy_height = abs(int(height / transform_y * enemy.size))
        enemy_width = enemy_height

        draw_x = enemy_screen_x - enemy_width // 2
        draw_y = half_h - enemy_height // 2

        # Se estiver vendo através de paredes, pode desenhar semi-transparente
        color = enemy.color
        if see_through_walls:
            color = (color[0], color[1], color[2], 128)  # RGBA, 128 = semi-transparente

        pg.draw.rect(screen, color, (draw_x, draw_y, enemy_width, enemy_height))

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