import pygame as pg

import functions
import constants
import grid
import game_items


Grid = {}
for x, row in enumerate(grid.GRID):
    for y, element in enumerate(row):
        Grid[(x, y)] = element

class Player: 
    def __init__(self, xy) -> None:
        (self.x, self.y) = xy
        self.direction = constants.Point2(1, 0)
        self.plane = constants.Point2(0, 0.66)

        # maos
        self.right_hand = None
        self.left_hand = None

        # inventario do jogador
        self.inventory = ["knife"]

        # vida do jogador
        self.hp = 20

    @property
    def xy(self) -> constants.Point2:
        return constants.Point2(self.x, self.y)

    def get_damage(self, hand: str) -> int:
        """Retorna o dano baseado no item equipado em uma mão"""
        items = game_items.equipable_items_hand_dmg
        item = None
        if hand == "right":
            item = self.right_hand
        elif hand == "left":
            item = self.left_hand

        if item and item in items:
            return items[item]
        return 1  # soco se não tiver nada equipado
    
    def move(self, dx=0, dy=0, enemies=None) -> None:
        new_x = self.x + dx * constants.STEPSIZE * self.direction.x
        new_y = self.y + dy * constants.STEPSIZE * self.direction.y

        if is_walkable(int(new_x), int(new_y)):
            if not enemies or all(
                (new_x - e.x) ** 2 + (new_y - e.y) ** 2 > 0.01 for e in enemies
            ):
                self.x, self.y = new_x, new_y
    
    def rotate(self, degrees) -> None:
        rads = (degrees / 36) * constants.DEG_STEP
        self.direction = constants.Point2(
            *functions.rotate_by_step(self.direction, rads)
        )
        self.plane = constants.Point2(*functions.rotate_by_step(self.plane, rads))

    def handle_event(self, events, pressed, enemies=None) -> None:
        if pressed[pg.K_LEFT]:
            self.rotate(-constants.DEG_STEP)
        if pressed[pg.K_RIGHT]:
            self.rotate(constants.DEG_STEP)
        if pressed[pg.K_DOWN]:
            self.move(-1, -1, enemies)
        if pressed[pg.K_UP]:
            self.move(1, 1, enemies)

def is_walkable(x, y):
    if 0 <= x < len(grid.GRID) and 0 <= y < len(grid.GRID[0]):
        return grid.GRID[x][y] == 0
    return False

class Enemy:
    def __init__(self, xy, name="enemy", hp=10, weapon="knife") -> None:
        self.x, self.y = xy
        self.color = (255, 0, 0)  
        self.size = 0.3
        self.name = name
        self.hp = hp
        self.weapon = weapon

    @property
    def xy(self):
        return constants.Point2(self.x, self.y)

    def get_damage(self) -> int:
        from game_items import equipable_items_hand_dmg
        return equipable_items_hand_dmg.get(self.weapon, 1)
    
class SparedEnemy(Enemy):
    def __init__(self, xy, name="spared_enemy", dropped_weapon=None):
        super().__init__(xy, name=name, hp=1, weapon=dropped_weapon)
        self.color = (0, 0, 255)  # azul
        self.weapon = None  # n possui arma
        self.size = 0.3

    def get_damage(self) -> int:
        # n causa dano
        return 0

class Terminal:
    def __init__(self, font, width, height):
        self.text = ""  # linha escrevivel
        self.font = font
        self.width = width
        self.height = height
        self.active = True
        self.messages = []  # mensagens postadas

    def handle_event(self, events, command_callback=None, error_callback=None):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:
                    if self.text.strip():
                        command = self.parse_command(self.text)
                        if command and command_callback:
                            command_callback(command)
                        elif error_callback:
                            error_callback(self.text.strip())
                        else:
                            self.messages.append(self.text)
                    self.text = ""
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode and event.key not in (pg.K_ESCAPE, pg.K_RETURN, pg.K_BACKSPACE):
                    self.text += event.unicode

    def parse_command(self, text):
        parts = text.strip().split()

        # player -a <hand> <enemy>
        if len(parts) == 4 and parts[0] == "player" and parts[1] == "-a":
            hand = parts[2].lower()
            target = parts[3]
            if hand in ("right", "left"):
                return {"type": "attack", "hand": hand, "target": target}
            return None
        
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-h":
            target = parts[2]
            return {"type": "hack", "target": target}

        # player -equip <hand> <item>
        if len(parts) == 4 and parts[0] == "player" and parts[1] == "-equip":
            hand = parts[2].lower()
            item = parts[3].lower()
            if hand in ("right", "left") and item in game_items.equipable_items_hand:
                return {"type": "equip", "hand": hand, "item": item}
            return None
        
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-i" and parts[2] == "ls":
            return {"type": "inventory_list"}

        # listar equipamentos
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-e" and parts[2] == "ls":
            return {"type": "equipment_list"}

        # <nome> -rm
        if len(parts) == 2 and parts[1] == "-rm":
            nome = parts[0]
            return {"type": "remove", "target": nome}
        
        if len(parts) == 2 and parts[1] == "spare":
            nome = parts[0]
            return {"type": "spare", "target": nome}
    
        # pickup <item>
        if len(parts) == 2 and parts[0] == "pickup":
            return {"type": "pickup", "item": parts[1].lower()}

        # combat runaway
        if text.strip() == "combat runaway":
            return {"type": "runaway"}

        # combat exit
        if text.strip() == "combat exit":
            return {"type": "exit"}

        return None

    def draw(self, screen):
        line_height = self.font.get_height() + 5
        margin_top = 20
        margin_bottom = 10
        usable_height = self.height - margin_top - margin_bottom
        total_lines = usable_height // line_height
        msgs_to_show = min(len(self.messages), total_lines - 1)
        y = margin_top
        for msg in self.messages[-msgs_to_show:]:
            rendered = self.font.render(msg, True, (0, 255, 0))
            screen.blit(rendered, (20, y))
            y += line_height
        edit_y = min(y, self.height - margin_bottom - line_height)
        edit_rendered = self.font.render(self.text, True, (0, 255, 0))
        screen.blit(edit_rendered, (20, edit_y))
        cursor = self.font.render("_", True, (0, 255, 0))
        screen.blit(cursor, (20 + self.font.size(self.text)[0], edit_y))