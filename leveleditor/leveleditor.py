class DisplayBlock:
    def hovering(self):
        return self.rect.collidepoint(MOUSE_X, MOUSE_Y)


class Tilemap(DisplayBlock):
    max_size = 64
    min_size = 16

    def __init__(self, size):
        self.surface_size = size
        self.surface = pygame.Surface((self.surface_size, self.surface_size))
        self.rect = pygame.Rect(0, 0, self.surface_size, self.surface_size)

        self.size = Tilemap.max_size  # How many tiles can be seen on screen
        self.column_offset = self.row_offset = 0  # Position of top left tile when zoomed in or not

        self.list = []
        for _ in range(self.size):
            row = []
            for _ in range(self.size):
                row.append(0)
            self.list.append(row)

        self.saved = None
        self.loaded = None

    def calc_tile_size_and_pos(self):
        self.tile_size = int(self.surface_size / self.size)
        self.tile_x = int((MOUSE_X - self.rect.x) / self.tile_size) + self.column_offset
        self.tile_y = int((MOUSE_Y - self.rect.y) / self.tile_size) + self.row_offset

    def apply_texture(self):
        # If item placed was player start item,
        # remove previously placed player start item from tilemap
        # This is done because level can only have 1 player start item
        if ACTIVE_VALUE == START_VALUE:
            for row in range(len(self.list)):
                for column in range(len(self.list[row])):
                    if self.list[row][column] == START_VALUE:
                        # Return tile to normal
                        self.list[row][column] = 0

        self.list[self.tile_y][self.tile_x] = ACTIVE_VALUE

    def zoom(self, in_=True):
        can_zoom = False
        if in_:
            if self.size > Tilemap.min_size:
                self.size = int(self.size / 2)
                can_zoom = True
        else:
            if self.size < Tilemap.max_size:
                self.size = int(self.size * 2)
                can_zoom = True

        if can_zoom:
            self.column_offset = self.tile_x - int(self.size / 2)
            self.row_offset = self.tile_y - int(self.size / 2)

            # Reset x offset if needed
            if self.column_offset < 0:
                self.column_offset = 0
            elif self.column_offset + self.size > Tilemap.max_size:
                self.column_offset = Tilemap.max_size - self.size

            # Reset y offset if needed
            if self.row_offset < 0:
                self.row_offset = 0
            elif self.row_offset + self.size > Tilemap.max_size:
                self.row_offset = Tilemap.max_size - self.size

    def new(self):
        ANGLE_BOX.angle = 0  # Reset anglebox
        SKYTEXTURE_BOX.value = 0  # Reset sky texture

        level_nr = 1
        while str(level_nr) in os.listdir('../levels'):
            level_nr += 1
        LEVEL_NR.text = str(level_nr)

        self.__init__(self.surface_size)

    def save(self):
        def get_player_pos():
            # Scan and find player start pos
            # This is done inside a function to break out from double "for loop" with return
            for row in range(len(self.list)):
                for column in range(len(self.list[row])):
                    if self.list[row][column] == START_VALUE:
                        # Return tile to normal
                        self.list[row][column] = 0

                        # +0.5 centers player position in tile
                        return column + 0.5, row + 0.5
            return None, None

        # Tries to save tilemap and puts self.saved to either True or False depending on if it's possible or not
        SIDEBAR.message_ticks = Sidebar.message_display_time
        self.loaded = None

        start_x, start_y = get_player_pos()
        if start_x and start_y and LEVEL_NR.text != '':  # If ready to save
            filepath = '../levels/{}/tilemap.txt'.format(LEVEL_NR.text)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                for row in self.list:
                    f.write('{}\n'.format(row))
                f.write(str(SKYTEXTURE_BOX.value) + '\n')
                f.write(str(FLOOR_TEXTURE_BOX.value))

            filepath = '../levels/{}/player.txt'.format(LEVEL_NR.text)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write('{},{}\n'.format(start_x, start_y))
                f.write(str(ANGLE_BOX.angle))

            # Add player start item back to editor
            self.list[int(start_y)][int(start_x)] = START_VALUE

            self.saved = True
        else:
            self.saved = False

    def load(self):
        SIDEBAR.message_ticks = Sidebar.message_display_time
        self.saved = None
        try:
            with open('../levels/{}/tilemap.txt'.format(LEVEL_NR.text), 'r') as f:
                self.list = []
                lines = list(f)
                for line in lines[:-2]:
                    row = line[1:-2]  # Get rid of '[' and ']'
                    row = row.split(',')  # Split line into list
                    row = [int(i) for i in row]  # Turn all number strings to an int
                    self.list.append(row)
                SKYTEXTURE_BOX.value = int(lines[-2])
                FLOOR_TEXTURE_BOX.value = int(lines[-1])

            with open('../levels/{}/player.txt'.format(LEVEL_NR.text), 'r') as f:
                player_pos = f.readline().replace('\n', '').split(',')
                player_x, player_y = [float(i) for i in player_pos]
                ANGLE_BOX.angle = float(f.readline().replace('\n', ''))

                # Add player start tile to tilemap
                self.list[int(player_y)][int(player_x)] = START_VALUE

        except FileNotFoundError:
            self.loaded = False
        else:
            self.loaded = True

    def draw(self):
        # Draw grid
        self.surface.fill(Colour.white)
        for pixel in range(0, self.surface_size + 1, self.tile_size):
            pygame.draw.line(self.surface, Colour.grey,
                             (self.rect.x + pixel, self.rect.y), (self.rect.x + pixel, self.rect.y + self.surface_size))
            pygame.draw.line(self.surface, Colour.grey,
                             (self.rect.x, self.rect.y + pixel), (self.rect.x + self.surface_size, self.rect.y + pixel))

        # Draw textures
        y = self.rect.y
        for row in range(self.row_offset, self.row_offset + self.size):
            x = self.rect.x
            for column in range(self.column_offset, self.column_offset + self.size):
                tile_value = self.list[row][column]
                if tile_value:
                    texture = TILE_VALUES_INFO[tile_value].texture  # Get the texture
                    texture = pygame.transform.scale(texture, (self.tile_size, self.tile_size))  # Scale to tile size
                    self.surface.blit(texture, (x, y))
                    if TILE_VALUES_INFO[tile_value].desc == 'Secret':
                        pygame.draw.rect(self.surface, Colour.red, (x, y, self.tile_size, self.tile_size), 2)
                x += self.tile_size
            y += self.tile_size

        DISPLAY.blit(self.surface, (self.rect.x, self.rect.y))


