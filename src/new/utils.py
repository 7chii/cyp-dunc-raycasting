import assets.game_items as game_items
def player_collides_enemy(player, enemy, radius=0.2):
    if hasattr(enemy, 'is_peaceful') and enemy.is_peaceful:
        return False
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    return dx*dx + dy*dy < radius*radius

def player_collides_shop(player, grid_dict, radius=0.7):
    """Retorna o nome da loja se o jogador encostar em uma, senão None"""
    SHOP_TILES = game_items.SHOP_NAMES
    px, py = int(player.x), int(player.y)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(0,0)]:
        nx, ny = px + dx, py + dy
        tile = grid_dict.get((nx, ny))
        if tile in SHOP_TILES:
            # distância real pra evitar falsos positivos
            if (player.x - (nx+0.5))**2 + (player.y - (ny+0.5))**2 < radius**2:
                return SHOP_TILES[tile]
    return None

def find_free_position_with_exit(grid_dict, player_pos):
    max_x = max(x for x, _ in grid_dict.keys()) + 1
    max_y = max(y for _, y in grid_dict.keys()) + 1
    px, py = int(player_pos.x), int(player_pos.y)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = px + dx, py + dy
        if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
            return nx+0.5, ny+0.5
    return px+0.5, py+0.5