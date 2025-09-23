import random
import assets.game_objects as game_objects
import minigames 
import pygame as pg

def handle_terminal_commands(screen, enemies, player, terminal, events, dropped_items, black_screen, collided_enemy, grid):
    """
    lida com os comandos do terminal (apertar TAB ou combate) e retorna
    os estados atualizados de black_screen e collided_enemy
    """
    def find_free_position_with_exit(grid_dict, player_pos):
        max_x = max(x for x, _ in grid_dict.keys()) + 1
        max_y = max(y for _, y in grid_dict.keys()) + 1
        px, py = int(player_pos.x), int(player_pos.y)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = px + dx, py + dy
            if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
                return nx + 0.5, ny + 0.5
        return px + 0.5, py + 0.5

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

            # limpa a tela antes de desenhar
            screen.fill((0, 0, 0))  
            terminal.draw(screen)

            pg.display.flip()
            pg.time.delay(delay)


    def terminal_command_callback(command):
        nonlocal black_screen
        nonlocal collided_enemy
        def enemy_turn():
            if collided_enemy and collided_enemy in enemies and collided_enemy.hp > 1:
                terminal_loading(terminal, screen, label="loading action")
                dano = collided_enemy.get_damage()
                player.hp -= dano
                terminal.messages.append(
                    f"{collided_enemy.name} attacked you with {collided_enemy.weapon}! (-{dano} HP). Your HP: {player.hp}"
                )
                if player.hp <= 0:
                    terminal.messages.append("You died! Game Over.")
                    import pygame as pg
                    pg.quit()
                    exit()

        if black_screen and collided_enemy:
            # comandos durante combate
            if command["type"] == "attack":
                    if collided_enemy and command["target"] == collided_enemy.name:
                        terminal_loading(terminal, screen, label="loading attack")
                        dano = player.get_damage(command["hand"])
                        collided_enemy.hp = max(1, collided_enemy.hp - dano)
                        terminal.messages.append(
                            f"{collided_enemy.name} received {dano} dmg from {command['hand']} hand! enemy HP: {collided_enemy.hp}"
                        )
                        enemy_turn()
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
                        if collided_enemy and collided_enemy in enemies and collided_enemy.hp > 1:
                            dano = collided_enemy.get_damage()
                            player.hp -= dano
                            terminal.messages.append(
                                f"{collided_enemy.name} attacked you with {collided_enemy.weapon}! (-{dano} HP). Your HP: {player.hp}"
                            )
                            if player.hp <= 0:
                                terminal.messages.append("You died! Game Over.")
                                pg.quit()
                                exit()
                else:
                    terminal.messages.append(
                        f"ERROR: You can only hack the enemy currently in combat ({collided_enemy.name if collided_enemy else 'none'})!"
                    )
            elif command["type"] == "pickup":
                item = command["item"]
                picked = None
                for drop in dropped_items:
                    dx = player.x - drop[0]
                    dy = player.y - drop[1]
                    if dx*dx + dy*dy < 1.0 and drop[2] == item:
                        picked = drop
                        break

                if picked:
                    player.inventory.append(item)
                    dropped_items.remove(picked)
                    terminal.messages.append(f"You picked up {item} and added it to your inventory.")
                else:
                    terminal.messages.append(f"No {item} nearby to pick up.")
            elif command["type"] == "inventory_list":
                if player.inventory:
                    items = ", ".join(player.inventory)
                    terminal.messages.append(f"Inventory: {items}")
                else:
                    terminal.messages.append("Inventory is empty.")

            elif command["type"] == "equipment_list":
                right = player.right_hand if player.right_hand else "empty"
                left = player.left_hand if player.left_hand else "empty"
                terminal.messages.append(f"Right hand: {right}, Left hand: {left}")
            elif command["type"] == "use":
                msg = player.use_item(command["item"])
                terminal.messages.append(msg)
            elif command["type"] == "equip":
                if command["item"] not in player.inventory:
                    terminal.messages.append(f"You don’t have {command['item']} in your inventory!")
                else:
                    if command["hand"] == "right":
                        player.right_hand = command["item"]
                    elif command["hand"] == "left":
                        player.left_hand = command["item"]
                    terminal.messages.append(f"You equipped {command['item']} on your {command['hand']} hand.")
                enemy_turn()

            elif command["type"] == "remove":
                if collided_enemy and command["target"] == collided_enemy.name:
                    if collided_enemy.hp == 1:
                        if collided_enemy.weapon:
                            dropped_items.append((collided_enemy.x, collided_enemy.y, collided_enemy.weapon))
                            terminal.messages.append(
                                f"{collided_enemy.name} died and dropped {collided_enemy.weapon} on the ground!"
                            )
                        enemies.remove(collided_enemy)
                        terminal.messages.append(f"{collided_enemy.name} was removed!")
                        collided_enemy = None
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
                        collided_enemy = spared
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
            elif command["type"] == "pickup":
                item = command["item"]
                picked = None
                for drop in dropped_items:
                    dx = player.x - drop[0]
                    dy = player.y - drop[1]
                    if dx*dx + dy*dy < 1.0 and drop[2] == item:
                        picked = drop
                        break

                if picked:
                    player.inventory.append(item)
                    dropped_items.remove(picked)
                    terminal.messages.append(f"You picked up {item} and added it to your inventory.")
                else:
                    terminal.messages.append(f"No {item} nearby to pick up.")
            elif command["type"] == "inventory_list":
                if player.inventory:
                    terminal.messages.append("Inventory:")
                    max_per_line = 5  # numero de itens por linha
                    for i in range(0, len(player.inventory), max_per_line):
                        line = ", ".join(player.inventory[i:i+max_per_line])
                        terminal.messages.append("  " + line)
                else:
                    terminal.messages.append("Inventory is empty.")


            elif command["type"] == "equipment_list":
                right = player.right_hand if player.right_hand else "empty"
                left = player.left_hand if player.left_hand else "empty"
                terminal.messages.append(f"Right hand: {right}, Left hand: {left}")
            elif command["type"] == "equip":
                if command["item"] not in player.inventory:
                    terminal.messages.append(f"You don’t have {command['item']} in your inventory!")
                else:
                    if command["hand"] == "right":
                        player.right_hand = command["item"]
                    elif command["hand"] == "left":
                        player.left_hand = command["item"]
                    terminal.messages.append(f"You equipped {command['item']} on your {command['hand']} hand.")

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