class Sidebar(DisplayBlock):
    message_display_time = 90
    message_pos = (290, 16)
    x_safezone = 24

    def __init__(self, width, height):
        self.surface = pygame.Surface((width, height))
        self.rect = pygame.Rect(TILEMAP.surface_size, 0, width, height)
        self.message_ticks = 0

    def update_messages(self):
        self.surface.fill(Colour.black)

        if self.message_ticks:
            self.message_ticks -= 1

            if TILEMAP.saved is not None:
                if TILEMAP.saved:
                    text = FONT.render('SAVED', False, Colour.green)
                    self.surface.blit(text, Sidebar.message_pos)
                else:
                    text = FONT.render('SAVE FAILED', False, Colour.red)
                    self.surface.blit(text, Sidebar.message_pos)

                if not self.message_ticks:
                    TILEMAP.saved = None

            if TILEMAP.loaded is not None:
                if TILEMAP.loaded:
                    text = FONT.render('LOAD SUCCESSFUL', False, Colour.green)
                    self.surface.blit(text, Sidebar.message_pos)
                else:
                    text = FONT.render('LOAD FAILED', False, Colour.red)
                    self.surface.blit(text, Sidebar.message_pos)

                if not self.message_ticks:
                    TILEMAP.loaded = None

    def draw(self):
        # Active value texture
        active_texture = TILE_VALUES_INFO[ACTIVE_VALUE].texture
        self.surface.blit(pygame.transform.scale(active_texture, (TEXTURE_SIZE * 2, TEXTURE_SIZE * 2)),
                          (Sidebar.x_safezone, 16))

        # Active value description
        active_item = FONT.render('ACTIVE ITEM:', False, Colour.white)
        item_type = FONT.render('{}:'.format(TILE_VALUES_INFO[ACTIVE_VALUE].type), False, Colour.white)
        item_desc = FONT.render(TILE_VALUES_INFO[ACTIVE_VALUE].desc, False, Colour.white)
        self.surface.blit(active_item, (Sidebar.x_safezone + TEXTURE_SIZE * 2, 16))
        self.surface.blit(item_type, (Sidebar.x_safezone + TEXTURE_SIZE * 2, 32))
        self.surface.blit(item_desc, (Sidebar.x_safezone + TEXTURE_SIZE * 2, 48))

        # Sidebar objects
        for sidebar_obj in SIDEBAR_OBJECTS:
            sidebar_obj.draw()

        # Map position mouse is hovering over
        if TILEMAP.hovering():
            tile_pos = 'x:{} y:{}'.format(TILEMAP.tile_x, TILEMAP.tile_y)
        else:
            tile_pos = 'None'
        tile_pos = FONT.render(tile_pos, False, Colour.white)
        self.surface.blit(tile_pos, (Sidebar.x_safezone, self.rect.h - FONT_SIZE))

        DISPLAY.blit(self.surface, (self.rect.x, self.rect.y))


