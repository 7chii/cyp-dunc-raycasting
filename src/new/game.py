import pygame as pg
import time
import random
import constmath.constants as constants
import assets.game_objects as game_objects

import terminal_commands as terminal_commands
import rendering as rendering 
from events import handle_events
from utils import player_collides_enemy, find_free_position_with_exit

def main() -> None:
    player = game_objects.Player((3, 10))
    grid = game_objects.Grid
    enemies = [
        game_objects.Enemy((5.5, 5.5), name="enemy1", hp=12, weapon="knife"),
        game_objects.Enemy((10.5, 8.5), name="enemy2", hp=8, weapon="hammer"),
        game_objects.Enemy((15.5, 12.5), name="enemy3", hp=20, weapon="chainsaw"),
    ]
    dropped_items = []

    pg.init()
    font = font = pg.font.SysFont("Courier New", 18)
    clock = pg.time.Clock()
    width, height = constants.SIZE
    terminal = game_objects.Terminal(font, width, height)
    half_w, half_h = width // 2, height // 2
    screen = pg.display.set_mode((width, height))

    black_screen = False
    collided_enemy = None
    tab_pressed = False

    running = True
    while running:
        dt = clock.tick(constants.FPS)/1000.0
        if player.update_buffs(dt):
            terminal.messages.append("WARN: dmg buff ended")
        running, events, tab_pressed= handle_events(black_screen, tab_pressed, running, player, enemies)
        if not running:
            break
        
        if tab_pressed or black_screen:
            screen.fill((0, 0, 0))
            black_screen, collided_enemy = terminal_commands.handle_terminal_commands(
                screen, enemies, player, terminal, events, dropped_items,
                black_screen, collided_enemy, grid
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
            terminal.messages.append(f"Enemy: {hit.name} HP: {hit.hp}")
            pg.display.flip()
            continue

        rendering.clear_screen(screen)
        rendering.draw_floor(screen, width, height)
        rendering.draw_ceiling(screen, width, height)
        
        
        rendering.cast_rays(screen, player.xy, player.direction, player.plane, grid, width, height)
        rendering.draw_enemies(screen, player, enemies, grid, width, height)
        rendering.draw_text(screen, font, clock, half_w)
        pg.display.flip()

if __name__ == "__main__":
    main()