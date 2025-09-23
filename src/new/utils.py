def player_collides_enemy(player, enemy, radius=0.2):
    if hasattr(enemy, 'is_peaceful') and enemy.is_peaceful:
        return False
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    return dx*dx + dy*dy < radius*radius

def find_free_position_with_exit(grid_dict, player_pos):
    max_x = max(x for x, _ in grid_dict.keys()) + 1
    max_y = max(y for _, y in grid_dict.keys()) + 1
    px, py = int(player_pos.x), int(player_pos.y)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = px + dx, py + dy
        if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
            return nx+0.5, ny+0.5
    return px+0.5, py+0.5