class SidebarObject:
    def hovering(self):
        display_rect = pygame.Rect(SIDEBAR.rect.x + self.rect.x, SIDEBAR.rect.y + self.rect.y, self.rect.w, self.rect.h)
        return display_rect.collidepoint(MOUSE_X, MOUSE_Y)


class SelectionBox:
    arrow_safezone = 4

    def draw_outline(self):
        if self.active:
            outline_color = Colour.red
            if self.value - 1 in self.values:
                SIDEBAR.surface.blit(SelectionBox.up_arrow,
                                     (self.rect.x + (self.rect.w - SelectionBox.arrow_w) / 2,
                                      self.rect.y - SelectionBox.arrow_h - SelectionBox.arrow_safezone))
            if self.value + 1 in self.values:
                SIDEBAR.surface.blit(SelectionBox.down_arrow,
                                     (self.rect.x + (self.rect.w - SelectionBox.arrow_w) / 2,
                                      self.rect.y + self.rect.h + SelectionBox.arrow_safezone))
        else:
            outline_color = Colour.white
        pygame.draw.rect(SIDEBAR.surface, outline_color, self.rect, 1)


class TextureGroup(SidebarObject, SelectionBox):
    def __init__(self, pos, value):
        self.rect = pygame.Rect(pos, (TEXTURE_SIZE, TEXTURE_SIZE))
        self.value = value  # Current texturegroup value
        self.values = [value]  # All possible texturegroup values

        self.active = False

    def clicked(self):
        self.active = True
        global ACTIVE_VALUE
        ACTIVE_VALUE = self.value

    def change_value(self, increase):
        if self.value + increase in self.values:
            self.value += increase
            global ACTIVE_VALUE
            ACTIVE_VALUE = self.value

    def draw(self):
        texture = TILE_VALUES_INFO[self.value].texture
        SIDEBAR.surface.blit(texture, (self.rect.x, self.rect.y))

        self.draw_outline()


class BackgroundBox(SidebarObject, SelectionBox):
    def __init__(self, caption, pos, textures):
        self.rect = pygame.Rect(pos, (SIDEBAR.rect.w - Sidebar.x_safezone * 2, 64))
        self.caption = FONT.render(caption, False, Colour.white)

        self.values = [x for x in range(len(textures))]
        self.value = self.values[0]

        self.textures = textures
        self.active = False

    def clicked(self):
        self.active = True

    def change_value(self, increase):
        if self.value + increase in self.values:
            self.value += increase

    def draw(self):
        # Draw caption
        SIDEBAR.surface.blit(self.caption, (self.rect.x, self.rect.y - FONT_SIZE))
        # Draw background texture
        texture = self.textures[self.value]
        if texture.get_width() == TEXTURE_SIZE:
            texture_width = round(self.rect.w / int(self.rect.w / TEXTURE_SIZE))
            for x in range(self.rect.x, self.rect.x + self.rect.w - TEXTURE_SIZE, texture_width):
                SIDEBAR.surface.blit(pygame.transform.scale(texture, (texture_width, TEXTURE_SIZE)), (x, self.rect.y))
        else:
            SIDEBAR.surface.blit(
                pygame.transform.scale(texture, (self.rect.w, self.rect.h)), (self.rect.x, self.rect.y))
        self.draw_outline()


class InputBox(SidebarObject):
    def __init__(self, caption, pos, text_colour, width=40, character_limit=2):
        self.rect = pygame.Rect(pos, (width, FONT_SIZE))
        self.caption = FONT.render(caption, False, Colour.white)
        self.character_limit = character_limit

        self.text_colour = text_colour
        self.text = ''
        self.active = False

    def clicked(self):
        self.active = True

    def draw(self):
        # Draw inputbox background
        if self.active:
            background_color = Colour.white
        else:
            background_color = Colour.grey
        pygame.draw.rect(SIDEBAR.surface, background_color, self.rect)

        # Draw inputbox text
        text = FONT.render(self.text, False, self.text_colour)
        SIDEBAR.surface.blit(text, (self.rect.x + (self.rect.w - text.get_width()) / 2, self.rect.y))

        # Draw caption text
        SIDEBAR.surface.blit(self.caption, (self.rect.x, self.rect.y - FONT_SIZE))


