import pygame as pg
import time
import random
import constmath.constants as constants
import assets.game_objects as game_objects
import dinamic.dinamic as dinamic
import assets.grid as grid_starter

import terminal_commands as terminal_commands
import rendering as rendering 
from events import handle_events
from utils import player_collides_enemy, find_free_position_with_exit
level = 0
def main() -> None:
    player = game_objects.Player((3, 10))
    def generate_level():
        global level
        GRID = grid_starter.start_grid()
        level += 1
        #level = 49
        grid_dict = {}
        for x, row in enumerate(GRID):
            for y, element in enumerate(row):
                grid_dict[(x, y)] = element
        enemies = dinamic.generate_enemies_distributed(level +1, grid_dict, level)
        player.x, player.y = terminal_commands.fix_char_position(grid_dict, player.xy)
        return GRID, grid_dict, enemies, level
    
    #grid = game_objects.Grid
    #enemies = dinamic.generate_enemies_distributed(10, grid)
    GRID, grid, enemies, level = generate_level()
    dropped_items = []
    pg.init()
    font = font = pg.font.SysFont("Courier New", 23)
    clock = pg.time.Clock()
    width, height = constants.SIZE
    terminal = game_objects.Terminal(font, width, height, "nana", "twinkpad")
    half_w, half_h = width // 2, height // 2
    screen = pg.display.set_mode((width, height))
    background_surface = rendering.pre_render_background(font, width, height)

    black_screen = False
    collided_enemy = None
    tab_pressed = False
    see_through = False
    exit_pos = None

    running = True
    while running:
        dt = clock.tick(constants.FPS)/1000.0
        if player.update_buffs(dt):
            terminal.messages.append("WARN: buff ended")
        running, events, tab_pressed, see_through, blocked= handle_events(black_screen, tab_pressed, running, player, enemies, see_through)
        if not running:
            break
        
        if tab_pressed or black_screen:
            screen.fill((0, 0, 0))
            black_screen, collided_enemy = terminal_commands.handle_terminal_commands(
                screen, enemies, player, terminal, events, dropped_items,
                black_screen, collided_enemy, grid, level
            )
            continue
        
        hit = None
        for enemy in enemies:
            if player_collides_enemy(player, enemy):
                hit = enemy
                break
        
        if hit:
            black_screen = True
            collided_enemy = hit
            terminal.keywords = game_objects.get_key_words(collided_enemy)
            terminal.messages.append(f"name: {hit.name} HP: {hit.hp}")
            if hit.chance >= 0.6:
                terminal.messages.append(f"{hit.name} seems unlucky!")
            pg.display.flip()
            continue
        all_spared = allspared(enemies)
        if not enemies or all_spared:
            if(exit_pos == None):
                exit_pos = dinamic.add_exit_door(grid)
            px, py = int(player.x), int(player.y)
            ex, ey = exit_pos
            if "you have cleared this level! find the stairs" not in terminal.messages:
                terminal.messages.append("you have cleared this level! find the stairs")
            # Supondo que `exit_pos = (x, y)` retornado de add_exit_door(grid)

            # verifica se o jogador encostou na porta
            if abs(px - ex) + abs(py - ey) == 1:
                # carrega próximo nível
                GRID, grid, enemies, level = generate_level()
                dropped_items = []
                player.x, player.y = 3, 10
            

        
        rendering.clear_screen(screen)
        rendering.draw_floor_and_ceiling_ascii(screen, background_surface)

        # raycasting e objetos
        step = 1
        rendering.cast_rays_ascii(screen, player.xy, player.direction, player.plane, grid, width, height, font, step, see_through)
        rendering.draw_items_ascii(screen, player, dropped_items, grid, width, height, font, see_through)
        rendering.draw_enemies_ascii(screen, player, enemies, grid, width, height, font, see_through)

        # HUD
        rendering.draw_level_number(screen, font, level, width-100)
        rendering.draw_fps(screen, font, clock, half_w)

        pg.display.flip()

def allspared(enemies):
        if not enemies:
            return True
        return all(getattr(enemy, "is_peaceful", False) for enemy in enemies)
    

if __name__ == "__main__":
    main()