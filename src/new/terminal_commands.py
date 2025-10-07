
import assets.game_objects as game_objects
import assets.game_items as game_items
import assets.initial_menu as initial_menu
import minigames 
import dinamic.item_dinamic as item_dinamic
import pygame as pg
import unicodedata
from collections import deque


def handle_terminal_commands(screen, enemies, player, terminal, events, dropped_items, black_screen, collided_enemy, grid, level, terminalmsg, touching_shop, shop_name, inventory):
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
        

    def terminal_command_callback(commands):
        import random
        nonlocal black_screen
        nonlocal collided_enemy
        nonlocal level

        nonlocal touching_shop
        nonlocal shop_name
        nonlocal inventory
        
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
                        if random.random() < (force_unequip - player.unequip_resist):
                            # lista de todas as mãos + próteses de braço
                            hands_to_check = ["right_hand", "left_hand"]
                            for prost in player.prostheses:
                                base_name = prost
                                if "-" in prost:
                                    parts = prost.split("-")
                                    if parts[0] in game_items.item_companies:
                                        base_name = parts[1]
                                    else:
                                        base_name = parts[0]
                                    base_name = ''.join([c for c in base_name if not c.isdigit()])
                                if base_name == "arm":
                                    hands_to_check.append(prost)

                            # desequipa tudo
                            unequipped_items = []
                            for hand_attr in hands_to_check:
                                if getattr(player, hand_attr, None):
                                    unequipped_items.append(getattr(player, hand_attr))
                                    setattr(player, hand_attr, None)

                            if unequipped_items:
                                items_str = ", ".join(unequipped_items)
                                terminal.messages.append(f"You were disarmed! {collided_enemy.name}'s attack made you drop: {items_str}")
                            else:
                                terminal.messages.append(f"{collided_enemy.name}'s attack tried to disarm you, but you had nothing equipped.")

                        # aplica dano
                        dmg_reduc = player.damage_reduction
                        if(dmg_reduc<=0):
                            dmg_reduc = 1
                        player.hp -= (dmg * dmg_reduc)
                        terminal.messages.append(
                            f"{collided_enemy.name} attacked you with {collided_enemy.weapon}! (-{dmg} HP). Your HP: {player.hp}"
                        )

                    if player.hp <= 0:
                        terminal.messages.append("You died! Game Over.")
                        import pygame as pg
                        pg.quit()
                        exit()

        for command in commands:
            extra_turns = player.extra_turns
            if black_screen and collided_enemy:
                if player.is_stunned:
                    terminal.messages.append("You are stunned and lose your turn!")
                    enemy_turn()
                    player.is_stunned = False
                    extra_turns = 0
                    return black_screen, collided_enemy
                
                # comandos durante combate
                if command["type"] == "attack":
                    if collided_enemy and command["target"] == collided_enemy.name:
                        terminal_loading(terminal, screen, label="loading attack")
                        dmg, chance_to_hit, stun_chance, force_unequip, weapon  = player.get_damage(command["hand"])
                        chance = 0.0
                        dmg += player.extra_damage + player.damage_buff
                        if (chance_to_hit==1.0):
                            chance = chance_to_hit
                        else:
                            chance = player.chance + chance_to_hit
                            if(chance < 0):
                                chance == 0.0
                            if(chance > 1.0):
                                chance == 1.0
                        
                    
                                
                        # verifica se errou
                        if random.random() > chance:
                            terminal.messages.append(
                                f"{collided_enemy.name} received 0 dmg from {command['hand']} handed weapon! You missed! enemy HP: {collided_enemy.hp}"
                            )
                        else:
                            if random.random() < 0.3:
                                collided_enemy.hacked = False
                            if(collided_enemy.hacked == True):
                                dmg *= 2
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
                            extra_turns -= 1
                      
                    else:
                        terminal.messages.append(
                            f"ERROR: You can only attack the enemy currently in combat ({collided_enemy.name if collided_enemy else 'nenhum'})!"
                        )
                    enemy_turn()

                elif command["type"] == "hack":
                    if collided_enemy and collided_enemy.name == command["target"]:
                        terminal_loading(terminal, screen, label="loading hack")
                        off_time = player.hack_speed_bonus
                        success = minigames.run_minigames(screen, terminal, off_time)
                        extra_turns -= 1
                        if collided_enemy.is_boss:
                            dmg = collided_enemy.hp * player.hacking_damage
                        else:
                            dmg = collided_enemy.hp
                        if success:
                            collided_enemy.hp -= dmg
                            if(collided_enemy.hp <= 0):
                                collided_enemy.hp = 1
                            terminal.messages.append("hacking complete")
                            terminal.messages.append(
                                f"{collided_enemy.name} received {dmg} dmg from hacking! enemy HP: {collided_enemy.hp}"
                            )
                            #se menor q % do dano de hacking
                            if random.random() < player.hacking_damage:
                                terminal.messages.append(
                                    f"{collided_enemy.name} has weaknesses! consider attacking!"
                                )
                                collided_enemy.hacked = True
                        else:
                            player.hp -= (player.hp * 0.45)
                            terminal.messages.append(f"ERROR: HACKING FAILED (-45% HP) Current HP:{player.hp}")
                    else:
                        terminal.messages.append(
                            f"ERROR: You can only hack the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                        )
                    enemy_turn()
                
                elif command["type"] == "shop_list":
                    terminal.messages.append("there are no shops nearby.")
                elif command["type"] == "shop_buy":
                    terminal.messages.append("there are no shops nearby.")
                    #outros shops em combate
                elif command["type"] == "scan":
                    if collided_enemy and collided_enemy.name == command["target"]:
                        terminal_loading(terminal, screen, label="loading scan")
                        extra_turns -= 1

                        # sempre mostra a arma
                        terminal.messages.append(
                            f"{collided_enemy.name} holds {collided_enemy.weapon}"
                        )

                        # mostra próteses, limitado ao número de scan_objects do jogador
                        if hasattr(collided_enemy, "prostheses") and collided_enemy.prostheses:
                            max_to_show = player.scan_objects
                            if max_to_show > 0:
                                shown_prostheses = collided_enemy.prostheses[:max_to_show]
                                for prosthetic in shown_prostheses:
                                    terminal.messages.append(
                                        f"{collided_enemy.name} has prosthetic {prosthetic['name']}"
                                    )
                            else:
                                terminal.messages.append(
                                    f"Scanning deeper requires more scan modules..."
                                )
                    else:
                        terminal.messages.append(
                            f"ERROR: You can only scan the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                        )
                    enemy_turn()

                elif command["type"] == "install_prosthesis":
                        terminal.messages.append(
                            f"You cannot install during combat."
                        )
                elif command["type"] == "status":
                    terminal.messages.append(player.get_status())
                elif command["type"] == "save":
                    terminal.messages.append("ERROR: cannot save mid combat!")
                elif command["type"] == "help":
                    terminal.messages.append("Available commands:")
                    terminal.messages.append("  player -a <hand> <enemy>    -> attack with right/left hand")
                    terminal.messages.append("  player -h <enemy>           -> hack enemy")
                    terminal.messages.append("  player -equip <hand> <item or null> -> equip item in hand")
                    terminal.messages.append("  player -use <item>          -> use an item")
                    terminal.messages.append("  player -scan <enemy>        -> scan enemy equipment")
                    terminal.messages.append("  player -install <prosthesis> -> install prosthesis (out of combat)")
                    terminal.messages.append("  player -i ls                -> list inventory")
                    terminal.messages.append("  player -e ls                -> list equipment")
                    terminal.messages.append("  player status               -> show status")
                    terminal.messages.append("  player status save          -> save game")
                    terminal.messages.append("  <enemy> -rm                 -> remove enemy at 1 HP (combat only)")
                    terminal.messages.append("  <enemy> spare               -> spare enemy at 1 HP (combat only)")
                    terminal.messages.append("  <company> ls                -> list items on sale")
                    terminal.messages.append("  <company> buy <item>        -> buy item")
                    terminal.messages.append("  pickup <item>               -> pick up nearby item")
                    terminal.messages.append("  combat runaway              -> try to escape combat")
                    terminal.messages.append("  combat exit                 -> end combat if enemy HP = 1")
                    terminal.messages.append("  to view older commands      -> ↑ / ↓")
                    terminal.messages.append("  to view older msg history   -> pgup / pgdown")
                    terminal.messages.append("  help                        -> show this list")
                    terminal.messages.append("  exit the game               -> esc")

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
                        # mãos
                        right = player.right_hand if player.right_hand else "empty"
                        left = player.left_hand if player.left_hand else "empty"
                        terminal.messages.append(f"Right hand: {right}, Left hand: {left}")
                        if player.prostheses:
                            prost_list = []
                            for attr_name in player.prostheses:
                                prost_item = getattr(player, attr_name, "unknown")
                                if prost_item == None:
                                    prost_item = "empty"
                                prost_list.append(f"{attr_name}: {prost_item}")
                            terminal.messages.append("Prostheses installed: " + ", ".join(prost_list))
                        else:
                            terminal.messages.append("Prostheses installed: None")

                        # gera keywords para inv e itens dropados
                        game_objects.generate_item_keywords(player.inventory, dropped_items)
                elif command["type"] == "use":
                    extra_turns -= 1
                    msg = player.use_item(command["item"])
                    terminal.messages.append(msg)
                    enemy_turn()
                elif command["type"] == "equip":
                    extra_turns -= 1
                    item_full = command["item"]  # ex: "megacorp-chainsaw"
                    item_full = unicodedata.normalize('NFC', item_full)

                    item_parse = False
                    # extrai item base sem grades
                    if not item_full == "null":
                        item_parse = True
                        item_parts = item_full.split("-")
                        if item_parts[0] in game_items.item_companies:
                            item_type = item_parts[1]
                        else:
                            item_type = item_parts[0]
                    inventory_keys = [unicodedata.normalize('NFC', k) for k in player.inventory.keys()]

                    if item_full not in inventory_keys and not item_full == "null":
                        terminal.messages.append(f"You don’t have {item_full} in your inventory!")
                    elif item_parse and item_type not in game_items.equipable_items_hand:
                        terminal.messages.append(f"{item_type} cannot be equipped!")
                    else:
                        hand = command["hand"]
                        valid_hand = False

                        # lista de todas as mãos e próteses arm para checar onde o item está equipado
                        hands_to_check = ["right_hand", "left_hand"]
                        for prost in player.prostheses:
                            base_name = prost
                            if "-" in prost:
                                parts = prost.split("-")
                                if parts[0] in game_items.item_companies:
                                    base_name = parts[1]
                                else:
                                    base_name = parts[0]
                                base_name = ''.join([c for c in base_name if not c.isdigit()])
                            if base_name == "arm":
                                hands_to_check.append(prost)

                        # mapeia hand selecionada para atributo correto
                        if hand in ("right", "left"):
                            valid_hand = True
                            hand_attr = hand + "_hand"
                        elif hand in player.prostheses:
                            base_name = hand
                            if "-" in hand:
                                parts = hand.split("-")
                                if parts[0] in game_items.item_companies:
                                    base_name = parts[1]
                                else:
                                    base_name = parts[0]
                                base_name = ''.join([c for c in base_name if not c.isdigit()])
                            if base_name == "arm":
                                valid_hand = True
                                hand_attr = hand
                        else:
                            hand_attr = None

                        if valid_hand:
                            if item_full == "null":
                                # desequipar
                                setattr(player, hand_attr, None)
                                terminal.messages.append(f"You desequipped the item from your {hand}.")
                            else:
                                # conta quantas vezes o item já está equipado
                                equipped_count = sum(1 for h in hands_to_check if getattr(player, h, None) == item_full)
                                max_count = player.inventory.get(item_full, 0)
                                
                                if equipped_count >= max_count:
                                    terminal.messages.append(f"You already have all {max_count} {item_full} equipped!")
                                else:
                                    # remove o item de qualquer mão/protese onde ele já está (opcional: só se quiser limitar 1 por slot)
                                    # for h in hands_to_check:
                                    #     if getattr(player, h, None) == item_full:
                                    #         setattr(player, h, None)

                                    # equipa na mão/protese selecionada
                                    setattr(player, hand_attr, item_full)
                                    target_name = "" if hand_attr in ("right_hand", "left_hand") else "prosthesis"
                                    terminal.messages.append(f"You equipped {item_full} on your {hand} {target_name}.")
                                enemy_turn()
                        else:
                            terminal.messages.append(f"{hand} is not a valid hand or prosthesis.")

                    

                elif command["type"] == "remove":
                    if collided_enemy and command["target"] == collided_enemy.name:
                        if collided_enemy.hp == 1:
                            if collided_enemy.weapon:
                                dropped_items.append((collided_enemy.x, collided_enemy.y, collided_enemy.weapon))
                                terminal.messages.append(
                                    f"{collided_enemy.name} died and dropped {collided_enemy.weapon} on the ground!"
                                )
                                if hasattr(collided_enemy, "prostheses"):
                                    for prosthetic in collided_enemy.prostheses:
                                        drop_name = prosthetic["name"]
                                        dropped_items.append((collided_enemy.x, collided_enemy.y, drop_name))
                                        terminal.messages.append(
                                            f"{collided_enemy.name} dropped prosthetic {drop_name}!"
                                        )
                                drop = random.choice(list(game_items.usable_items) + [None])  # 50/50
                                if drop:
                                    drop_item = item_dinamic.generate_item(drop, level)
                                    drop_name = drop_item['name']
                                    dropped_items.append((collided_enemy.x, collided_enemy.y, drop_name))
                                    terminal.messages.append(f"{collided_enemy.name} also dropped {drop_name}!")
                            kredits = int(150 * (1 + 0.1 * level))
                            player.kredits = getattr(player, "kredits", 0) + kredits
                            terminal.messages.append(f"{collided_enemy.name} dropped {kredits} kredits!")

                            game_objects.generate_item_keywords(player.inventory, dropped_items)
                            game_objects.remove_keyword(collided_enemy.name)
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
                            if hasattr(collided_enemy, "prostheses"):
                                    for prosthetic in collided_enemy.prostheses:
                                        drop_name = prosthetic["name"]
                                        dropped_items.append((collided_enemy.x, collided_enemy.y, drop_name))
                                        terminal.messages.append(
                                            f"{collided_enemy.name} dropped prosthetic {drop_name}!"
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
                            kredits = int(150 * (1 + 0.1 * level))
                            player.kredits = getattr(player, "kredits", 0) + kredits
                            terminal.messages.append(f"{collided_enemy.name} dropped {kredits} kredits!")
                            game_objects.generate_item_keywords(player.inventory, dropped_items)
                            game_objects.remove_keyword(collided_enemy.name)
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
                elif command["type"] == "unknown":
                        txt = command["raw"]
                        terminal.messages.append(
                                f"ERROR: command {txt} not recognized!"
                            )
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
                    elif command["type"] == "scan":
                            terminal.messages.append(
                                f"ERROR: You can only scan the enemy currently in combat (none)!"
                            )
                    elif command["type"] == "install_prosthesis":
                            msg = player.install_prosthesis(command['prosthesis'])
                            terminal.messages.append(
                                f"{msg}"
                            )
                    elif command["type"] == "shop_list":
                        if (touching_shop):
                            print(shop_name.lower())
                            print(command['shop'])
                            if(command['shop']== shop_name.lower()):
                                inv_type = "prosthetics"
                                if shop_name.lower() == "milbay":
                                    inv_type = "weapons"
                                elif shop_name.lower() == "cafeteria":
                                    inv_type = "items"
                                for item in range(len(inventory[inv_type])):
                                    terminal.messages.append(f"> {inventory[inv_type][item]}")
                                    game_objects.add_keyword(inventory[inv_type][item]['name'])

                            else:
                                terminal.messages.append(f"{command['shop']} is not nearby..")
                        else:
                            terminal.messages.append(f"{command['shop']} is not nearby")
                    
                    elif command["type"] == "shop_buy":
                        if (touching_shop):
                            print(shop_name.lower())
                            print(command['shop'])
                            if(command['shop']== shop_name.lower()):
                                inv_type = "prosthetics"
                                if shop_name.lower() == "milbay":
                                    inv_type = "weapons"
                                elif shop_name.lower() == "cafeteria":
                                    inv_type = "items"
                                item_name = command["item"].lower()
                                if item_name in [i['name'] for i in inventory[inv_type]]:
                                    
                                    item_dict = next((i for i in inventory[inv_type] if i["name"].lower() == item_name), None)
                                    price = item_dict.get("price", 0)
                                    if player.kredits >= price:
                                        inventory[inv_type].remove(item_dict)
                                        if item_name in player.inventory:
                                            player.inventory[item_name] += 1
                                        else:
                                            player.inventory[item_name] = 1

                                        terminal.messages.append(f"you bought {item_name}!")
                                        player.kredits -= price
                                    else:
                                        terminal.messages.append(f"you dont have enough kredits!")
                                else:
                                    terminal.messages.append(f"{item_name} is not available in {shop_name}.")
                            else:
                                terminal.messages.append(f"{command['shop']} is not nearby..")
                        else:
                            terminal.messages.append(f"{command['shop']} is not nearby.")


                    elif command["type"] == "help":
                        terminal.messages.append("Available commands:")
                        terminal.messages.append("  player -a <hand> <enemy>    -> attack with right/left hand")
                        terminal.messages.append("  player -h <enemy>           -> hack enemy")
                        terminal.messages.append("  player -equip <hand> <item or null> -> equip item in hand")
                        terminal.messages.append("  player -use <item>          -> use an item")
                        terminal.messages.append("  player -scan <enemy>        -> scan enemy equipment")
                        terminal.messages.append("  player -install <prosthesis> -> install prosthesis (out of combat)")
                        terminal.messages.append("  player -i ls                -> list inventory")
                        terminal.messages.append("  player -e ls                -> list equipment")
                        terminal.messages.append("  player status               -> show status")
                        terminal.messages.append("  player status save          -> save game")
                        terminal.messages.append("  <enemy> -rm                 -> remove enemy at 1 HP (combat only)")
                        terminal.messages.append("  <enemy> spare               -> spare enemy at 1 HP (combat only)")
                        terminal.messages.append("  <company> ls                -> list items on sale")
                        terminal.messages.append("  <company> buy <item>        -> buy item")
                        terminal.messages.append("  pickup <item>               -> pick up nearby item")
                        terminal.messages.append("  combat runaway              -> try to escape combat")
                        terminal.messages.append("  combat exit                 -> end combat if enemy HP = 1")
                        terminal.messages.append("  to view older commands      -> ↑ / ↓")
                        terminal.messages.append("  to view older msg history   -> pgup / pgdown")
                        terminal.messages.append("  help                        -> show this list")
                        terminal.messages.append("  exit the game               -> esc")

                    elif command["type"] == "status":
                        terminal.messages.append(player.get_status())
                        
                    elif command["type"] == "save":
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
                            "hacking_damage":player.hacking_damage,
                            "hp": player.hp,
                            "damage_buff": player.damage_buff,
                            "buff_timer": player.buff_timer,
                            "kredits":player.kredits
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
                        # mãos
                        right = player.right_hand if player.right_hand else "empty"
                        left = player.left_hand if player.left_hand else "empty"
                        terminal.messages.append(f"Right hand: {right}, Left hand: {left}")
                        if player.prostheses:
                            prost_list = []
                            for attr_name in player.prostheses:
                                prost_item = getattr(player, attr_name, "unknown")
                                if prost_item == None:
                                    prost_item = "empty"
                                prost_list.append(f"{attr_name}: {prost_item}")
                            terminal.messages.append("Prostheses installed: " + ", ".join(prost_list))
                        else:
                            terminal.messages.append("Prostheses installed: None")

                        # gera keywords para inventário/drops
                        game_objects.generate_item_keywords(player.inventory, dropped_items)
                    elif command["type"] == "equip":
                        item_full = command["item"]  # ex: "megacorp-chainsaw"
                        item_full = unicodedata.normalize('NFC', item_full)

                        item_parse = False
                        # extrai item base sem grades
                        if not item_full == "null":
                            item_parse = True
                            item_parts = item_full.split("-")
                            if item_parts[0] in game_items.item_companies:
                                item_type = item_parts[1]
                            else:
                                item_type = item_parts[0]
                        inventory_keys = [unicodedata.normalize('NFC', k) for k in player.inventory.keys()]

                        if item_full not in inventory_keys and not item_full == "null":
                            terminal.messages.append(f"You don’t have {item_full} in your inventory!")
                        elif item_parse and item_type not in game_items.equipable_items_hand:
                            terminal.messages.append(f"{item_type} cannot be equipped!")
                        else:
                            hand = command["hand"]
                            valid_hand = False

                            # lista de todas as mãos e próteses arm para checar onde o item está equipado
                            hands_to_check = ["right_hand", "left_hand"]
                            for prost in player.prostheses:
                                base_name = prost
                                if "-" in prost:
                                    parts = prost.split("-")
                                    if parts[0] in game_items.item_companies:
                                        base_name = parts[1]
                                    else:
                                        base_name = parts[0]
                                    base_name = ''.join([c for c in base_name if not c.isdigit()])
                                if base_name == "arm":
                                    hands_to_check.append(prost)

                            # mapeia hand selecionada para atributo correto
                            if hand in ("right", "left"):
                                valid_hand = True
                                hand_attr = hand + "_hand"
                            elif hand in player.prostheses:
                                base_name = hand
                                if "-" in hand:
                                    parts = hand.split("-")
                                    if parts[0] in game_items.item_companies:
                                        base_name = parts[1]
                                    else:
                                        base_name = parts[0]
                                    base_name = ''.join([c for c in base_name if not c.isdigit()])
                                if base_name == "arm":
                                    valid_hand = True
                                    hand_attr = hand
                            else:
                                hand_attr = None

                            if valid_hand:
                                if item_full == "null":
                                    # desequipar
                                    setattr(player, hand_attr, None)
                                    terminal.messages.append(f"You desequipped the item from your {hand}.")
                                else:
                                    # conta quantas vezes o item já está equipado
                                    equipped_count = sum(1 for h in hands_to_check if getattr(player, h, None) == item_full)
                                    max_count = player.inventory.get(item_full, 0)
                                    
                                    if equipped_count >= max_count:
                                        terminal.messages.append(f"You already have all {max_count} {item_full} equipped!")
                                    else:
                                        # remove o item de qualquer mão/protese onde ele já está (opcional: só se quiser limitar 1 por slot)
                                        # for h in hands_to_check:
                                        #     if getattr(player, h, None) == item_full:
                                        #         setattr(player, h, None)

                                        # equipa na mão/protese selecionada
                                        setattr(player, hand_attr, item_full)
                                        target_name = "" if hand_attr in ("right_hand", "left_hand") else "prosthesis"
                                        terminal.messages.append(f"You equipped {item_full} on your {hand} {target_name}.")
                            else:
                                terminal.messages.append(f"{hand} is not a valid hand or prosthesis.")

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
                    elif command["type"] == "unknown":
                        txt = command["raw"]
                        terminal.messages.append(
                                f"ERROR: command {txt} not recognized!"
                            )
    def terminal_error_callback(cmd_text):
        terminal.messages.append(f'ERROR: Command "{cmd_text}" not recognized!')

    terminal.handle_event(events, player, command_callback=terminal_command_callback, error_callback=terminal_error_callback, terminalmsg=terminalmsg)
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
        if 0 <= x < max_x and 0 <= y < max_y:
            return x + 0.5, y + 0.5

        # expande vizinhos
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited and 0 <= nx < max_x and 0 <= ny < max_y:
                queue.append((nx, ny))

    # fallback: retorna a pos original se não achar nada
    return px + 0.5, py + 0.5