class AngleBox(SidebarObject):
    def __init__(self, caption, pos):
        try:
            self.image = pygame.image.load('textures/redarrow.png').convert_alpha()
        except pygame.error as loading_error:
            sys.exit(loading_error)

        self.rect = pygame.Rect(pos, self.image.get_size())
        self.caption = FONT.render(caption, False, Colour.white)

        self.rotating_radians = pi / 2
        self.angle = 0
        self.active = False

    def clicked(self):
        self.angle += self.rotating_radians
        if self.angle > pi:
            self.angle -= pi * 2

    def draw(self):
        SIDEBAR.surface.blit(pygame.transform.rotate(self.image, degrees(-self.angle)), (self.rect.x, self.rect.y))
        SIDEBAR.surface.blit(self.caption, (self.rect.x, self.rect.y - FONT_SIZE))


def events():
    global QUIT
    global ACTIVE_VALUE

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            QUIT = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if SIDEBAR.hovering():
                    for sidebar_obj in SIDEBAR_OBJECTS:
                        if sidebar_obj.hovering():
                            sidebar_obj.clicked()
                        else:
                            sidebar_obj.active = False

            elif event.button == 4:  # Scroll wheel up
                if TILEMAP.hovering() and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    TILEMAP.zoom()

                else:
                    for selection_box in SELECTION_BOXES:
                        if selection_box.active:
                            selection_box.change_value(-1)
                            break

            elif event.button == 5:  # Scroll wheel down
                if TILEMAP.hovering() and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    TILEMAP.zoom(False)

                else:
                    for selection_box in SELECTION_BOXES:
                        if selection_box.active:
                            selection_box.change_value(1)
                            break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.new()

            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.save()

            elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.load()

            else:
                if LEVEL_NR.active:
                    if event.key == pygame.K_BACKSPACE:
                        LEVEL_NR.text = LEVEL_NR.text[:-1]
                    elif pygame.key.name(event.key).isdigit() and len(LEVEL_NR.text) < LEVEL_NR.character_limit:
                        LEVEL_NR.text += event.unicode

    # If mouse left button pressed down and mouse inside tilemap area
    if pygame.mouse.get_pressed()[0]:
        if TILEMAP.hovering():
            TILEMAP.apply_texture()


def create_sidebar_objects():
    # Load selectionbox arrows
    try:
        SelectionBox.up_arrow = pygame.image.load('textures/arrow.png').convert_alpha()
        SelectionBox.down_arrow = pygame.transform.flip(SelectionBox.up_arrow, False, True)
        SelectionBox.arrow_w, SelectionBox.arrow_h = SelectionBox.up_arrow.get_size()
    except pygame.error as loading_error:
        sys.exit(loading_error)

    # Texturegroups
    x_gap = 16
    y_gap = 32

    # Texturegroup heights
    tg_starts = {
        'Enemy':     (Sidebar.x_safezone,                              192 + (TEXTURE_SIZE + y_gap) * 0),
        'Object':    (Sidebar.x_safezone,                              192 + (TEXTURE_SIZE + y_gap) * 1),
        'Door':      (Sidebar.x_safezone,                              192 + (TEXTURE_SIZE + y_gap) * 2),
        'Thin Wall': (Sidebar.x_safezone + 3 * (TEXTURE_SIZE + x_gap), 192 + (TEXTURE_SIZE + y_gap) * 2),
        'Wall':      (Sidebar.x_safezone,                              192 + (TEXTURE_SIZE + y_gap) * 3),
        'Special':   (Sidebar.x_safezone,                              192 + (TEXTURE_SIZE + y_gap) * 5)
    }

    global TEXTUREGROUPS
    TEXTUREGROUPS = []

    tile_infos = []
    for value in TILE_VALUES_INFO:
        tile_type = TILE_VALUES_INFO[value].type
        tile_desc = TILE_VALUES_INFO[value].desc
        if (tile_type, tile_desc) not in tile_infos:  # If the need to create a new texturegroup
            x, y = tg_starts[tile_type]
            for type, desc in tile_infos:
                if tile_type == type:
                    # For every texturegroup with same tpye, move x
                    x += TEXTURE_SIZE + x_gap
                    if x > SIDEBAR.rect.w - TEXTURE_SIZE - Sidebar.x_safezone:
                        x = Sidebar.x_safezone
                        y += TEXTURE_SIZE + y_gap
            TEXTUREGROUPS.append(TextureGroup((x, y), value))
            tile_infos.append((tile_type, tile_desc))
        else:
            TEXTUREGROUPS[-1].values.append(value)
            if value < 0:
                TEXTUREGROUPS[-1].value = value

    # Level nr
    global LEVEL_NR
    LEVEL_NR = InputBox('LEVEL NR:', (Sidebar.x_safezone, SIDEBAR.rect.h - 250), Colour.black)

    # Angle box
    global ANGLE_BOX
    ANGLE_BOX = AngleBox('STARTING ANGLE:', (Sidebar.x_safezone + 100, SIDEBAR.rect.h - 250))

    # Skytexture box
    skytextures = []
    for skytexture_name in os.listdir('../textures/skies'):
        skytextures.append(pygame.image.load('../textures/skies/{}'.format(skytexture_name)).convert())

    global SKYTEXTURE_BOX
    SKYTEXTURE_BOX = BackgroundBox('SKYTEXTURE:', (Sidebar.x_safezone, SIDEBAR.rect.h - 190), skytextures)

    # Floor texture box
    try:
        floor_textures_image = pygame.image.load('../textures/walls/floor.png').convert()
    except pygame.error as loading_error:
        sys.exit(loading_error)
    else:
        floor_textures = []
        for y in range(0, floor_textures_image.get_height(), TEXTURE_SIZE):
            floor_textures.append(floor_textures_image.subsurface(0, y, TEXTURE_SIZE, TEXTURE_SIZE))
        global FLOOR_TEXTURE_BOX
        FLOOR_TEXTURE_BOX = BackgroundBox('FLOOR TEXTURE:', (Sidebar.x_safezone, SIDEBAR.rect.h - 95), floor_textures)

    global SIDEBAR_OBJECTS
    SIDEBAR_OBJECTS = TEXTUREGROUPS + [LEVEL_NR] + [ANGLE_BOX] + [SKYTEXTURE_BOX] + [FLOOR_TEXTURE_BOX]

    global SELECTION_BOXES
    SELECTION_BOXES = TEXTUREGROUPS + [SKYTEXTURE_BOX] + [FLOOR_TEXTURE_BOX]


