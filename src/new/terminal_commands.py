
import assets.game_objects as game_objects
import assets.game_items as game_items
import assets.initial_menu as initial_menu
import minigames 
import dinamic.item_dinamic as item_dinamic
import pygame as pg

def handle_terminal_commands(screen, enemies, player, terminal, events, dropped_items, black_screen, collided_enemy, grid, level):
    """
    lida com os comandos do terminal (apertar TAB ou combate) e retorna
    os estados atualizados de black_screen e collided_enemy
    """

    def terminal_loading(terminal, screen, label="loading", steps=6, delay=100):
        """
        animacaozinha do terminal
        """
        terminal.messages.append(f"{label} [{'·' * steps}]")

        for i in range(steps + 1):
            filled = "=" * i
            empty = " " * (steps - i)
            bar = f"[{filled}{empty}]"
            terminal.messages[-1] = f"{label} {bar}"
            screen.fill((0, 0, 0))  
            terminal.draw(screen)

            pg.display.flip()
            pg.time.delay(delay)
        terminal.messages.append("loading complete.")
        

    def terminal_command_callback(command):
        import random
        nonlocal black_screen
        nonlocal collided_enemy
        
        def enemy_turn():
            if collided_enemy and collided_enemy in enemies and collided_enemy.hp > 1:
                if(collided_enemy.is_stunned):
                    terminal.messages.append(
                        f"{collided_enemy.name} is stunned."
                    )
                    collided_enemy.is_stunned = False
                    return black_screen, collided_enemy
                else:
                    terminal_loading(terminal, screen, label="loading action")

                    import random
                    # pega dano base da arma
                    dmg, chance_to_hit, stun_chance, force_unequip  = collided_enemy.get_damage()

                    # verifica se errou
                    if random.random() < chance_to_hit:
                        terminal.messages.append(
                            f"{collided_enemy.name} tried to attack you with {collided_enemy.weapon}! They missed."
                        )
                    else:
                        # aplica stun
                        if random.random() < stun_chance:
                            terminal.messages.append(f"{collided_enemy.name} stunned you! You lose your next turn!")
                            player.is_stunned = True

                        # aplica force unequip
                        if random.random() < (force_unequip - player.unequip_resist):  # force_unequip é decimal vindo do parse_weapon_grades
                            if player.right_hand or player.left_hand:
                                terminal.messages.append(f"{collided_enemy.name}'s attack threw you to the ground!")
                                player.right_hand = None
                                player.left_hand = None

                        # aplica dano
                        player.hp -= dmg
                        terminal.messages.append(
                            f"{collided_enemy.name} attacked you with {collided_enemy.weapon}! (-{dmg} HP). Your HP: {player.hp}"
                        )

                    if player.hp <= 0:
                        terminal.messages.append("You died! Game Over.")
                        import pygame as pg
                        pg.quit()
                        exit()


        if black_screen and collided_enemy:
            if player.is_stunned:
                terminal.messages.append("You are stunned and lose your turn!")
                enemy_turn()
                player.is_stunned = False
                return black_screen, collided_enemy

            # comandos durante combate
            if command["type"] == "attack":
                if collided_enemy and command["target"] == collided_enemy.name:
                    terminal_loading(terminal, screen, label="loading attack")
                    dmg, chance_to_hit, stun_chance, force_unequip, weapon  = player.get_damage(command["hand"])

                    # verifica se errou
                    if random.random() < chance_to_hit + player.chance:
                        terminal.messages.append(
                            f"{collided_enemy.name} received 0 dmg from {command['hand']} handed weapon! You missed! enemy HP: {collided_enemy.hp}"
                        )
                    else:
                        # aplica stun
                        if random.random() < stun_chance:
                            terminal.messages.append(f"Your attack left {collided_enemy.name} stunned!")
                            collided_enemy.is_stunned = True

                        # aplica force unequip
                        if random.random() < (force_unequip - collided_enemy.unequip_resist):
                            if collided_enemy.weapon:
                                terminal.messages.append(f"You threw {collided_enemy.name} weapon {collided_enemy.weapon} far away!")
                                collided_enemy.weapon = None

                        else:
                            collided_enemy.hp = max(1, collided_enemy.hp - dmg)
                            terminal.messages.append(
                                f"{collided_enemy.name} received {dmg} dmg from {command['hand']} handed weapon: {weapon}! enemy HP: {collided_enemy.hp}"
                            )
                    enemy_turn()  # turno do inimigo acontece normalmente
                else:
                    terminal.messages.append(
                        f"ERROR: You can only attack the enemy currently in combat ({collided_enemy.name if collided_enemy else 'nenhum'})!"
                    )

            if command["type"] == "hack":
                if collided_enemy and collided_enemy.name == command["target"]:
                    terminal_loading(terminal, screen, label="loading hack")
                    
                    success = minigames.run_minigames(screen, terminal)

                    if success:
                        terminal.messages.append("hacking complete")
                        terminal.messages.append(
                            f"{collided_enemy.name} received {collided_enemy.hp} dmg from hacking! enemy HP: 1"
                        )
                        collided_enemy.hp = 1
                    else:
                        player.hp -= 3
                        terminal.messages.append(f"ERROR: HACKING FAILED (-3 HP) Current HP:{player.hp}")
                        enemy_turn()
                else:
                    terminal.messages.append(
                        f"ERROR: You can only hack the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                    )
            if command["type"] == "scan":
                #print(f"{collided_enemy.name}, {command['target']}")
                if collided_enemy and collided_enemy.name == command["target"]:
                    terminal_loading(terminal, screen, label="loading scan")
                    terminal.messages.append(
                            f"{collided_enemy.name} holds {collided_enemy.weapon}"
                    )
                else:
                    terminal.messages.append(
                        f"ERROR: You can only scan the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                    )
            elif command["type"] == "install_prosthesis":
                    terminal.messages.append(
                        f"You cannot install during combat."
                    )
            elif command["type"] == "status":
                terminal.messages.append(player.get_status())
            elif command["type"] == "save":
                terminal.messages.append("ERROR: cannot save mid combat!")
                enemy_turn()
            elif command["type"] == "pickup":
                item = command["item"]
                picked = None
                for drop in dropped_items:
                    dx = player.x - drop[0]
                    dy = player.y - drop[1]
                    if dx * dx + dy * dy < 1.0 and drop[2] == item:
                        picked = drop
                        break

                if picked:
                    # se já tem o item, aumenta a quantidade
                    if item in player.inventory:
                        player.inventory[item] += 1
                    else:
                        player.inventory[item] = 1
                    dropped_items.remove(picked)
                    terminal.messages.append(f"You picked up {item} and added it to your inventory.")
                else:
                    terminal.messages.append(f"No {item} nearby to pick up.")

            elif command["type"] == "inventory_list":
                if player.inventory:
                    items = ", ".join([f"{name} x{qty}" for name, qty in player.inventory.items()])
                    terminal.messages.append(f"{items}")
                    game_objects.generate_item_keywords(player.inventory, dropped_items)
                else:
                    terminal.messages.append("Inventory is empty.")

            elif command["type"] == "equipment_list":
                right = player.right_hand if player.right_hand else "empty"
                left = player.left_hand if player.left_hand else "empty"
                terminal.messages.append(f"Right hand: {right}, Left hand: {left}")
                game_objects.generate_item_keywords(player.inventory, dropped_items)
            elif command["type"] == "use":
                msg = player.use_item(command["item"])
                terminal.messages.append(msg)
            elif command["type"] == "equip":
                item_full = command["item"]  # ex: "generic-knife-Σ"
                
                # extrai item base sem grades
                item_parts = item_full.split("-")
                if item_parts[0] in game_items.item_companies:
                    item_type = item_parts[1]
                else:
                    item_type = item_parts[0]

                if item_full not in player.inventory:
                    terminal.messages.append(f"You don’t have {item_full} in your inventory!")
                elif item_type not in game_items.equipable_items_hand:
                    terminal.messages.append(f"{item_type} cannot be equipped!")
                else:
                    if command["hand"] == "right":
                        if player.left_hand == item_full:
                            player.left_hand = None
                        player.right_hand = item_full
                    elif command["hand"] == "left":
                        if player.right_hand == item_full:
                            player.right_hand = None
                        player.left_hand = item_full
                    terminal.messages.append(f"You equipped {item_full} on your {command['hand']} hand.")

                enemy_turn()

            elif command["type"] == "remove":
                if collided_enemy and command["target"] == collided_enemy.name:
                    if collided_enemy.hp == 1:
                        if collided_enemy.weapon:
                            dropped_items.append((collided_enemy.x, collided_enemy.y, collided_enemy.weapon))
                            terminal.messages.append(
                                f"{collided_enemy.name} died and dropped {collided_enemy.weapon} on the ground!"
                            )
                            drop = random.choice(list(game_items.usable_items) + [None])  # 50/50
                            if drop:
                                drop_item = item_dinamic.generate_item(drop, level)
                                drop_name = drop_item['name']
                                dropped_items.append((collided_enemy.x, collided_enemy.y, drop_name))
                                terminal.messages.append(f"{collided_enemy.name} also dropped {drop_name}!")
                        game_objects.generate_item_keywords(player.inventory, dropped_items)
                        enemies.remove(collided_enemy)
                        terminal.messages.append(f"{collided_enemy.name} was removed!")
                        terminal.text = ""
                    else:
                        terminal.messages.append(
                            f"{collided_enemy.name} cannot be removed! Current HP: {collided_enemy.hp}"
                        )
                else:
                    terminal.messages.append(
                        f"ERROR: You can only remove the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                    )

            elif command["type"] == "spare":
                if collided_enemy and command["target"] == collided_enemy.name:
                    if collided_enemy.hp == 1:
                        if collided_enemy.weapon:
                            dropped_items.append((collided_enemy.x, collided_enemy.y, collided_enemy.weapon))
                            terminal.messages.append(
                                f"{collided_enemy.name} dropped {collided_enemy.weapon} on the ground!"
                            )
                        spared = game_objects.SparedEnemy((collided_enemy.x, collided_enemy.y), name=collided_enemy.name)
                        enemies[enemies.index(collided_enemy)] = spared
                        terminal.messages.append(f"{collided_enemy.name} has been spared and is now peaceful!")
                        drop = random.choice(list(game_items.usable_items) + [None])  # 50/50
                        if drop:
                            drop_item = item_dinamic.generate_item(drop, level)
                            drop_name = drop_item['name']
                            dropped_items.append((collided_enemy.x, collided_enemy.y, drop_name))
                            terminal.messages.append(f"{collided_enemy.name} also dropped {drop_name}!")
                        game_objects.generate_item_keywords(player.inventory, dropped_items)
                        collided_enemy = spared
                        spared.is_peaceful = True
                        terminal.text = ""
                    else:
                        terminal.messages.append(
                            f"{collided_enemy.name} cannot be spared! Current HP: {collided_enemy.hp}"
                        )
                else:
                    terminal.messages.append(
                        f"ERROR: You can only spare the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                    )


            elif command["type"] == "runaway":
                if collided_enemy and collided_enemy.hp > 1:
                    import random
                    if random.random() < 0.5:
                        terminal.messages.append(
                            f"You tried running from {collided_enemy.name}, with no avail!"
                        )
                        enemy_turn()
                    else:
                        free_x, free_y = find_free_position_with_exit(grid, player.xy)
                        player.x, player.y = free_x, free_y
                        terminal.messages.append(
                            f"You ran away from {collided_enemy.name}!"
                        )
                        black_screen = False
                        collided_enemy = None
                        terminal.text = ""
                else:
                    terminal.messages.append("Combat end.")
                    black_screen = False
                    collided_enemy = None
                    terminal.text = ""

            elif command["type"] == "exit":
                if collided_enemy and collided_enemy.hp > 1:
                    terminal.messages.append(f"ERRO: {collided_enemy.name} still stands!")
                else:
                    terminal.messages.append("Combat end.")
                    black_screen = False
                    collided_enemy = None
                    terminal.text = ""
        else:
            # comandos gerais (fora de combate)
            if command["type"] == "attack":
                        terminal.messages.append(
                            f"ERROR: You can only attack an enemy in combat (none)!"
                        )
            elif command["type"] == "hack":
                    terminal.messages.append(
                        f"ERROR: You can only hack the enemy currently in combat (none)!"
                    )
            if command["type"] == "scan":
                    terminal.messages.append(
                        f"ERROR: You can only scan the enemy currently in combat (none)!"
                    )
            if command["type"] == "install_prosthesis":
                    msg = player.install_prosthesis(command['prosthesis'])
                    terminal.messages.append(
                        f"{msg}"
                    )
            if command["type"] == "status":
                terminal.messages.append(player.get_status())
                
            if command["type"] == "save":
                # tenta achar o slot já existente pelo par (playerName, terminalName)
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

            elif command["type"] == "pickup":
                item = command["item"]
                picked = None
                for drop in dropped_items:
                    dx = player.x - drop[0]
                    dy = player.y - drop[1]
                    if dx * dx + dy * dy < 4.0 and drop[2] == item:
                        picked = drop
                        break

                if picked:
                    # se já tem o item, aumenta a quantidade
                    if item in player.inventory:
                        player.inventory[item] += 1
                    else:
                        player.inventory[item] = 1
                    dropped_items.remove(picked)
                    terminal.messages.append(f"You picked up {item} and added it to your inventory.")
                else:
                    terminal.messages.append(f"No {item} nearby to pick up.")

            elif command["type"] == "inventory_list":
                if player.inventory:
                    items = ", ".join([f"{name} x{qty}" for name, qty in player.inventory.items()])
                    terminal.messages.append(f"{items}")
                    game_objects.generate_item_keywords(player.inventory, dropped_items)
                else:
                    terminal.messages.append("Inventory is empty.")


            elif command["type"] == "equipment_list":
                right = player.right_hand if player.right_hand else "empty"
                left = player.left_hand if player.left_hand else "empty"
                terminal.messages.append(f"Right hand: {right}, Left hand: {left}")
                game_objects.generate_item_keywords(player.inventory, dropped_items)
            elif command["type"] == "equip":
                item_full = command["item"]  # ex: "generic-knife-Σ"
                
                # extrai item base sem grades
                item_parts = item_full.split("-")
                if item_parts[0] in game_items.item_companies:
                    item_type = item_parts[1]
                else:
                    item_type = item_parts[0]

                if item_full not in player.inventory:
                    terminal.messages.append(f"You don’t have {item_full} in your inventory!")
                elif item_type not in game_items.equipable_items_hand:
                    terminal.messages.append(f"{item_type} cannot be equipped!")
                else:
                    if command["hand"] == "right":
                        if player.left_hand == item_full:
                            player.left_hand = None
                        player.right_hand = item_full
                    elif command["hand"] == "left":
                        if player.right_hand == item_full:
                            player.right_hand = None
                        player.left_hand = item_full
                    terminal.messages.append(f"You equipped {item_full} on your {command['hand']} hand.")

            elif command["type"] == "use":
                msg = player.use_item(command["item"])
                terminal.messages.append(msg)
            elif command["type"] == "remove":
                    terminal.messages.append(
                        f"ERROR: You can only remove the enemy currently in combat (none)!"
                    )
            elif command["type"] == "spare":
                    terminal.messages.append(
                        f"ERROR: You can only spare the enemy currently in combat (none)!"
                    )

            elif command["type"] == "runaway":
                terminal.messages.append(
                        f"ERROR: there is nothing to run away from!"
                    )
            elif command["type"] == "exit":
                terminal.messages.append(
                        f"ERROR: there is no combat!"
                    )
    def terminal_error_callback(cmd_text):
        terminal.messages.append(f'ERROR: Command "{cmd_text}" not recognized!')

    terminal.handle_event(events, command_callback=terminal_command_callback, error_callback=terminal_error_callback)
    terminal.draw(screen)
    pg.display.flip()
    return black_screen, collided_enemy

def find_free_position_with_exit(grid_dict, player_pos):
        max_x = max(x for x, _ in grid_dict.keys()) + 1
        max_y = max(y for _, y in grid_dict.keys()) + 1
        px, py = int(player_pos.x), int(player_pos.y)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = px + dx, py + dy
            if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
                return nx + 0.5, ny + 0.5
        return px + 0.5, py + 0.5

def fix_char_position(grid_dict, player_pos):
    from collections import deque
    max_x = max(x for x, _ in grid_dict.keys()) + 1
    max_y = max(y for _, y in grid_dict.keys()) + 1
    px, py = int(player_pos.x), int(player_pos.y)

    visited = set()
    queue = deque([(px, py)])

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))

        # achou espaço livre
        if 0 <= x < max_x and 0 <= y < max_y and grid_dict.get((x, y), 1) == 0:
            return x + 0.5, y + 0.5

        # expande vizinhos
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited and 0 <= nx < max_x and 0 <= ny < max_y:
                queue.append((nx, ny))

    # fallback: retorna a pos original se não achar nada
    return px + 0.5, py + 0.5
