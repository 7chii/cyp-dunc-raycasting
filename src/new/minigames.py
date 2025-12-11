import time
import random
import pygame as pg
import constmath.constants as constants

def run_minigames(screen, terminal, time_off):
    game = random.choice(["A", "B"])
    if(game=="A"):
        return run_hack_minigame(screen, terminal, time_off)
    elif(game=="B"):
        return run_space_invaders_minigame(screen, terminal, time_off)
    
def run_space_invaders_minigame(screen, terminal, time_off):
    hack_width = 16
    hack_height = 8
    duration = 15 - time_off
    if(duration < 0):
        duration = 0.5
    player_pos = hack_width // 2
    player_line_idx = hack_height - 1 

    enemy_spawn_interval = 0.8
    enemy_speed = 2.0  # linhas por segundo
    bullet_speed = 4.0  # linhas por segundo

    enemies = []
    bullets = []

    messages_backup = terminal.messages.copy()

    start_time = time.time()
    last_enemy_spawn = 0
    enemy_move_accumulator = 0
    mini_clock = pg.time.Clock()
    
    space_pressed_last_frame = False

    running = True
    while running:
        dt = mini_clock.tick(60) / 1000
        current_time = time.time()
        elapsed = current_time - start_time

        if elapsed > duration:
            return True

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        # mov jogador
        pressed = pg.key.get_pressed()
        if pressed[pg.K_LEFT]:
            player_pos = max(0, player_pos - dt * 30)
        if pressed[pg.K_RIGHT]:
            player_pos = min(hack_width - 1, player_pos + dt * 30)

        # atirar
        if pressed[pg.K_SPACE] and not space_pressed_last_frame:
            bullets.append([player_pos, float(player_line_idx - 1)])
        space_pressed_last_frame = pressed[pg.K_SPACE]

        # spawn inimigos
        if current_time - last_enemy_spawn > enemy_spawn_interval:
            max_enemies_per_wave = 6
            positions = list(range(0, hack_width, 3))
            random.shuffle(positions)
            num_to_spawn = random.randint(1, max_enemies_per_wave)
            for x in positions[:num_to_spawn]:
                enemies.append([float(x), 0.0])
            last_enemy_spawn = current_time

        # mover inimigos
        for enemy in enemies:
            enemy[1] += enemy_speed * dt

        # update balas
        bullets = [[b[0], b[1] - bullet_speed * dt] for b in bullets if b[1] - bullet_speed * dt >= 0]

        # colisao bala x inimigo
        enemies_to_remove = set()
        new_bullets = []
        for b in bullets:
            hit_any = False
            for idx, e in enumerate(enemies):
                if abs(b[0] - e[0]) < 1 and abs(b[1] - e[1]) < 1:
                    hit_any = True
                    enemies_to_remove.add(idx)
                    break
            if not hit_any:
                new_bullets.append(b)

        bullets = new_bullets
        enemies = [e for idx, e in enumerate(enemies) if idx not in enemies_to_remove]

        # verif derrota
        player_hit = any(e[1] >= player_line_idx for e in enemies)
        if player_hit:
            return False


        screen.fill((0, 0, 0))
        y = 20
        line_height = terminal.font.get_height() + 5

        # msg
        for msg in messages_backup[-5:]:
            rendered = terminal.font.render(msg, True, constants.TERMINAL)
            screen.blit(rendered, (20, y))
            y += line_height

        cell_w = terminal.font.size(' ')[0]
        cell_h = line_height
        y_offset = y

        # desenhar inimigos
        for ex, ey in enemies:
            ex_px = 20 + ex * cell_w
            ey_px = y_offset + ey * cell_h
            screen.blit(terminal.font.render('T', True, constants.TERMINAL), (ex_px, ey_px))

        # desenhar balas
        for bx, by in bullets:
            bx_px = 20 + bx * cell_w
            by_px = y_offset + by * cell_h
            screen.blit(terminal.font.render('|', True, constants.TERMINAL), (bx_px, by_px))

        # Desenhar jogador
        player_px = 20 + player_pos * cell_w
        player_py = y_offset + player_line_idx * cell_h
        screen.blit(terminal.font.render('@', True, constants.TERMINAL), (player_px, player_py))

        pg.display.flip()




def run_hack_minigame(screen, terminal, time_off):
    hack_width = 20
    hack_height = 8
    duration = 10 - time_off
    if(duration < 0):
        duration = 0.5
    player_pos = hack_width // 2
    obstacle_interval = 0.2

    lines = [[' ']*hack_width for _ in range(hack_height)]
    messages_backup = terminal.messages.copy()
    player_line_idx = hack_height - 4

    start_time = time.time()
    last_obstacle_time = 0
    mini_clock = pg.time.Clock()
    path_width = 8
    path_start_col = max(0, min(hack_width - path_width, player_pos - path_width // 2))

    running = True
    while running:
        dt = mini_clock.tick(60) / 1000
        current_time = time.time()
        elapsed = current_time - start_time

        if elapsed > duration:
            return True

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()

        # mov jogador
        pressed = pg.key.get_pressed()
        if pressed[pg.K_LEFT] and player_pos > 0:
            player_pos -= 0.3
        if pressed[pg.K_RIGHT] and player_pos < hack_width - 1:
            player_pos += 0.3

        # Gerar parede
        if current_time - last_obstacle_time > obstacle_interval:
            lines.pop(0)
            
            # Chance random de diminuir o caminho
            if path_width == 8 and random.random() < 0.2:  # 20% de chance de reduzir
                path_width = 6

            new_line = ['#']*hack_width
            shift = random.choice([-2, -1, 0, 1, 2])
            path_start_col += shift
            path_start_col = max(0, min(hack_width - path_width, path_start_col))
            for i in range(path_start_col, path_start_col + path_width):
                new_line[i] = ' '
            lines.append(new_line)
            last_obstacle_time = current_time



        screen.fill((0, 0, 0))
        y = 20
        line_height = terminal.font.get_height() + 5

        # msg
        for msg in messages_backup[-5:]:
            rendered = terminal.font.render(msg, True, constants.TERMINAL)
            screen.blit(rendered, (20, y))
            y += line_height

        cell_w = terminal.font.size(' ')[0]
        cell_h = line_height

        # desenhar paredes
        for row_idx, row in enumerate(lines):
            for col_idx, char in enumerate(row):
                if char == '#':
                    obstacle_render = terminal.font.render('#', True, constants.TERMINAL)
                    screen.blit(obstacle_render, (20 + col_idx * cell_w, y + row_idx * cell_h))

        # player separado
        player_rect = pg.Rect(
            20 + player_pos * cell_w,
            y + player_line_idx * cell_h,
            cell_w, cell_h
        )
        player_render = terminal.font.render('@', True, constants.TERMINAL)
        screen.blit(player_render, player_rect.topleft)

        # colisao jogador x parede
        for col, char in enumerate(lines[player_line_idx]):
            if char == '#':
                obstacle_rect = pg.Rect(
                    20 + col * cell_w,
                    y + player_line_idx * cell_h,
                    cell_w, cell_h
                )
                if player_rect.colliderect(obstacle_rect):
                    return False

        pg.display.flip()