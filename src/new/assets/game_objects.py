import pygame as pg

import constmath.functions as functions
import constmath.constants as constants
import assets.grid as grid
import assets.game_items as game_items

class Player: 
    def __init__(self, xy) -> None:
        (self.x, self.y) = xy
        self.direction = constants.Point2(1, 0)
        self.plane = constants.Point2(0, 0.66)

        # maos
        self.right_hand = None
        self.left_hand = None
        self.is_stunned = False
        self.extra_damage = 1
        #chance de miss
        self.chance = 0.1

        # inventario do jogador
        self.inventory = ["generic-chainsaw", "ecig", "healthjuice", "parteehard"]

        # vida do jogador
        self.hp = 10000
        self.damage_buff = 0   # usado se consumir algo tipo ParteeHard
        self.buff_timer = 0

    @property
    def xy(self) -> constants.Point2:
        return constants.Point2(self.x, self.y)

    def use_item(self, item: str) -> str:
        from assets.game_items import usable_items_values
        if item not in self.inventory:
            return f"You don’t have {item} in your inventory!"

        if item not in usable_items_values:
            return f"{item} cannot be used!"

        effect = usable_items_values[item]
        msg = []
        if "H" in effect:  # cura
            self.hp += effect["H"]
            msg.append(f"+{effect['H']} HP (total: {self.hp})")
        if "D" in effect:  # buff de dano
            self.damage_buff += effect["D"]
            self.buff_timer = 120
            msg.append(f"+{effect['D']} damage buff (120s)")

        self.inventory.remove(item)  # consumir
        return f"You used {item}: " + ", ".join(msg)


    def get_damage(self, hand: str) -> int:
            items = game_items.equipable_items_hand_dmg
            item = None
            if hand == "right":
                item = self.right_hand
                if item :
                    company, base, symbols = parse_weapon(item)
                    
            elif hand == "left":
                item = self.left_hand
                if item :
                    company, base, symbols = parse_weapon(item)

            if not item:
                return self.extra_damage  # caso não tenha arma

          # nome da arma

            # pega dano base
            dmg = game_items.equipable_items_hand_dmg.get(base, 1)

            # aplica extra damage (de grades ou inimigo)
            chance_to_hit, stun_chance, force_unequip, extra_dmg = parse_weapon_grades(symbols)
            dmg += self.extra_damage + extra_dmg
            
            # aplica multiplicador da marca
            dmg *= game_items.item_companies_values.get(company, 1)
            
            return int(dmg), chance_to_hit, stun_chance, force_unequip

    def update_buffs(self, dt: float) -> None:
        ended = False
        if self.buff_timer > 0:
            self.buff_timer = max(0, self.buff_timer - dt)
            if self.buff_timer == 0:
                self.damage_buff = 0
                ended = True
        return ended
    
    def move(self, dx=0, dy=0, enemies=None) -> None:
        new_x = self.x + dx * constants.STEPSIZE * self.direction.x
        new_y = self.y + dy * constants.STEPSIZE * self.direction.y

        if is_walkable(int(new_x), int(new_y)):
            if not enemies or all(
                (new_x - e.x) ** 2 + (new_y - e.y) ** 2 > 0.01 for e in enemies
            ):
                self.x, self.y = new_x, new_y

    def run(self, dx=0, dy=0, enemies=None) -> None:
        new_x = self.x + dx * (constants.STEPSIZE+0.05) * self.direction.x
        new_y = self.y + dy * (constants.STEPSIZE+0.05) * self.direction.y

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
            if pressed[pg.K_LSHIFT]:
                self.run(-1, -1, enemies)
            else:
                self.move(-1, -1, enemies)
        if pressed[pg.K_UP]:
            if pressed[pg.K_LSHIFT]:
                self.run(1, 1, enemies)
            else:
                self.move(1, 1, enemies)

def is_walkable(x, y):
    if 0 <= x < len(grid.GRID) and 0 <= y < len(grid.GRID[0]):
        return grid.GRID[x][y] == 0
    return False

