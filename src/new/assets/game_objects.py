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
        self.prostheses = []
        #chance de miss
        self.chance = 0.1

        # inventario do jogador
        self.inventory = {
            "generic-chainsaw": 1,   # equipável → sempre 1
            "generic-ecig": 5,               # consumível
            "generic-healthjuice": 2,        # consumível
            "generic-parteehard": 1          # consumível
        }


        # vida do jogador
        self.hp = 10000
        self.damage_buff = 0   # usado se consumir algo tipo ParteeHard
        self.buff_timer = 0

    @property
    def xy(self) -> constants.Point2:
        return constants.Point2(self.x, self.y)

    def use_item(self, item_name: str) -> str:
        """Usa um item do inventário, aplicando efeitos com multiplicadores de marca e reduzindo quantidade."""
        if item_name not in self.inventory:
            return f"You don’t have {item_name}!"

        # separar prefixo (marca) do nome base
        parts = item_name.split("-", 1)
        if len(parts) == 2:
            company, base_name = parts

        # checar se é consumível
        if base_name in game_items.usable_items:
            effect = game_items.usable_items_values[base_name]
            multiplier = game_items.item_companies_values.get(company, 1)
            msg_parts = []

            if "H" in effect:
                hp_gain = int(effect["H"] * multiplier)
                self.hp += hp_gain
                msg_parts.append(f"+{hp_gain} HP")
            
            if "D" in effect:
                dmg_buff = int(effect["D"] * multiplier)
                self.damage_buff += dmg_buff
                self.buff_timer = 120  # dura 5 turnos
                msg_parts.append(f"+{dmg_buff} Damage buff")

            # diminuir quantidade
            self.inventory[item_name] -= 1
            if self.inventory[item_name] <= 0:
                del self.inventory[item_name]

            return f"You used {item_name}! ({', '.join(msg_parts)})"

        # se não for consumível
        return f"{item_name} cannot be used!"


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
                return self.extra_damage, 1.0, 0.0, False, None  # caso não tenha arma

          # nome da arma

            # pega dano base
            dmg = game_items.equipable_items_hand_dmg.get(base, 1)

            # aplica extra damage (de grades ou inimigo)
            chance_to_hit, stun_chance, force_unequip, extra_dmg = parse_weapon_grades(symbols)
            dmg += self.extra_damage + extra_dmg
            
            # aplica multiplicador da marca
            dmg *= game_items.item_companies_values.get(company, 1)
            
            return int(dmg), chance_to_hit, stun_chance, force_unequip, item

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

    def handle_event(self, events, pressed, enemies=None, blocked=False) -> None:
        
        if blocked:
            return  # não processa nada enquanto bloqueado

        # rotação
        if pressed[pg.K_LEFT]:
            self.rotate(-constants.DEG_STEP)
        if pressed[pg.K_RIGHT]:
            self.rotate(constants.DEG_STEP)

        # movimentação para frente/atrás
        move_dir = 0
        run_dir = 0

        if pressed[pg.K_UP]:
            move_dir += 1
            run_dir += 1
        if pressed[pg.K_DOWN]:
            move_dir -= 1
            run_dir -= 1

        if move_dir != 0:
            if pressed[pg.K_LSHIFT]:
                self.run(run_dir, move_dir, enemies)
            else:
                self.move(move_dir, move_dir, enemies)

def is_walkable(x, y):
    if 0 <= x < len(grid.GRID) and 0 <= y < len(grid.GRID[0]):
        return grid.GRID[x][y] == 0
    return False

