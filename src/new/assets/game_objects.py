import pygame as pg

import constmath.functions as functions
import constmath.constants as constants
import assets.grid as grid
import assets.game_items as game_items
import assets.initial_menu as initial_menu

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
        
        self.extra_turns = 0
        self.unequip_resist = 0.0
        self.scan_objects = 0
        self.damage_reduction = 0.0
        self.hack_speed_bonus = 0.0
        self.hp = 15000
        self.damage_buff = 0   # usado se consumir algo tipo ParteeHard
        self.buff_timer = 0


        # inventario do jogador
        self.inventory = {
            "generic-chainsaw": 1,   # equipavel → sempre 1
            "generic-knife-Σ":1,
            "generic-ecig": 5,               # consumivel
            "generic-healthjuice": 2,       
            "generic-parteehard": 1, 
            "generic-arm" : 1
        }


    def get_status(self):
        return (
            f"Player Status: "
            f"HP: {self.hp} "
            f"Prostheses: {', '.join(self.prostheses) if self.prostheses else 'None'} "
            f"Extra Damage: {self.extra_damage + self.damage_buff} "
            f"Miss Chance: {self.chance:.2f} "
            f"Extra Turns: {self.extra_turns} "
            f"Unequip Resist: {self.unequip_resist:.2f} "
            f"Scan Objects: {self.scan_objects} "
            f"Damage Reduction: {self.damage_reduction:.2f} "
            f"Hack Speed Bonus: {self.hack_speed_bonus:.2f} "
            f"Damage Buff: {self.damage_buff} (timer: {self.buff_timer}) "
        )

    @property
    def xy(self) -> constants.Point2:
        return constants.Point2(self.x, self.y)
    
    def install_prosthesis(self, prost_name):
        has_cut_item = False
        company, base, symbols = parse_weapon(prost_name)
        if prost_name not in self.inventory:
            return f"You don’t have {prost_name}!"

        # verifica se é um tipo equip
        if base not in game_items.equipable_prosthetics:
            return f"{prost_name} is not a valid prosthesis!"

        cuttable_items = game_items.cuttable_items

        for item_full in self.inventory:
            # pega o item base (remove prefixo de empresa e sufixo de grades)
            item_parts = item_full.split("-")
            item_base = item_parts[1] if item_parts[0] in game_items.item_companies else item_parts[0]
            if item_base in cuttable_items:
                has_cut_item = True
                break
        if not has_cut_item:
            return "There is nothing to cut with."

        # aplica o efeito
        data = game_items.equipable_prosthetics_data.get(base, {})
        multiplier = game_items.item_companies_values.get(company, 1)
        count = sum(1 for p in self.prostheses if base in p)
        attr_name = f"{prost_name}{count + 1}"
        if "nt" in data:  
            self.extra_turns += int(data["nt"] * multiplier)
            # cria nome único para esta instância da prótese
            setattr(self, attr_name, None)  # adiciona atributo ao jogador
        if "uq" in data: 
            self.unequip_resist += data["uq"] * multiplier
        if "sc" in data: 
            self.scan_objects += int(data["sc"] * multiplier)
        if "df" in data:  
            self.damage_reduction += data["df"] * multiplier
        if "hk" in data: 
            self.hack_speed_bonus += data["hk"] * multiplier
                
        dmg_reduction, extra_hp, force_unequip_reduction, extra_dmg = parse_weapon_grades(symbols)

        self.damage_reduction += dmg_reduction
        self.hp += extra_hp 
        self.unequip_resist += force_unequip_reduction
        self.extra_damage += extra_dmg

        # salva na lista de próteses
        self.prostheses.append(attr_name)

        # consome do inventário
        if self.inventory[prost_name] > 1:
            self.inventory[prost_name] -= 1
        else:
            del self.inventory[prost_name]

        return f"{prost_name} successfully installed as {attr_name}!"

    def use_item(self, item_name: str) -> str:
        """Usa um item do inventário, aplicando efeitos com multiplicadores de marca e reduzindo quantidade."""
        if item_name not in self.inventory:
            return f"You don’t have {item_name}!"

        # separar prefixo (marca) do nome base
        parts = item_name.split("-", 1)
        if len(parts) == 2:
            company, base_name = parts

        # checar se na lista de consum
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
                self.buff_timer = 120 
                msg_parts.append(f"+{dmg_buff} Damage buff")

            # diminuir quantidade
            self.inventory[item_name] -= 1
            if self.inventory[item_name] <= 0:
                del self.inventory[item_name]

            return f"You used {item_name}! ({', '.join(msg_parts)})"

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
            return

        # rotação
        if pressed[pg.K_LEFT]:
            self.rotate(-constants.DEG_STEP)
        if pressed[pg.K_RIGHT]:
            self.rotate(constants.DEG_STEP)
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
    def __init__(self, xy,chance, name="enemy", hp=10, weapon="knife", is_boss=False, unequip_resist=0.2) -> None:
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
        self.unequip_resist = unequip_resist
    @property
    def xy(self):
        return constants.Point2(self.x, self.y)

    def get_damage(self) -> int:
        if not self.weapon:
            return self.extra_damage 

        # separa o nome da arma em partes
        company, base, symbols = parse_weapon(self.weapon) 

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
            grade_part = self.name.split("-")[-4:]  
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
    def __init__(self, font, width, height,level, username="player", terminal_name="terminal"):
        self.font = font
        self.width = width
        self.height = height
        self.messages = []
        self.scroll_offset = 0
        self.text = ""

        self._username = username
        self._terminal_name = terminal_name
        self.update_prompt()
    
    @property
    def username(self):
        return self._username
    @username.setter
    def username(self, value):
        self._username = value
        self.update_prompt()

    @property
    def terminal_name(self):
        return self._terminal_name
    @terminal_name.setter
    def terminal_name(self, value):
        self._terminal_name = value
        self.update_prompt()

    def update_prompt(self):
        self.prompt_prefix = f"{self._username}@{self.terminal_name}:"
        

    def handle_event(self, events, player, command_callback=None, error_callback=None):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.scroll_offset = min(self.scroll_offset + 1, len(self.messages))
                elif event.key == pg.K_DOWN:
                    self.scroll_offset = max(self.scroll_offset - 1, 0)
                    
                elif event.key == pg.K_RETURN:
                    if self.text.strip():
                        # mostra o que o jogador digitou no histórico
                        self.messages.append(f"{self.prompt_prefix} {self.text.strip()}")

                        # agora parse_command retorna uma LISTA de dicts
                        commands = self.parse_command(self.text, player)

                        if commands:
                            if command_callback:
                                command_callback(commands)   # passa lista inteira
                        else:
                            if error_callback:
                                error_callback(self.text.strip())

                    # limpa linha do terminal
                    self.text = ""




                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]

                elif event.key == pg.K_TAB:
                    # AUTOCOMPLETE
                    COMMANDS = get_key_words()
                    raw = self.text 

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
                    self.text += event.unicode


    def parse_command(self, text, player):
        # divide o input em segmentos separados por "&&"
        segments = [seg.strip() for seg in text.split("&&") if seg.strip()]

        max_cmds = max(1, player.extra_turns)  # limite de comandos por turno
        segments = segments[:max_cmds]             # corta os excedentes

        results = []

        for seg in segments:
            parts = seg.strip().split()
            if not parts:
                continue

            # player -a <hand> <enemy>
            if len(parts) == 4 and parts[0] == "player" and parts[1] == "-a":
                hand = parts[2].lower()
                target = parts[3]
                if hand in ("right", "left"):
                    results.append({"type": "attack", "hand": hand, "target": target})
                else:
                    results.append({"type": "unknown", "raw": seg})

            # player -h <enemy>
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "-h":
                results.append({"type": "hack", "target": parts[2]})

            # player -equip <hand> <item>
            elif len(parts) == 4 and parts[0] == "player" and parts[1] == "-equip":
                hand = parts[2].lower()
                item = parts[3].lower()  # permitimos "null" aqui

                # monta a lista de mãos válidas
                valid_hands = ["right", "left"]
                for prost in player.prostheses:
                    if "arm" in prost.lower():  # inclui só próteses de braço
                        valid_hands.append(prost)

                # permite equipar ou desequipar ("null")
                if hand in valid_hands and (item_base := item if item != "null" else "null"):
                    results.append({"type": "equip", "hand": hand, "item": item})
                else:
                    results.append({"type": "unknown", "raw": seg})



            # player -use <item>
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "-use":
                results.append({"type": "use", "item": parts[2].lower()})

            # player -scan <enemy>
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "-scan":
                results.append({"type": "scan", "target": parts[2].lower()})

            # player -install <protese>
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "-install":
                results.append({"type": "install_prosthesis", "prosthesis": parts[2].lower()})

            # player -i ls
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "-i" and parts[2] == "ls":
                results.append({"type": "inventory_list"})

            # player -e ls
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "-e" and parts[2] == "ls":
                results.append({"type": "equipment_list"})

            # player status
            elif len(parts) == 2 and parts[0] == "player" and parts[1] == "status":
                results.append({"type": "status"})

            # player status save
            elif len(parts) == 3 and parts[0] == "player" and parts[1] == "status" and parts[2] == "save":
                results.append({"type": "save"})

            # <enemy> -rm
            elif len(parts) == 2 and parts[1] == "-rm":
                results.append({"type": "remove", "target": parts[0]})

            # <enemy> spare
            elif len(parts) == 2 and parts[1] == "spare":
                results.append({"type": "spare", "target": parts[0]})

            # pickup <item>
            elif len(parts) == 2 and parts[0] == "pickup":
                results.append({"type": "pickup", "item": parts[1].lower()})

            # combat runaway
            elif seg.strip() == "combat runaway":
                results.append({"type": "runaway"})

            # combat exit
            elif seg.strip() == "combat exit":
                results.append({"type": "exit"})

            # help
            elif len(parts) == 1 and parts[0] == "help":
                results.append({"type": "help"})

            # comando inválido
            else:
                results.append({"type": "unknown", "raw": seg})

        return results


    def draw(self, screen):
        line_height = self.font.get_height() + 5
        margin_top = 20
        margin_bottom = 20
        reserved_lines = 3
        usable_height = self.height - margin_top - margin_bottom
        total_lines = usable_height // line_height

        # desenha mensagens
        all_msg_lines = []
        for msg in self.messages:
            all_msg_lines.extend(wrap_text(msg, self.font, self.width))

        message_lines_available = max(0, total_lines - reserved_lines)
        start_index = max(0, len(all_msg_lines) - message_lines_available - self.scroll_offset)
        end_index = start_index + message_lines_available
        msgs_to_show = all_msg_lines[start_index:end_index]

        y = margin_top
        for msg in msgs_to_show:
            rendered = self.font.render(msg, True, (0, 255, 0))
            screen.blit(rendered, (20, y))
            y += line_height

        # linha de input com prompt fixo
        input_text = f"{self.prompt_prefix} {self.text}"
        edit_lines = wrap_text(input_text, self.font, self.width)
        edit_lines = edit_lines[-reserved_lines:]
        edit_start_y = min(y, self.height - margin_bottom - (len(edit_lines)-1)*line_height)

        for i, line in enumerate(edit_lines):
            line_y = edit_start_y + i*line_height
            rendered = self.font.render(line, True, (0, 255, 0))
            screen.blit(rendered, (20, line_y))

        # cursor piscante
        if edit_lines:
            last_line = edit_lines[-1]
            cursor_x = 20 + self.font.size(last_line)[0]
            cursor_y = edit_start_y + (len(edit_lines)-1)*line_height
            cursor = self.font.render("_", True, (0, 255, 0))
            screen.blit(cursor, (cursor_x, cursor_y))

