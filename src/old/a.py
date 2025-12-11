import pygame as pg
import game_objects
import numerical
import constants
import functions
import time
import random

tab_pressed = False

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
    font = pg.font.SysFont(pg.font.get_default_font(), 24)
    clock = pg.time.Clock()
    width, height = constants.SIZE
    terminal = game_objects.Terminal(font, width, height)
    half_w, half_h = width // 2, height // 2
    screen = pg.display.set_mode((width, height))

    def run_space_invaders_minigame():
        hack_width = 16
        hack_height = 8
        duration = 15
        player_pos = hack_width // 2
        player_line_idx = hack_height - 1

        enemy_spawn_interval = 0.8
        enemy_speed = 2.0
        bullet_speed = 0.4

        enemies = []
        bullets = []

        messages_backup = terminal.messages.copy()

        start_time = time.time()
        last_enemy_spawn = 0
        enemy_move_accumulator = 0
        mini_clock = pg.time.Clock()

        running = True
        while running:
            dt = mini_clock.tick(30) / 1000
            current_time = time.time()
            elapsed = current_time - start_time

            if elapsed > duration:
                return True

            # Eventos
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()

            # Movimento jogador
            pressed = pg.key.get_pressed()
            if pressed[pg.K_LEFT] and player_pos > 0:
                player_pos -= 1
            if pressed[pg.K_RIGHT] and player_pos < hack_width - 1:
                player_pos += 1
            if pressed[pg.K_SPACE]:
                if not bullets or bullets[-1][1] < player_line_idx - 1:
                    bullets.append([player_pos, player_line_idx - 1])

            # Spawn de inimigos
            if current_time - last_enemy_spawn > enemy_spawn_interval:
                max_enemies_per_wave = 6
                possible_positions = list(range(0, hack_width, 3))  # ≥2 espaços
                random.shuffle(possible_positions)
                num_to_spawn = random.randint(1, max_enemies_per_wave)
                spawn_positions = possible_positions[:num_to_spawn]
                for x in spawn_positions:
                    enemies.append([x, 0])
                last_enemy_spawn = current_time

            # Move inimigos
            enemy_move_accumulator += dt
            if enemy_move_accumulator >= 1 / enemy_speed:
                for enemy in enemies:
                    enemy[1] += 1
                enemy_move_accumulator = 0

            # Atualiza balas
            bullets = [[b[0], b[1]-bullet_speed] for b in bullets if b[1]-bullet_speed >= 0]

            # Colisão bala x inimigo
            remaining_enemies = []
            new_bullets = bullets.copy()
            for e in enemies:
                hit = False
                for b in bullets:
                    if b[0] == e[0] and int(b[1]) == e[1]:
                        hit = True
                        if b in new_bullets:
                            new_bullets.remove(b)
                        break
                if not hit:
                    remaining_enemies.append(e)
            enemies = remaining_enemies
            bullets = new_bullets

            # Se algum inimigo chegou à última linha, derrota
            if any(e[1] >= hack_height for e in enemies):
                return False

            # --- Desenhar ---
            screen.fill((0, 0, 0))
            y = 20
            line_height = terminal.font.get_height() + 5

            # Mensagens
            for msg in messages_backup[-5:]:
                rendered = terminal.font.render(msg, True, constants.TERMINAL)
                screen.blit(rendered, (20, y))
                y += line_height

            cell_w = terminal.font.size(' ')[0]
            cell_h = line_height
            y_offset = y  # deslocamento vertical após mensagens

            # Desenhar inimigos
            for ex, ey in enemies:
                enemy_render = terminal.font.render('*', True, constants.TERMINAL)
                screen.blit(enemy_render, (20 + ex * cell_w, y_offset + ey * cell_h))

            # Desenhar balas
            for bx, by in bullets:
                bullet_render = terminal.font.render('|', True, constants.TERMINAL)
                screen.blit(bullet_render, (20 + bx * cell_w, y_offset + int(by) * cell_h))

            # Desenhar jogador
            player_render = terminal.font.render('@', True, constants.TERMINAL)
            player_rect = pg.Rect(20 + player_pos * cell_w, y_offset + player_line_idx * cell_h, cell_w, cell_h)
            screen.blit(player_render, player_rect.topleft)

            # Colisão jogador x inimigo
            for ex, ey in enemies:
                enemy_rect = pg.Rect(20 + ex * cell_w, y_offset + ey * cell_h, cell_w, cell_h)
                if player_rect.colliderect(enemy_rect):
                    return False

            pg.display.flip()

    def run_hack_minigame():
        hack_width = 20
        hack_height = 8
        duration = 10
        player_pos = hack_width // 2
        obstacle_interval = 0.1

        lines = [[' ']*hack_width for _ in range(hack_height)]
        messages_backup = terminal.messages.copy()
        player_line_idx = hack_height - 4

        start_time = time.time()
        last_obstacle_time = 0
        mini_clock = pg.time.Clock()
        path_width = 15
        path_start_col = max(0, min(hack_width - path_width, player_pos - path_width // 2))

        running = True
        while running:
            dt = mini_clock.tick(60) / 1000
            current_time = time.time()
            elapsed = current_time - start_time

            if elapsed > duration:
                return True

            # Eventos
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()

            # Movimento jogador
            pressed = pg.key.get_pressed()
            if pressed[pg.K_LEFT] and player_pos > 0:
                player_pos -= 0.3
            if pressed[pg.K_RIGHT] and player_pos < hack_width - 1:
                player_pos += 0.3

            # Gerar obstáculos
            if current_time - last_obstacle_time > obstacle_interval:
                lines.pop(0)
                new_line = ['#']*hack_width
                shift = random.choice([-2, -1, 0, 1, 2])
                path_start_col += shift
                path_start_col = max(0, min(hack_width - path_width, path_start_col))
                for i in range(path_start_col, path_start_col + path_width):
                    new_line[i] = ' '
                lines.append(new_line)
                last_obstacle_time = current_time

            # --- Desenhar ---
            screen.fill((0, 0, 0))
            y = 20
            line_height = terminal.font.get_height() + 5

            # Mensagens
            for msg in messages_backup[-5:]:
                rendered = terminal.font.render(msg, True, constants.TERMINAL)
                screen.blit(rendered, (20, y))
            y_offset = y + 5 * line_height  # deslocamento após mensagens

            # Tamanho célula
            cell_w = terminal.font.size(' ')[0]
            cell_h = line_height

            # Desenhar obstáculos
            for row_idx, row in enumerate(lines):
                for col_idx, char in enumerate(row):
                    if char == '#':
                        obstacle_render = terminal.font.render('#', True, constants.TERMINAL)
                        screen.blit(obstacle_render, (20 + col_idx * cell_w, y_offset + row_idx * cell_h))

            # Jogador separado
            player_rect = pg.Rect(
                20 + player_pos * cell_w,
                y_offset + player_line_idx * cell_h,
                cell_w, cell_h
            )
            player_render = terminal.font.render('@', True, constants.TERMINAL)
            screen.blit(player_render, player_rect.topleft)

            # Colisão jogador x obstáculos
            for col, char in enumerate(lines[player_line_idx]):
                if char == '#':
                    obstacle_rect = pg.Rect(
                        20 + col * cell_w,
                        y_offset + player_line_idx * cell_h,
                        cell_w, cell_h
                    )
                    if player_rect.colliderect(obstacle_rect):
                        return False

            pg.display.flip()


    black_screen = False
    collided_enemy = None

    def find_free_position_with_exit(grid_dict, player_pos):
        max_x = max(x for x, _ in grid_dict.keys()) + 1
        max_y = max(y for _, y in grid_dict.keys()) + 1

        px, py = int(player_pos.x), int(player_pos.y)

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = px + dx, py + dy
            if 0 <= nx < max_x and 0 <= ny < max_y and grid_dict.get((nx, ny), 1) == 0:
                return nx + 0.5, ny + 0.5

        return px + 0.5, py + 0.5

    running = True
    while running:
        dt = clock.tick(constants.FPS)/1000.0
        buff_ended = player.update_buffs(dt)
        if buff_ended:
            terminal.messages.append("WARN: dmg buff ended")
        running, events, pressed = handle_events(player, enemies, blocked=black_screen)
        if not running:
            break
        if tab_pressed:
            screen.fill((0, 0, 0))
            def terminal_command_callback(command):
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
                        items = ", ".join(player.inventory)
                        terminal.messages.append(f"Inventory: {items}")
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
            continue
            
        if black_screen:
            screen.fill((0, 0, 0))

            def terminal_command_callback(command):
                import random
                nonlocal black_screen, collided_enemy
                def enemy_turn():
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

                if command["type"] == "attack":
                    if collided_enemy and command["target"] == collided_enemy.name:
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
                        minigame_choice = random.choice(["A", "B"])
                        if minigame_choice == "A":
                            success = run_hack_minigame()
                        else:
                            success = run_space_invaders_minigame()

                        if success:
                            terminal.messages.append("hacking complete")
                            terminal.messages.append(
                                f"{collided_enemy.name} received {collided_enemy.hp} dmg from hacking! enemy HP: 1"
                            )
                            collided_enemy.hp = 1
                        else:
                            player.hp -= 3
                            terminal.messages.append(f"HACKING FAILED (-3 HP) Current HP:{player.hp}")
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

            def terminal_error_callback(cmd_text):
                terminal.messages.append(f'ERROR: Command "{cmd_text}" not recognized!')

            terminal.handle_event(events, command_callback=terminal_command_callback, error_callback=terminal_error_callback)
            terminal.draw(screen)
            pg.display.flip()
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

        clear_screen(screen)
        draw_floor(screen, width, height)
        draw_ceiling(screen, width, height)

        cast_rays(
            screen,
            player.xy,
            player.direction,
            player.plane,
            grid,
            width,
            height,
            step=constants.STEP
        )
        draw_enemies(screen, player, enemies, grid, width, height)

        draw_text(screen, font, clock, half_w)
        pg.display.flip()

def player_collides_enemy(player, enemy, radius=0.2):
    if isinstance(enemy, game_objects.SparedEnemy):
        return False
    dx = player.x - enemy.x
    dy = player.y - enemy.y
    return dx * dx + dy * dy < radius * radius

def clear_screen(screen):
    screen.fill((0, 0, 0))

def draw_floor(screen, width, height):
    pg.draw.rect(screen, constants.FLOOR, (0, height // 2, width, height // 2))

def draw_ceiling(screen, width, height):
    pg.draw.rect(screen, constants.CEILING, (0, 0, width, height // 2))

def draw_text(screen, font, clock, half_w):
    text = font.render(f"fps={int(clock.get_fps())}", False, (255, 0, 0))
    screen.blit(text, (half_w, 0))

def handle_events(player, enemies=None, blocked=False):
    global tab_pressed
    running = True
    events = pg.event.get()
    pressed = pg.key.get_pressed()

    for event in events:
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            running = False
        elif event.type == pg.KEYDOWN and event.key == pg.K_TAB:
            tab_pressed = not tab_pressed
            blocked = not blocked
        

    if not blocked:
        player.handle_event(events, pressed, enemies)

    return running, events, pressed

def cast_rays(screen, origin, direction, plane, grid_dict, width, height, step=1):
    assert step >= 1
    half_h = height // 2

    for x in range(0, width, step):
        camera_x = (2 * x) / width - 1
        ray = constants.Point2(
            direction.x + plane.x * camera_x,
            direction.y + plane.y * camera_x,
        )

        dist, side, element = run_along_ray(origin, ray, grid_dict)
        if side == -1:
            continue

        safe_dist = dist if dist != 0 else 1e-6

        color = constants.WALL
        ratio = 1 - (1 / (safe_dist + 1))
        if side == 0:
            color = functions.darken_rgb(color, 50)
        color = functions.darken_rgb(color, ratio * 150)

        line_height = height / (safe_dist * 2)
        y_start = max(0, int((half_h - line_height / 2)))
        y_end = min(height - 1, int((half_h + line_height / 2)))

        pg.draw.line(screen, color, (x, y_start), (x, y_end))

def run_along_ray(start, ray_dir, grid_dict):
    INF = float("inf")

    delta_dist_x = INF if ray_dir.x == 0 else abs(1 / ray_dir.x)
    delta_dist_y = INF if ray_dir.y == 0 else abs(1 / ray_dir.y)

    int_map_x, int_map_y = int(start.x), int(start.y)

    if numerical.is_below(ray_dir.x, 0):
        step_x = -1
        side_dist_x = (start.x - int_map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (int_map_x + 1.0 - start.x) * delta_dist_x

    if numerical.is_below(ray_dir.y, 0):
        step_y = -1
        side_dist_y = (start.y - int_map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (int_map_y + 1.0 - start.y) * delta_dist_y

    max_iter = 100
    while max_iter > 0:
        max_iter -= 1
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            int_map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            int_map_y += step_y
            side = 1

        element = grid_dict.get((int_map_x, int_map_y), -1)
        if element != 0:
            break
    else:
        return float("inf"), -1, -1

    if side == 0:
        perp_dist = side_dist_x - delta_dist_x
    else:
        perp_dist = side_dist_y - delta_dist_y

    return perp_dist, side, element

def draw_enemies(screen, player, enemies, grid_dict, width, height):
    half_h = height // 2

    enemies_sorted = sorted(enemies, key=lambda e: (e.x - player.x) ** 2 + (e.y - player.y) ** 2, reverse=True)

    for enemy in enemies_sorted:
        rel_x = enemy.x - player.x
        rel_y = enemy.y - player.y

        inv_det = 1.0 / (player.plane.x * player.direction.y - player.direction.x * player.plane.y)

        transform_x = inv_det * (player.direction.y * rel_x - player.direction.x * rel_y)
        transform_y = inv_det * (-player.plane.y * rel_x + player.plane.x * rel_y)

        if transform_y <= 0:
            continue

        enemy_dist = (rel_x**2 + rel_y**2) ** 0.5
        ray_dir = constants.Point2(rel_x / enemy_dist, rel_y / enemy_dist)

        wall_dist, _, _ = run_along_ray(player.xy, ray_dir, grid_dict)
        if wall_dist < enemy_dist:
            continue

        enemy_screen_x = int((width / 2) * (1 + transform_x / transform_y))

        enemy_height = abs(int(height / transform_y * enemy.size))
        enemy_width = enemy_height

        draw_x = enemy_screen_x - enemy_width // 2
        draw_y = half_h - enemy_height // 2

        pg.draw.rect(screen, enemy.color, (draw_x, draw_y, enemy_width, enemy_height))

if __name__ == "__main__":
    main()