def get_tilevaluesinfo():
    try:
        eraser_texture = pygame.transform.scale(
            pygame.image.load('textures/eraser.png').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE))
        start_texture = pygame.transform.scale(
            pygame.image.load('textures/start.png').convert(), (TEXTURE_SIZE, TEXTURE_SIZE))
        end_texture = pygame.transform.scale(
            pygame.image.load('textures/end.png').convert(), (TEXTURE_SIZE, TEXTURE_SIZE))

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        # Get tile_values_info from graphics.py
        global TILE_VALUES_INFO
        TILE_VALUES_INFO = graphics.get_tile_values_info(enemies.get_enemy_info())

        for value in TILE_VALUES_INFO:
            if value:
                # Crop all textures to 64x64 pixels
                TILE_VALUES_INFO[value].texture = TILE_VALUES_INFO[value].texture.subsurface(0, 0, TEXTURE_SIZE, TEXTURE_SIZE)
            if TILE_VALUES_INFO[value].desc == 'End-trigger':
                # Replace the end-trigger textures with start and end texture
                TILE_VALUES_INFO[value].texture = end_texture
                TILE_VALUES_INFO[value].type = 'Special'

                global START_VALUE
                START_VALUE = value + 1
                TILE_VALUES_INFO[START_VALUE].texture = start_texture
                TILE_VALUES_INFO[START_VALUE].type = 'Special'
                TILE_VALUES_INFO[START_VALUE].desc = 'Start'

        # Add eraser texture to value 0
        TILE_VALUES_INFO[0].texture = eraser_texture
        TILE_VALUES_INFO[0].type = 'Special'
        TILE_VALUES_INFO[0].desc = 'Eraser'


import sys
import os
import pygame

from math import pi, degrees
from game.main import Colour
from game.settings import TEXTURE_SIZE
import game.graphics as graphics
import game.enemies as enemies

pygame.init()
pygame.display.set_caption('Raycaster Level Editor')
TILEMAP = Tilemap(1024)
SIDEBAR = Sidebar(512, 1024)
DISPLAY = pygame.display.set_mode((TILEMAP.surface_size + SIDEBAR.rect.w, max((TILEMAP.surface_size, SIDEBAR.rect.h))))
CLOCK = pygame.time.Clock()

FONT_SIZE = 16
FONT = pygame.font.Font('../font/LCD_Solid.ttf', FONT_SIZE)

ACTIVE_VALUE = 0

get_tilevaluesinfo()
create_sidebar_objects()

QUIT = False
while not QUIT:
    DISPLAY.fill(Colour.black)
    MOUSE_X, MOUSE_Y = pygame.mouse.get_pos()
    TILEMAP.calc_tile_size_and_pos()
    SIDEBAR.update_messages()

    events()

    TILEMAP.draw()
    SIDEBAR.draw()

    pygame.display.flip()
    CLOCK.tick(60)

pygame.quit()
