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
import assets.initial_menu as initial_menu
import json
import os

level = 0
def main() -> None:
    global level
    pg.init()
    pg.mixer.init()
    footstep_sound = pg.mixer.Sound("src/new/assets/audio/footstep.wav")
    terminalbg = pg.mixer.Sound("src/new/assets/audio/terminalbg.wav")
    terminalmsg = pg.mixer.Sound("src/new/assets/audio/terminalmsg.wav")
    
    terminalbg.set_volume(0.1)
    footstep_sound.set_volume(0.3)
    terminalmsg.set_volume(0.3)

    terminalbg_channel = pg.mixer.Channel(1)


    width, height = constants.SIZE
    #base_height = 1000
    #scale_factor = height / base_height  
    #font_size_main = int(23 * scale_factor)
    #font_size_world = int(15 * scale_factor)

    font = pg.font.SysFont("Courier New", 23)
    worldfont = pg.font.SysFont("Courier New", 15)

    if os.name == "nt":  # se for Windows
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
            # Obtém resolução real, ignorando escala do Windows
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
        except Exception:
            # fallback caso falhe
            info = pg.display.Info()
            width, height = info.current_w, info.current_h
    else:
        info = pg.display.Info()
        width, height = info.current_w, info.current_h

    screen = pg.display.set_mode((width, height))


    #info = pg.display.Info()
    #width, height = info.current_w, info.current_h
    #screen = pg.display.set_mode((width, height))
    clock = pg.time.Clock()
    half_w, half_h = width // 2, height // 2

    # Menu inicial
    terminal = game_objects.Terminal(font, width, height, level, "player", "terminal")
    menu = game_objects.TerminalMenu(terminal)
    running = True

    while running and menu.active:
        events = pg.event.get()
        for e in events:
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
            menu.handle_event(e)

        screen.fill((0,0,0))
        menu.draw(screen)
        pg.display.flip()

    if not running:
        return  # usuário fechou a janela

    # ---------------- Inicializa jogador ----------------
    player_name = menu.player_name
    terminal_name = menu.terminal_name

    # tenta carregar save
    slot_to_load = getattr(menu, "selected_slot", None)
    if slot_to_load:
        raw_data = initial_menu.load_player_data_from_slot(slot_to_load)
        if raw_data:
            player, level = build_player_from_data(raw_data)
        else:
            player, level = game_objects.Player((3, 10)), 1
    else:
        player, level = game_objects.Player((3, 10)), 1

    terminal.level = level
    terminal.username = player_name
    terminal.terminal_name = terminal_name
    terminal.update_prompt()

    # ---------------- Função para gerar níveis ----------------
    def generate_level():
        global level
        GRID = grid_starter.start_grid()
        grid_dict = {}
        for x, row in enumerate(GRID):
            for y, element in enumerate(row):
                grid_dict[(x, y)] = element
        terminal.level = level
        enemies = dinamic.generate_enemies_distributed(level +1, grid_dict, level)
        player.x, player.y = terminal_commands.fix_char_position(grid_dict, player.xy)
        return GRID, grid_dict, enemies, level

    GRID, grid, enemies, level = generate_level()
    dropped_items = []

    background_surface = rendering.pre_render_background(font, width, height)

    black_screen = False
    collided_enemy = None
    tab_pressed = False
    see_through = False
    exit_pos = None

    # ---------------- Loop do jogo ----------------
    while running:
        dt = clock.tick(constants.FPS)/1000.0
        if player.update_buffs(dt):
            terminal.messages.append("WARN: buff ended")
        running, events, tab_pressed, see_through, blocked= handle_events(black_screen, tab_pressed, running, player, enemies, see_through, dt, footstep_sound)
        if not running:
            break
        
        if tab_pressed or black_screen:
            # toca o som de terminal se ainda não estiver tocando
            if not terminalbg_channel.get_busy():
                terminalbg_channel.play(terminalbg, loops=-1)  # loops=-1 significa repetir infinito

            screen.fill((0, 0, 0))
            black_screen, collided_enemy = terminal_commands.handle_terminal_commands(
                screen, enemies, player, terminal, events, dropped_items,
                black_screen, collided_enemy, grid, level, terminalmsg
            )
            continue
        else:
            if terminalbg_channel.get_busy():
                terminalbg_channel.stop()


        
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
            if abs(px - ex) + abs(py - ey) == 1:
                GRID, grid, enemies, level = generate_level()
                level +=1
                dropped_items = []
                player.x, player.y = 3, 10
                save_new_level(terminal, player)
                

        rendering.clear_screen(screen)
        rendering.draw_floor_and_ceiling_ascii(screen, background_surface)

        step = 1
        rendering.cast_rays_ascii(screen, player.xy, player.direction, player.plane, grid, width, height, worldfont, step, see_through)
        rendering.draw_items_ascii(screen, player, dropped_items, grid, width, height, font, see_through)
        rendering.draw_enemies_ascii(screen, player, enemies, grid, width, height, font, see_through)

        rendering.draw_level_number(screen, font, level, width-100)
        rendering.draw_fps(screen, font, clock, half_w)

        pg.display.flip()

def allspared(enemies):
        if not enemies:
            return True
        return all(getattr(enemy, "is_peaceful", False) for enemy in enemies)
def save_new_level(terminal, player):
    saves = initial_menu.load_all_saves()
    slot = None
    for key, data in saves.items():
        cfg = data.get("config", {})
        if cfg.get("playerName") == terminal._username and cfg.get("terminalName") == terminal._terminal_name:
            slot = key
            break

    # se não achar, cria um slot novo
    if slot is None:
        slot = initial_menu.get_next_slot()

    # coleta dados crus do player
    player_data = {
        "right_hand": player.right_hand,
        "left_hand": player.left_hand,
        "is_stunned": player.is_stunned,
        "extra_damage": player.extra_damage,
        "chance": player.chance,
        "extra_turns": player.extra_turns,
        "unequip_resist": player.unequip_resist,
        "scan_objects": player.scan_objects,
        "damage_reduction": player.damage_reduction,
        "hack_speed_bonus": player.hack_speed_bonus,
        "hp": player.hp,
        "damage_buff": player.damage_buff,
        "buff_timer": player.buff_timer
    }
    for prost in player.prostheses:
        if hasattr(player, prost):  
            player_data[prost] = getattr(player, prost)


    items_data = {
        "prostheses": player.prostheses,
        "inventory": player.inventory
    }

    
    slotobj = saves.get(f"{slot}", {})
    config = slotobj.get("config", {})
    playername = config.get("playerName", "player")
    terminalname = config.get("terminalName", "terminal")

    # salva no arquivo
    initial_menu.save_slot_data(slot, player_data, items_data, playername, terminalname, level)

    terminal.messages.append(f"save complete to {slot}")
    
def build_player_from_data(raw_data: dict) -> tuple[game_objects.Player, int]:
    """Reconstrói Player a partir de um dict cru vindo do save"""
    player = game_objects.Player((3, 10))

    # aplica atributos simples e dinâmicos
    for attr, val in raw_data.get("playerData", {}).items():
        if hasattr(player, attr):
            setattr(player, attr, val)
        else:
            # cria dinamicamente (ex: slots de prótese)
            setattr(player, attr, val)

    # aplica inventário e próteses
    items = raw_data.get("itemsData", {})
    player.prostheses = items.get("prostheses", [])
    player.inventory = items.get("inventory", {})

    # nível inicial (se não existir, assume 1)
    level_data = raw_data.get("levelData", {})
    level = level_data.get("level", 1)

    return player, level



if __name__ == "__main__":
    main()