class Enemy:
    def __init__(self, xy,chance, name="enemy", hp=10, weapon="knife") -> None:
        self.x, self.y = xy
        self.color = constants.ENEMY
        self.size = 0.3
        self.name = name
        self.hp = hp
        self.weapon = weapon
        self.is_stunned = False
        self.extra_damage = self.hp/10
        self.chance = chance
    @property
    def xy(self):
        return constants.Point2(self.x, self.y)

    def get_damage(self) -> int:
        if not self.weapon:
            return self.extra_damage  # caso não tenha arma

        # separa o nome da arma em partes
        company, base, symbols = parse_weapon(self.weapon)  # nome da arma

        # pega dano base
        dmg = game_items.equipable_items_hand_dmg.get(base, 1)

        # aplica extra damage (de grades ou inimigo)
        
        if (len(symbols)>0):
                chance_to_hit, stun_chance, force_unequip, extra_dmg_weapon = parse_weapon_grades(symbols)
        else:
            extra_dmg_weapon = 0

        dmg += self.extra_damage + extra_dmg_weapon
        
        # aplica multiplicador da marca
        dmg *= game_items.item_companies_values.get(company, 1)
        
        return int(dmg), chance_to_hit, stun_chance, force_unequip

    def parse_grades(self):
        self.stun_chance = 0
        self.force_unequip = False

        # separa a parte dos grades (após o último "-")
        if "-" in self.name:
            grade_part = self.name.split("-")[-4:]  # pegar os últimos 4 segmentos que são grades
            grade_str = "-".join(grade_part)
        else:
            grade_str = ""

        plus_count = grade_str.count("+")
        s_count = grade_str.count("S")
        op_count = grade_str.count("OP")
        star_count = grade_str.count("*")

        self.chance = max(0.01, self.chance - plus_count * 0.1)
        self.extra_damage += min(10, s_count * 5)
        self.force_unequip = op_count > 0

        if star_count > 0:
            self.hp = int(self.hp * (30 * star_count))


class SparedEnemy(Enemy):
    def __init__(self, xy, name="spared_enemy", dropped_weapon=None, chance=0):
        super().__init__(xy, name=name, hp=1, weapon=dropped_weapon, chance=0)
        self.color = constants.SPARED
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
        
    # --- helpers (cole acima do Terminal ou no topo do arquivo) ---

    def handle_event(self, events, command_callback=None, error_callback=None):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:
                    if self.text.strip():
                        # Sempre salva o que o jogador digitou
                        self.messages.append("> " + self.text.strip())

                        command = self.parse_command(self.text)
                        if command and command_callback:
                            command_callback(command)
                        elif error_callback:
                            error_callback(self.text.strip())
                    self.text = ""

                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]

                elif event.key == pg.K_TAB:
                    # AUTOCOMPLETE
                    COMMANDS = get_key_words()
                    raw = self.text  # texto completo atual (pode ter espaços)

                    # 1) se há um único comando que começa com toda a linha -> completa a linha inteira
                    full_matches = [c for c in COMMANDS if c.startswith(raw)]
                    if len(full_matches) == 1:
                        self.text = full_matches[0] + " "
                        continue
                    if len(full_matches) > 1:
                        lcp = longest_common_prefix(full_matches)
                        if len(lcp) > len(raw):
                            self.text = lcp
                            continue
                        # não completar mais: mostrar opções ao jogador
                        #self.messages.append("Possíveis: " + ", ".join(full_matches[:20]))
                        continue

                    # 2) tenta completar apenas a última palavra (ex: digitei "player -e" -> "-equip")
                    parts = raw.split()
                    if not parts:
                        continue

                    last = parts[-1]
                    last_matches = [k for k in COMMANDS if k.startswith(last)]
                    if len(last_matches) == 1:
                        parts[-1] = last_matches[0]
                        self.text = " ".join(parts) + " "
                        continue
                    if len(last_matches) > 1:
                        lcp = longest_common_prefix(last_matches)
                        if len(lcp) > len(last):
                            parts[-1] = lcp
                            self.text = " ".join(parts)
                            continue
                        # muitas opções: listar
                        #self.messages.append("Possíveis para '{}': {}".format(last, ", ".join(last_matches[:20])))
                        continue

                    # 3) se nenhum match, avisa (opcional)
                    #self.messages.append("Nenhuma sugestão para: " + last)

                elif event.unicode and event.key not in (pg.K_ESCAPE, pg.K_RETURN, pg.K_BACKSPACE, pg.K_TAB):
                    # adiciona caractere normal
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
            print(item)
            item_type = item.split("-")[-1]
            if hand in ("right", "left") and item_type in game_items.equipable_items_hand:
                return {"type": "equip", "hand": hand, "item": item}
            return None
        
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-use":
            item = parts[2].lower()
            return {"type": "use", "item": item}
        
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-scan":
            target = parts[2].lower()
            print(target)
            return {"type": "scan", "target": target}


        
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
        if text.strip() == "terminal exit":
            return {"type": "exit"}

        return None

    def draw(self, screen):
        line_height = self.font.get_height() + 5
        margin_top = 20
        margin_bottom = 10
        usable_height = self.height - margin_top - margin_bottom
        total_lines = usable_height // line_height

        msgs_to_show = []
        for msg in self.messages:
            wrapped_lines = wrap_text(msg, self.font, self.width)
            msgs_to_show.extend(wrapped_lines)
        msgs_to_show = msgs_to_show[-total_lines+2:]

        y = margin_top
        for msg in msgs_to_show:
            rendered = self.font.render(msg, True, (0, 255, 0))
            screen.blit(rendered, (20, y))
            y += line_height
        edit_lines = wrap_text(self.text, self.font, self.width)

        edit_lines = edit_lines[-(total_lines - len(msgs_to_show)):]  

        for i, line in enumerate(edit_lines):
            edit_y = min(y, self.height - margin_bottom - (len(edit_lines) - i) * line_height)
            rendered = self.font.render(line, True, (0, 255, 0))
            screen.blit(rendered, (20, edit_y))
            y = edit_y + line_height

        if edit_lines:
            last_line = edit_lines[-1]
            cursor_x = 20 + self.font.size(last_line)[0]
            cursor_y = edit_y
            cursor = self.font.render("_", True, (0, 255, 0))
            screen.blit(cursor, (cursor_x, cursor_y))

