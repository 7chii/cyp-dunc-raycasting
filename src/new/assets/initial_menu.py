import json
import pygame as pg
import os

if os.name == "nt":
    CONFIG_FILE = "src/new/state/data.json"
else:
    CONFIG_FILE = "state/data.json"

def delete_save_slot(slot_name: str) -> bool:
    """
    Apaga um slot específico do arquivo de saves.
    Retorna True se foi apagado com sucesso, False se o slot não existia.
    """
    saves = load_all_saves()

    if slot_name not in saves:
        return False  # slot não existe

    del saves[slot_name]  # remove o slot
    with open(CONFIG_FILE, "w") as f:
        json.dump(saves, f, indent=4)

    return True


def get_next_slot():
    saves = load_all_saves()
    if not saves:
        return "slot1"
    
    numbers = []
    for key in saves.keys():
        if key.startswith("slot"):
            try:
                n = int(key[4:])
                numbers.append(n)
            except:
                pass
    next_num = max(numbers) + 1 if numbers else 1
    return f"slot{next_num}"

def load_all_saves():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def load_player_data_from_slot(slot: str) -> dict | None:
    """Carrega dados crus do save (dicts), sem instanciar Player"""
    saves = load_all_saves()
    if slot not in saves:
        return None

    pdata = saves[slot].get("playerData", {})
    idata = saves[slot].get("itemsData", {})
    config = saves[slot].get("config", {})
    level = saves[slot].get("levelData", {})

    return {
        "playerData": pdata,
        "itemsData": idata,
        "config": config,
        "levelData": level
    }


def save_slot_data(slot, player_data, items_data, player_name, terminal_name, level):
    """Salva apenas dados primitivos no arquivo, sem precisar importar Player"""
    data = load_all_saves()
    data[slot] = {
        "playerData": player_data,
        "itemsData": items_data,
        "levelData": {"level":level},
        "config": {
            "playerName": player_name,
            "terminalName": terminal_name
        }
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)



def menu_load_game(screen, font, width, height):
    """Menu para escolher qual save carregar."""
    saves = load_all_saves()
    if not saves:
        return None, None

    slots = sorted(saves.keys())
    selected = 0
    clock = pg.time.Clock()
    running = True

    while running:
        screen.fill((0,0,0))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return None, None
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    selected = (selected - 1) % len(slots)
                elif event.key == pg.K_DOWN:
                    selected = (selected + 1) % len(slots)
                elif event.key == pg.K_RETURN:
                    slot = slots[selected]
                    cfg = saves[slot]["config"]
                    return cfg.get("playerName", "player"), cfg.get("terminalName", "terminal")

        # desenha os saves
        for i, slot in enumerate(slots):
            cfg = saves[slot]["config"]
            name = f"{slot}: {cfg.get('playerName','player')} @ {cfg.get('terminalName','terminal')}"
            color = (0,255,0) if i == selected else (100,100,100)
            txt_surface = font.render(name, True, color)
            screen.blit(txt_surface, (50, 150 + i*60))

        pg.display.flip()
        clock.tick(30)


def menu_initial(screen, font, width, height):
    """Menu inicial: Novo Jogo ou Carregar Jogo."""
    options = ["New game", "Load save"]
    selected = 0
    clock = pg.time.Clock()
    running = True

    while running:
        screen.fill((0,0,0))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return None, None, None
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pg.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pg.K_RETURN:
                    return options[selected], selected, None  # retorna opção escolhida

        # desenha opções
        for i, option in enumerate(options):
            color = (0,255,0) if i == selected else (100,100,100)
            txt_surface = font.render(option, True, color)
            screen.blit(txt_surface, (50, 150 + i*60))

        pg.display.flip()
        clock.tick(30)

def menu_new_game(screen, font, width, height):
    """Menu para digitar playerName e terminalName."""
    input_boxes = ["playerName", "terminalName"]
    input_texts = ["", ""]
    active_index = 0
    prompt_texts = ["Enter Player Name:", "Enter Terminal Name:"]

    clock = pg.time.Clock()
    running = True
    while running:
        screen.fill((0,0,0))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return None, None
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:
                    if active_index < len(input_boxes) - 1:
                        active_index += 1
                    else:
                        # finaliza input
                        return input_texts[0] or "player", input_texts[1] or "terminal"
                elif event.key == pg.K_BACKSPACE:
                    input_texts[active_index] = input_texts[active_index][:-1]
                elif event.unicode:
                    input_texts[active_index] += event.unicode

        # desenha prompts
        for i, prompt in enumerate(prompt_texts):
            color = (0,255,0) if i == active_index else (100,100,100)
            txt_surface = font.render(prompt, True, color)
            screen.blit(txt_surface, (50, 100 + i*80))
            input_surface = font.render(input_texts[i], True, (0,255,0))
            screen.blit(input_surface, (50, 130 + i*80))

        pg.display.flip()
        clock.tick(30)