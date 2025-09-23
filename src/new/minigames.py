import time
import random
import pygame as pg

def run_minigames(screen, terminal):
    game = random.choice(["A", "B"])
    if(game=="A"):
        return run_hack_minigame(screen, terminal)
    elif(game=="B"):
        return run_space_invaders_minigame(screen, terminal)
    
def run_space_invaders_minigame(screen, terminal):
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
    
    # Controle de tiro
    space_pressed_last_frame = False

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
            player_pos -= 0.5
        if pressed[pg.K_RIGHT] and player_pos < hack_width - 1:
            player_pos += 0.5

        # ATIRAR: apenas quando tecla é pressionada agora
        if pressed[pg.K_SPACE] and not space_pressed_last_frame:
            bullets.append([player_pos, player_line_idx - 1])
        space_pressed_last_frame = pressed[pg.K_SPACE]

        # Spawn de inimigos
        if current_time - last_enemy_spawn > enemy_spawn_interval:
            max_enemies_per_wave = 6
            possible_positions = list(range(0, hack_width, 3))
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

        # Colisão bala x inimigo com explosão
        enemies_to_remove = set()
        new_bullets = []

        for b in bullets:
            hit_any = False
            for idx, e in enumerate(enemies):
                # colisão permissiva: +-1 coluna e +-1 linha
                if abs(b[0] - e[0]) <= 1 and abs(b[1] - e[1]) <= 1:
                    hit_any = True
                    # marca inimigos na vizinhança 3x3 para remoção
                    for j, other in enumerate(enemies):
                        if abs(other[0] - e[0]) <= 1 and abs(other[1] - e[1]) <= 1:
                            enemies_to_remove.add(j)
                    break
            if not hit_any:
                new_bullets.append(b)

        # Atualiza listas
        bullets = new_bullets
        enemies = [e for idx, e in enumerate(enemies) if idx not in enemies_to_remove]


        # Verifica derrota: inimigo chegou à linha do jogador ou colidiu
        player_hit = any(e[1] >= player_line_idx and e[0] == player_pos for e in enemies)
        if player_hit:
            return False

        # --- Desenhar ---
        screen.fill((0, 0, 0))
        y = 20
        line_height = terminal.font.get_height() + 5

        # Mensagens
        for msg in messages_backup[-5:]:
            rendered = terminal.font.render(msg, True, (0, 255, 0))
            screen.blit(rendered, (20, y))
            y += line_height

        cell_w = terminal.font.size(' ')[0]
        cell_h = line_height
        y_offset = y

        # Desenhar inimigos
        for ex, ey in enemies:
            enemy_render = terminal.font.render('T', True, (0, 255, 0))
            screen.blit(enemy_render, (20 + ex * cell_w, y_offset + int(ey) * cell_h))

        # Desenhar balas
        for bx, by in bullets:
            bullet_render = terminal.font.render('|', True, (0, 255, 0))
            screen.blit(bullet_render, (20 + bx * cell_w, y_offset + int(by) * cell_h))

        # Desenhar jogador
        player_render = terminal.font.render('@', True, (0, 255, 0))
        player_rect = pg.Rect(20 + player_pos * cell_w, y_offset + player_line_idx * cell_h, cell_w, cell_h)
        screen.blit(player_render, player_rect.topleft)

        pg.display.flip()


def run_hack_minigame(screen, terminal):
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
            
            # Chance aleatória de diminuir o caminho
            if path_width == 15 and random.random() < 0.2:  # 20% de chance de reduzir
                path_width = 11

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
            rendered = terminal.font.render(msg, True, (0, 255, 0))
            screen.blit(rendered, (20, y))
        y_offset = y + 5 * line_height  # deslocamento após mensagens

        # Tamanho célula
        cell_w = terminal.font.size(' ')[0]
        cell_h = line_height

        # Desenhar obstáculos
        for row_idx, row in enumerate(lines):
            for col_idx, char in enumerate(row):
                if char == '#':
                    obstacle_render = terminal.font.render('#', True, (0, 255, 0))
                    screen.blit(obstacle_render, (20 + col_idx * cell_w, y_offset + row_idx * cell_h))

        # Jogador separado
        player_rect = pg.Rect(
            20 + player_pos * cell_w,
            y_offset + player_line_idx * cell_h,
            cell_w, cell_h
        )
        player_render = terminal.font.render('@', True, (0, 255, 0))
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