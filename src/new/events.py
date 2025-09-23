import pygame as pg

def handle_events(blocked, tab_pressed, running, player, enemies, see_through):
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
                blocked = not blocked
            elif event.key == pg.K_v:
                see_through = True
        if event.type == pg.KEYUP:
            if event.key == pg.K_v:
                see_through = False

    if not blocked:
        player.handle_event(events, pressed, enemies)
    return running, events, tab_pressed, see_through