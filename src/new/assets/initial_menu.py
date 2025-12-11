import json
import pygame as pg
import os
from respath import resource_path

SAVE_DIR = os.path.join(os.getenv("APPDATA"), "CypRaycastingSave")

os.makedirs(SAVE_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(SAVE_DIR, "data.json")

def delete_save_slot(slot_name: str) -> bool:
    """
    Apaga um slot esp do arquivo de saves.
    Retorna true se foi apagado com sucesso, false se o slot n exista.
    """
    saves = load_all_saves()

    if slot_name not in saves:
        return False 

    del saves[slot_name]  
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
    """Carrega dados crus do save (dicts)"""
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
    """Salva dados no arquivo"""
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