class TerminalMenu:
    def __init__(self, terminal):
        self.terminal = terminal
        self.input_text = ""
        self.player_name = ""
        self.terminal_name = ""
        self.active = True

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pg.K_RETURN:
                self.process_command(self.input_text)
                self.input_text = ""
            elif event.unicode and event.key not in (pg.K_ESCAPE, pg.K_RETURN, pg.K_BACKSPACE, pg.K_TAB):
                    self.input_text += event.unicode
    
    def process_command(self, text):
        parts = text.strip().split()
        if not parts:
            self.terminal.messages.append("> " + text)
            return

        cmd = parts[0].lower()
        #set username <username or terminalname>
        if cmd == "set" and len(parts) >= 3:
            if parts[1] == "username":
                self.player_name = parts[2]
                self.terminal.messages.append(f"> Username set to {self.player_name}")
            elif parts[1] == "terminalname":
                self.terminal_name = parts[2]
                self.terminal.messages.append(f"> Terminal name set to {self.terminal_name}")
        #start <ng or slot<number>>
        elif cmd == "start" and len(parts) == 2:
            saves = initial_menu.load_all_saves()
            
            if parts[1] == "ng":
                if not self.player_name or not self.terminal_name:
                    self.terminal.messages.append("> Set username and terminalname first!")
                    return

                # cria um novo jogador com valores iniciais
                player = Player((3, 10))
                
                # extrai dados primitivos para salvar
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
                    "hp": player.hp,
                    "damage_buff": player.damage_buff,
                    "buff_timer": player.buff_timer
                }

                items_data = {
                    "prostheses": player.prostheses,
                    "inventory": player.inventory
                }

                slot = initial_menu.get_next_slot()
                initial_menu.save_slot_data(slot, player_data, items_data, self.player_name, self.terminal_name, 1)

                self.terminal.messages.append(f"> New game created in {slot}")
                self.active = False


            elif parts[1] in saves:
                slot = parts[1]
                raw_data = initial_menu.load_player_data_from_slot(slot)
                if not raw_data:
                    self.terminal.messages.append(f"> Failed to load save {slot}")
                    return

                # marca o slot selecionado para o main carregar
                self.selected_slot = slot

                cfg = raw_data.get("config", {})
                self.player_name = cfg.get("playerName", "player")
                self.terminal_name = cfg.get("terminalName", "terminal")

                self.terminal.messages.append(f"> Save {slot} selected: {self.player_name} @ {self.terminal_name}")
                self.active = False




            else:
                self.terminal.messages.append(f"> Unknown start option: {parts[1]}")
        #saves ls
        elif cmd == "saves" and len(parts) == 2 and parts[1] == "ls":
            saves = initial_menu.load_all_saves()
            if not saves:
                self.terminal.messages.append("> No saves found")
            else:
                for slot, data in saves.items():
                    cfg = data.get("config", {})
                    player_name = cfg.get("playerName", "player")
                    terminal_name = cfg.get("terminalName", "terminal")
                    self.terminal.messages.append(f"> {slot}: {player_name} @ {terminal_name}")
        elif cmd == "help":
            self.terminal.messages.append("> Available commands:")
            self.terminal.messages.append("  set username <name>      -> set player username")
            self.terminal.messages.append("  set terminalname <name>  -> set terminal name")
            self.terminal.messages.append("  start ng                 -> start a new game")
            self.terminal.messages.append("  start <slot>             -> load a saved game by slot name")
            self.terminal.messages.append("  saves ls                 -> list all saves")
            self.terminal.messages.append("  help                     -> show this help message")
        else:
            self.terminal.messages.append("> Unknown command: " + text)

    def draw(self, screen):
        txt_surf = self.terminal.font.render("> " + self.input_text, True, (0,255,0))
        screen.blit(txt_surf, (10, self.terminal.height - 30))

        # por algo como
        self.terminal.text = self.input_text  # propaga o texto do menu para o terminal
        self.terminal.draw(screen)




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

    global keywords

    # empresas
    companies = game_items.item_companies

    # itens equipáveis
    equip_items = game_items.equipable_items_hand

    # itens consumíveis
    usable = game_items.usable_items
    
    prosthetics = game_items.equipable_prosthetics

    def process_item(full_name):
        item_parts = full_name.split("-")

        # detecta prefixo de empresa
        company_prefix = item_parts[0] if item_parts[0] in companies else None

        # pega item_base (segundo se tiver empresa, senão primeiro)
        if company_prefix:
            if len(item_parts) >= 2:
                item_base = item_parts[1]
            else:
                return
        else:
            item_base = item_parts[0]

        # grades = tudo que sobra depois de empresa + base
        grades = item_parts[2:] if company_prefix else item_parts[1:]

        # monta nome base
        keyword = f"{company_prefix}-{item_base}" if company_prefix else item_base

        # só adiciona se for item válido
        if item_base in equip_items or item_base in usable or item_base in prosthetics:
            keywords.append(keyword)

            # adiciona versão com grades
            if grades:
                keyword_with_grades = f"{keyword}-{'-'.join(grades)}"
                keywords.append(keyword_with_grades)

    # ---- Inventário do jogador ----
    for full_name in player_inventory:
        process_item(full_name)

    # ---- Itens dropados ----
    for _, _, drop_name in dropped_items:
        process_item(drop_name)
    return list(set(keywords))  # remove duplicados