def longest_common_prefix(strs):
        if not strs:
            return ""
        shortest = min(strs, key=len)
        for i, ch in enumerate(shortest):
            for s in strs:
                if s[i] != ch:
                    return shortest[:i]
        return shortest
    
keywords = [
        "player -a", "player -h", "player -equip", "player -use", "player -scan",
        "player -i ls", "player -e ls",
        "pickup", "combat runaway", "terminal exit",
        "spare", "-rm", "right", "left"
    ]

def get_key_words(collided_enemy=None):
    """
    Retorna uma lista de possíveis comandos/palavras para autocomplete.
    Adiciona também os nomes dos inimigos em combate.
    """
    global keywords

    try:
        import assets.game_items as game_items
        if hasattr(game_items, "equipable_items_hand"):
            keywords.extend(list(game_items.equipable_items_hand))
        if hasattr(game_items, "usable_items_values"):
            keywords.extend(list(game_items.usable_items_values.keys()))
    except Exception:
        pass

    # adiciona inimigo atual
    if collided_enemy and not getattr(collided_enemy, "is_peaceful", False):
        keywords.append(collided_enemy.name)

    return sorted(set(keywords))

    
def wrap_text(text, font, max_width):
        """
        divide texto em várias linhas que caibam em max_width pixels.
        Retorna uma lista de linhas.
        """
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width - 40:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

def parse_weapon(weapon: str):
    """
    Separa arma em: marca, item base e símbolos de grade.
    Ex: 'wyutani-chainsaw-s-op' -> ('wyutani', 'chainsaw', ['s','op'])
    """
    parts = weapon.split("-")
    if len(parts) < 2:
        return weapon, weapon, []

    company = parts[0]
    base = parts[1]
    symbols = parts[2:] if len(parts) > 2 else []
    return company, base, symbols

def parse_weapon_grades(symbols: list):
    chance_to_hit = 0
    stun_chance = 0
    force_unequip = False
    extra_dmg = 0
    for sym in symbols:
                        if sym == "+":
                            chance_to_hit *= 0.9
                            extra_dmg += 20# 10% menos chance de errar por cada +
                        elif sym == "s":
                            stun_chance += 0.2  # cada S dá 20% chance de stun
                            extra_dmg += 20
                        elif sym == "op":
                            force_unequip = True
                            extra_dmg += 20
                        elif sym =="*":
                            extra_dmg +=100
    return chance_to_hit, stun_chance, force_unequip, extra_dmg
    
    
    