class Enemy:
    def __init__(self, xy,chance, name="enemy", hp=10, weapon="knife", is_boss=False) -> None:
        self.x, self.y = xy
        self.color = constants.ENEMY
        self.size = 0.3
        self.name = name
        self.hp = hp
        self.weapon = weapon
        self.is_stunned = False
        self.extra_damage = self.hp/10
        self.chance = chance
        self.is_boss = is_boss
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
            chance_to_hit = 1.0 - self.chance
            force_unequip = False
            stun_chance = 0

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
        plus_count = grade_str.count("Ω")
        s_count = grade_str.count("Σ")
        op_count = grade_str.count("α")
        star_count = grade_str.count("β")

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
        self.scroll_offset = 0
        
    # --- helpers (cole acima do Terminal ou no topo do arquivo) ---

    def handle_event(self, events, command_callback=None, error_callback=None):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.scroll_offset = min(self.scroll_offset + 1, len(self.messages))
                elif event.key == pg.K_DOWN:
                    self.scroll_offset = max(self.scroll_offset - 1, 0)
                    
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

                    full_matches = [c for c in COMMANDS if c.startswith(raw)]
                    if len(full_matches) == 1:
                        self.text = full_matches[0] + " "
                        continue
                    if len(full_matches) > 1:
                        lcp = longest_common_prefix(full_matches)
                        if len(lcp) > len(raw):
                            self.text = lcp
                            continue
                        continue

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
                        continue
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
            item_type = item.split("-")[-1]
            if hand in ("right", "left") and item_type in game_items.equipable_items_hand:
                return {"type": "equip", "hand": hand, "item": item}
            return None
        
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-use":
            item = parts[2].lower()
            return {"type": "use", "item": item}
        
        if len(parts) == 3 and parts[0] == "player" and parts[1] == "-scan":
            target = parts[2].lower()
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
        margin_bottom = 20
        reserved_lines = 3  # linhas reservadas para entrada
        usable_height = self.height - margin_top - margin_bottom
        total_lines = usable_height // line_height

        # processa todas as linhas de mensagens com wrap
        all_msg_lines = []
        for msg in self.messages:
            wrapped_lines = wrap_text(msg, self.font, self.width)
            all_msg_lines.extend(wrapped_lines)

        # espaço máximo para mensagens
        message_lines_available = max(0, total_lines - reserved_lines)

        # aplica scroll_offset: pega as últimas linhas visíveis, descontando scroll
        start_index = max(0, len(all_msg_lines) - message_lines_available - self.scroll_offset)
        end_index = start_index + message_lines_available
        msgs_to_show = all_msg_lines[start_index:end_index]

        # desenha mensagens
        y = margin_top
        for msg in msgs_to_show:
            rendered = self.font.render(msg, True, (0, 255, 0))
            screen.blit(rendered, (20, y))
            y += line_height

        # processa entrada
        edit_lines = wrap_text(self.text, self.font, self.width)
        edit_lines = edit_lines[-reserved_lines:]  # máximo de linhas reservadas

        # posição inicial da entrada: logo após mensagens
        edit_start_y = y
        max_edit_y = self.height - margin_bottom - line_height
        edit_start_y = min(edit_start_y, max_edit_y - (len(edit_lines) - 1) * line_height)

        # desenha entrada
        for i, line in enumerate(edit_lines):
            line_y = edit_start_y + i * line_height
            rendered = self.font.render(line, True, (0, 255, 0))
            screen.blit(rendered, (20, line_y))

        # cursor piscante
        if edit_lines:
            last_line = edit_lines[-1]
            cursor_x = 20 + self.font.size(last_line)[0]
            cursor_y = edit_start_y + (len(edit_lines) - 1) * line_height
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

def generate_item_keywords(player_inventory, dropped_items):
    """
    Gera lista de keywords para autocomplete a partir de:
    - Inventário do jogador
    - Itens dropados
    Inclui prefixos de empresas e sufixos de grades (se existirem).
    """

    # empresas
    companies = game_items.item_companies

    # itens equipáveis
    equip_items = game_items.equipable_items_hand

    # itens consumíveis
    usable = game_items.usable_items

    # ---- Inventário do jogador ----
    for full_name in player_inventory:
        # separa item puro e possível prefixo
        item_parts = full_name.split("-")
        item_base = item_parts[-1]
        company_prefix = item_parts[0] if item_parts[0] in companies else None

        # só equipável
        if item_base in equip_items:
            if company_prefix:
                keywords.append(f"{company_prefix}-{item_base}")
            else:
                keywords.append(item_base)
        elif item_base in usable:
            if company_prefix:
                keywords.append(f"{company_prefix}-{item_base}")
            else:
                keywords.append(item_base)

    # ---- Itens dropados ----
    for _, _, drop_name in dropped_items:
        item_parts = drop_name.split("-")
        item_base = item_parts[-1]
        company_prefix = item_parts[0] if item_parts[0] in companies else None

        if item_base in equip_items:
            if company_prefix:
                keywords.append(f"{company_prefix}-{item_base}")
            else:
                keywords.append(item_base)
        elif item_base in usable:
            if company_prefix:
                keywords.append(f"{company_prefix}-{item_base}")
            else:
                keywords.append(item_base)

    return list(set(keywords))  # remove duplicados
    
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
    chance_to_hit = 0.01
    stun_chance = 0
    force_unequip = False
    extra_dmg = 0
    for sym in symbols:
                        if sym == "Ω":
                            chance_to_hit *= 0.9
                            extra_dmg += 20# 10% menos chance de errar por cada +
                        elif sym == "Σ":
                            stun_chance += 0.2  # cada S dá 20% chance de stun
                            extra_dmg += 20
                        elif sym == "α":
                            force_unequip = True
                            extra_dmg += 20
                        elif sym =="β":
                            extra_dmg +=100
    return chance_to_hit, stun_chance, force_unequip, extra_dmg
    