keywords = [
        "player -a", "player -h", "player -equip", "player -use", "player -scan",
        "player -i ls", "player -e ls",
        "pickup", "combat runaway", "terminal exit","status", "-install",
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
        if hasattr(game_items, "equipable_prosthetics"):
            keywords.extend(list(game_items.equipable_prosthetics))
        if hasattr(game_items, "grades"):
            keywords.extend(list(game_items.grades))
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
    force_unequip = 0.0
    extra_dmg = 0
    for sym in symbols:
                        if sym == "Ω":
                            chance_to_hit *= 0.9
                            extra_dmg += 20 # 10% menos chance de errar por cada +
                        elif sym == "Σ":
                            stun_chance += 0.2  # cada S dá 20% chance de stun
                            extra_dmg += 20
                        elif sym == "α":
                            force_unequip += 0.1
                            extra_dmg += 20
                        elif sym =="β":
                            extra_dmg +=100
    return chance_to_hit, stun_chance, force_unequip, extra_dmg


def parse_prost_grades(symbols: list):
    extra_hp = 0
    dmg_reduction = 0.0
    extra_dmg = 0
    force_unequip_reduction = 0.0
    for sym in symbols:
                        if sym == "Ω":
                            dmg_reduction += 0.07
                        elif sym == "Σ":
                            extra_hp += 20
                        elif sym == "α":
                            force_unequip_reduction += 0.1
                        elif sym =="β":
                            extra_dmg +=100
    return dmg_reduction, extra_hp, force_unequip_reduction, extra_dmg
