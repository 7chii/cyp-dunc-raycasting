import pygame as pg

def handle_events(blocked, tab_pressed, running, player, enemies, see_through, dt, footstep_sound):
    events = pg.event.get()
    pressed = pg.key.get_pressed()

    for event in events:
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
            elif event.key == pg.K_LCTRL:
                tab_pressed = not tab_pressed
                # não inverte blocked aqui, apenas reflete o terminal aberto
                blocked = tab_pressed
            elif event.key == pg.K_v:
                see_through = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_v:
                see_through = False

    if not blocked:
        player.handle_event(events, pressed, enemies, blocked=False, dt=dt, footstep_sound=footstep_sound)
    else:
        player.handle_event([], [False]*len(pg.key.get_pressed()), enemies, blocked=True, dt=0, footstep_sound=None)


    return running, events, tab_pressed, see_through, blocked
