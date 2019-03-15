# TO DO
# Level editor README file describing how to use it


class TextureBox:
    def draw_box_outline_and_arrows(self):
        if self.active:
            outline_color = RED
            arrow_w, arrow_h = ARROW_UP.get_size()
            if self.value - 1 in self.values:
                DISPLAY.blit(ARROW_UP, (self.rect.x + (self.rect.w - arrow_w) / 2,
                                        self.rect.y - arrow_h - 8))
            if self.value + 1 in self.values:
                DISPLAY.blit(ARROW_DOWN, (self.rect.x + (self.rect.w - arrow_w) / 2,
                                          self.rect.y + self.rect.h + 8))
        else:
            outline_color = WHITE
        pygame.draw.rect(DISPLAY, outline_color, self.rect, 1)


class TextureGroup(TextureBox):
    def __init__(self, pos, value):
        self.rect = pygame.Rect(pos, (64, 64))
        self.value = value  # Current texturegroup value
        self.values = [value]  # All possible texturegroup values

        self.active = False

    def draw(self):
        texture = TILE_VALUES_INFO[self.value].texture
        DISPLAY.blit(texture, (self.rect.x, self.rect.y))

        self.draw_box_outline_and_arrows()


class SkyTexture(TextureBox):
    def __init__(self, pos, textures):
        self.rect = pygame.Rect(pos, (512, 50))
        self.value = 0
        self.values = [x for x in range(len(textures))]

        self.textures = textures
        self.text_surface = FONT.render('SKY TEXTURE:', False, WHITE)

        self.active = False

    def draw(self):
        # Draw text
        DISPLAY.blit(self.text_surface, (1024 + 32, self.rect.y - 16))
        # Draw sky texture
        DISPLAY.blit(pygame.transform.scale(self.textures[self.value], (512, 50)), (self.rect.x, self.rect.y))

        self.draw_box_outline_and_arrows()


class InputBox:
    def __init__(self, pos, caption, limit=999):
        self.rect = pygame.Rect(pos, (40, FONT_SIZE))

        self.caption = FONT.render(caption, False, WHITE)
        self.limit = limit
        self.text = ''

        self.active = False

    def draw(self):
        # Draw inputbox background
        if self.text == '' or int(self.text) <= self.limit:
            if self.active:
                background_color = WHITE
            else:
                background_color = GREY
        else:  # if self.text > limit:
            background_color = RED
        pygame.draw.rect(DISPLAY, background_color, self.rect)

        # Draw inputbox text
        text_surface = FONT.render(self.text, False, InputBox.text_color)
        text_offset = (self.rect.w - text_surface.get_width()) / 2

        DISPLAY.blit(text_surface, (self.rect.x + text_offset, self.rect.y))

        # Draw caption text
        DISPLAY.blit(self.caption, (self.rect.x - self.caption.get_width(), self.rect.y))


class AngleBox:
    def __init__(self, pos, image):
        self.rect = pygame.Rect(pos, image.get_size())
        self.image = image
        self.angle = 0

    def rotate(self, radians):
        self.angle += radians
        if self.angle <= -math.pi:
            self.angle += math.pi * 2

    def draw(self):
        DISPLAY.blit(pygame.transform.rotate(self.image, math.degrees(self.angle)), (self.rect.x, self.rect.y))


class Tilemap:
    def __init__(self):
        # Create new empty 64x64 tilemap
        self.list = []
        for _ in range(64):
            row = []
            for _ in range(64):
                row.append(0)
            self.list.append(row)

        self.size = 64  # How many tiles can be seen on screen
        self.offset = [0, 0]  # Position of top left tile when zoomed in or not
        self.tile_size = 16  # Tile size on screen (pixels)

        self.saved = None  # None bc False means that there was an error saving/loading
        self.loaded = None

    def new(self):
        # Reset anglebox
        ANGLEBOX.angle = 0
        # Reset rgb values
        for rgb in RGBS:
            rgb.text = ''
        # Reset sky texture
        SKYTEXTURE.value = 0
        # Set level nr to smallest number from 1 that's not in levels folder
        level_nr = 1
        while str(level_nr) in os.listdir('../levels'):
            level_nr += 1
        LEVEL_NR.text = str(level_nr)

        self.__init__()

    def save(self):
        # Tries to save tilemap and puts self.saved to either True or False depending on if it's possible or not

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

        self.message_ticks = 90
        self.loaded = None
        self.saved = False

        start_x, start_y = get_player_pos()
        if start_x and start_y:  # If start item placed

            for rgb in RGBS:  # Check if rgb values are ok
                if rgb.text == '' or int(rgb.text) > rgb.limit:
                    break

            else:  # If rgb-s fine
                if LEVEL_NR.text != '':  # If level number box not empty

                    # Creates filepath directory if it's not there already
                    filepath = '../levels/{}/tilemap.txt'.format(LEVEL_NR.text)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)

                    # Start writing the file
                    with open(filepath, 'w') as f:
                        f.write('{},{},{}\n'.format(start_x, start_y, ANGLEBOX.angle))  # Player x, y, starting angle
                        f.write('{},{},{}\n'.format(RGBS[0].text, RGBS[1].text, RGBS[2].text))  # Ceiling colour
                        f.write('{},{},{}\n'.format(RGBS[3].text, RGBS[4].text, RGBS[5].text))  # Floor colour
                        for row in self.list:
                            f.write('{}\n'.format(row))  # Tilemap rows

                    save_path = '../levels/{}/sky.png'.format(LEVEL_NR.text)
                    if SKYTEXTURE.value > 0:
                        pygame.image.save(SKYTEXTURE.textures[SKYTEXTURE.value], save_path)  # Saves sky texture
                    elif os.path.exists(save_path):
                        os.remove(save_path)

                    self.saved = True  # Saved without errors

            # Add player start item back to editor
            self.list[int(start_y)][int(start_x)] = START_VALUE

    def load(self):
        self.message_ticks = 90
        self.saved = None
        try:
            with open('../levels/{}/tilemap.txt'.format(LEVEL_NR.text), 'r') as f:
                player_x, player_y, player_angle = [float(i) for i in f.readline().replace('\n', '').split(',')]
                # Update anglebox angle
                ANGLEBOX.angle = player_angle

                # Level nr
                LEVEL_NR.text = str(LEVEL_NR.text)
                # Ceiling colour
                RGBS[0].text, RGBS[1].text, RGBS[2].text = f.readline().replace('\n', '').split(',')
                # Floor colour
                RGBS[3].text, RGBS[4].text, RGBS[5].text = f.readline().replace('\n', '').split(',')

                # Update SKYTEXTURE value
                try:
                    sky_texture = pygame.image.load('../levels/{}/sky.png'.format(LEVEL_NR.text)).convert()
                except pygame.error:
                    SKYTEXTURE.value = 0
                else:
                    for value, st in enumerate(SKYTEXTURE.textures):
                        if st == sky_texture:
                            SKYTEXTURE.value = value
                            break

                # Update the tilemap
                self.list = []
                for line in f:
                    row = line.replace('\n', '')  # Get rid of newline (\n)
                    row = row[1:-1]  # Get rid of '[' and ']'
                    row = row.split(',')  # Split line into list
                    row = [int(i) for i in row]  # Turn all number strings to an int
                    self.list.append(row)
                # Add player start tile to tilemap
                self.list[int(player_y)][int(player_x)] = START_VALUE
            self.loaded = True

        except FileNotFoundError:
            self.loaded = False

    def status_update(self):
        def scale(image, times):
            image_w, image_h = image.get_size()
            return pygame.transform.scale(image, (int(image_w * times), int(image_h * times)))

        message_pos = (1024 + 290, 16)

        if self.saved != None:
            if self.saved:
                message_text = FONT.render('SAVED', False, GREEN)
                DISPLAY.blit(scale(message_text, 1.5), message_pos)
            else:
                message_text = FONT.render('SAVE FAILED', False, RED)
                DISPLAY.blit(scale(message_text, 1.5), message_pos)

            self.message_ticks -= 1
            if self.message_ticks == 0:
                self.saved = None

        elif self.loaded != None:
            if self.loaded:
                message_text = FONT.render('LOAD SUCCESSFUL', False, GREEN)
                DISPLAY.blit(scale(message_text, 1.5), message_pos)
            else:
                message_text = FONT.render('LOAD FAILED', False, RED)
                DISPLAY.blit(scale(message_text, 1.5), message_pos)

            self.message_ticks -= 1
            if self.message_ticks == 0:
                self.loaded = None


def draw_tilemap():
    # Draw grid
    pygame.draw.rect(DISPLAY, WHITE, (0, 0, 1024, 1024))
    lines = int(1024 / TILEMAP.tile_size) + 1
    for x in range(lines):
        pygame.draw.line(DISPLAY, GREY, (x * TILEMAP.tile_size, 0), (x * TILEMAP.tile_size, 1024))
    for y in range(lines):
        pygame.draw.line(DISPLAY, GREY, (0, y * TILEMAP.tile_size), (1024, y * TILEMAP.tile_size))

    # Draw textures
    for y, row in enumerate(range(TILEMAP.offset[1], TILEMAP.offset[1] + TILEMAP.size)):
        for x, column in enumerate(range(TILEMAP.offset[0], TILEMAP.offset[0] + TILEMAP.size)):
            tile_value = TILEMAP.list[row][column]
            if tile_value != 0:
                texture = TILE_VALUES_INFO[tile_value].texture  # Get the texture
                texture = pygame.transform.scale(texture, (TILEMAP.tile_size, TILEMAP.tile_size))  # Scale it to tile size
                DISPLAY.blit(texture, (x * TILEMAP.tile_size, y * TILEMAP.tile_size))


def apply_texture():
    # If item placed was player start item,
    # remove previously placed player start item from tilemap
    # This is done because level can only have 1 player start item
    if ACTIVE_VALUE == START_VALUE:
        for row in range(len(TILEMAP.list)):
            for column in range(len(TILEMAP.list[row])):
                if TILEMAP.list[row][column] == START_VALUE:
                    # Return tile to normal
                    TILEMAP.list[row][column] = 0

    tile_x = int(MOUSE_X / TILEMAP.tile_size) + TILEMAP.offset[0]
    tile_y = int(MOUSE_Y / TILEMAP.tile_size) + TILEMAP.offset[1]
    TILEMAP.list[tile_y][tile_x] = ACTIVE_VALUE


def draw_sidebar():
    # Active value texture
    active_texture = TILE_VALUES_INFO[ACTIVE_VALUE].texture
    DISPLAY.blit(pygame.transform.scale(active_texture, (128, 128)), (1024 + 32, 0 + 16))

    # Active value description
    activeitem_text = FONT.render('ACTIVE ITEM:', False, WHITE)
    item_type = FONT.render('{}:'.format(TILE_VALUES_INFO[ACTIVE_VALUE].type), False, WHITE)
    item_description = FONT.render(TILE_VALUES_INFO[ACTIVE_VALUE].desc, False, WHITE)

    DISPLAY.blit(activeitem_text, (1152 + 32, 0 + 16))
    DISPLAY.blit(item_type, (1152 + 32,  20 + 16))
    DISPLAY.blit(item_description, (1152 + 32, 40 + 16))

    # Draw texturegroups
    for tg in TEXTUREGROUPS:
        tg.draw()

    # Draw rgb boxes
    ceiling_text = FONT.render('CEILING COLOUR', False, WHITE)
    floor_text = FONT.render('FLOOR COLOUR', False, WHITE)
    DISPLAY.blit(ceiling_text, (RGBS[0].rect.x, RGBS[0].rect.y - FONT_SIZE))
    DISPLAY.blit(  floor_text, (RGBS[3].rect.x, RGBS[3].rect.y - FONT_SIZE))
    for ib in RGBS:
        ib.draw()

    # Draw level number box
    LEVEL_NR.draw()

    # Draw starting angle box
    starting_angle_text = FONT.render('STARTING ANGLE:', False, WHITE)
    DISPLAY.blit(starting_angle_text, (ANGLEBOX.rect.x, ANGLEBOX.rect.y - FONT_SIZE))
    ANGLEBOX.draw()

    SKYTEXTURE.draw()


def zoom(in_):

    # Calculate the tile the mouse is in when zoomed
    if MOUSE_X < 1024:
        tile_x = int(MOUSE_X / TILEMAP.tile_size) + TILEMAP.offset[0]
        tile_y = int(MOUSE_Y / TILEMAP.tile_size) + TILEMAP.offset[1]

        can_zoom = False
        if in_:
            if TILEMAP.tile_size < 128:
                TILEMAP.tile_size *= 2
                can_zoom = True
        else:
            if TILEMAP.tile_size > 16:
                TILEMAP.tile_size /= 2
                can_zoom = True

        if can_zoom:
            TILEMAP.tile_size = int(TILEMAP.tile_size)
            TILEMAP.size = int(1024 / TILEMAP.tile_size)
            TILEMAP.offset = [int(tile_x - TILEMAP.size / 2),
                              int(tile_y - TILEMAP.size / 2)]

            # Reset x offset if needed
            if TILEMAP.offset[0] < 0:
                TILEMAP.offset[0] = 0
            elif TILEMAP.offset[0] + TILEMAP.size > 64:
                TILEMAP.offset[0] = 64 - TILEMAP.size

            # Reset y offset if needed
            if TILEMAP.offset[1] < 0:
                TILEMAP.offset[1] = 0
            elif TILEMAP.offset[1] + TILEMAP.size > 64:
                TILEMAP.offset[1] = 64 - TILEMAP.size


def events():
    global QUIT
    global ACTIVE_VALUE

    # Event handling that checks mouse and keyboard inputs
    # Also checks pygame quit event

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            QUIT = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if MOUSE_X > 1024:
                    # Activate/deactivate sidebar objects
                    for sidebar_obj in TEXTUREGROUPS + [SKYTEXTURE] + INPUTBOXES:
                        if sidebar_obj.rect.collidepoint(MOUSE_X, MOUSE_Y):
                            sidebar_obj.active = True
                            if sidebar_obj in TEXTUREGROUPS:
                                ACTIVE_VALUE = sidebar_obj.value
                        else:
                            sidebar_obj.active = False

                    if ANGLEBOX.rect.collidepoint(MOUSE_X, MOUSE_Y):
                        ANGLEBOX.rotate(-math.pi / 2)

            elif event.button == 4:  # Scroll wheel up
                # If control pressed down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    zoom(True)

                # If control not pressed down
                else:
                    for scrollable_obj in TEXTUREGROUPS + [SKYTEXTURE]:
                        if scrollable_obj.active:
                            if scrollable_obj.value - 1 in scrollable_obj.values:
                                scrollable_obj.value -= 1
                                if scrollable_obj in TEXTUREGROUPS:
                                    ACTIVE_VALUE = scrollable_obj.value
                            break

            elif event.button == 5:  # Scroll wheel down
                # If control pressed down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    zoom(False)

                # If control not pressed down
                else:
                    for scrollable_obj in TEXTUREGROUPS + [SKYTEXTURE]:
                        if scrollable_obj.active:
                            if scrollable_obj.value + 1 in scrollable_obj.values:
                                scrollable_obj.value += 1
                                if scrollable_obj in TEXTUREGROUPS:
                                    ACTIVE_VALUE = scrollable_obj.value
                            break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.new()

            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.save()

            elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.load()

            else:
                for ib in INPUTBOXES:
                    if ib.active:
                        if event.key == pygame.K_BACKSPACE:
                            ib.text = ib.text[:-1]
                        elif pygame.key.name(event.key).isdigit() and len(ib.text) < 3:  # rgb values cannot be < 3 digits
                            ib.text += event.unicode
                        break

    # If mouse left button pressed down and mouse inside tilemap area
    if pygame.mouse.get_pressed()[0] == True:
        if MOUSE_X < 1024:
            apply_texture()

def create_sidebar_objects():
    def create_texturegroups():
        tg_heights = {  # Texturegroup heights
            'Enemy': 192,
            'Object': 288,
            'Door': 384,
            'Wall': 480,
            'Special': 576
        }

        texturegroups = []
        infos = []
        start_x = 1024 + 32

        for value in TILE_VALUES_INFO:
            info = (TILE_VALUES_INFO[value].type, TILE_VALUES_INFO[value].desc)
            if info not in infos:  # If the need to create a new texturegroup
                x = start_x
                for i in infos:  # For every texturegroup with same tpye, add 80 to x
                    if i[0] == info[0]:
                        x += 80
                texturegroups.append(TextureGroup((x, tg_heights[info[0]]), value))
                infos.append(info)
            else:
                texturegroups[-1].values.append(value)
                if value < 0:
                    texturegroups[-1].value = value

        return texturegroups

    def create_skytexturebox():
        skytextures = [pygame.image.load('defaultskytexture.png').convert()]
        for skytexture_name in os.listdir('../textures/skies'):
            skytextures.append(pygame.image.load('../textures/skies/{}'.format(skytexture_name)).convert())
        skytexture = SkyTexture((1024 + 8, 1024 - 96), skytextures)
        return skytexture

    def create_inputboxes():
        rgbs = []
        # Ceiling colour
        rgbs.append(InputBox((1024 +  64, 1024 - 256), 'R:', 255))
        rgbs.append(InputBox((1024 + 128, 1024 - 256), 'G:', 255))
        rgbs.append(InputBox((1024 + 192, 1024 - 256), 'B:', 255))
        # Floor colour
        rgbs.append(InputBox((1024 +  64, 1024 - 192), 'R:', 255))
        rgbs.append(InputBox((1024 + 128, 1024 - 192), 'G:', 255))
        rgbs.append(InputBox((1024 + 192, 1024 - 192), 'B:', 255))
        # Level number
        level_nr = InputBox((1024 + 384, 1024 - 192), 'LEVEL NR:')

        return rgbs, level_nr

    def create_anglebox():
        return AngleBox((1024 + 288, 1024 - 256), RED_ARROW)

    texturegroups = create_texturegroups()
    skytexture = create_skytexturebox()
    rgbs, level_nr = create_inputboxes()
    anglebox = create_anglebox()
    return texturegroups, skytexture, rgbs, level_nr, anglebox


def get_arrow_images():
    try:
        return pygame.image.load('redarrow.png').convert_alpha(),\
               pygame.image.load('arrow.png').convert()

    except pygame.error as loading_error:
        sys.exit(loading_error)


def get_tilevaluesinfo():
    try:
        eraser_texture = pygame.transform.scale(pygame.image.load('eraser.png').convert(), (64, 64))
        start_texture = pygame.transform.scale(pygame.image.load('start.png').convert(), (64, 64))
        end_texture = pygame.transform.scale(pygame.image.load('end.png').convert(), (64, 64))

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        # Get tile_values_info from graphics.py
        enemy_info = graphics.get_enemy_info(sys, pygame)
        tile_values_info = graphics.get_tile_values_info(sys, pygame, 64, enemy_info)

        # Replace all textures in it with 64x64 pixel textures
        for value in tile_values_info:
            if value != 0:
                tile_values_info[value].texture = tile_values_info[value].texture.subsurface(0, 0, 64, 64)

        # Replace two end-trigger textures with start and end texture
        for value in tile_values_info:
            if tile_values_info[value].desc  == 'End-trigger':
                tile_values_info[value].texture = end_texture
                tile_values_info[value].type = 'Special'

                start_block_value = value + 1
                tile_values_info[start_block_value].texture = start_texture
                tile_values_info[start_block_value].type = 'Special'
                tile_values_info[start_block_value].desc = 'Start'
                break

        # Add eraser texture to value 0
        tile_values_info[0].texture = eraser_texture
        tile_values_info[0].type = 'Special'
        tile_values_info[0].desc = 'Eraser'

        return tile_values_info, start_block_value


import math
import game.graphics as graphics
import pygame
import sys
import os

# Colours
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
InputBox.text_color = BLACK

pygame.init()
pygame.display.set_caption('Raycaster level editor')
DISPLAY = pygame.display.set_mode((1024 + 528, 1024))  # 528 is the sidebar width
CLOCK = pygame.time.Clock()

FONT_SIZE = 16
FONT = pygame.font.Font('../font/LCD_Solid.ttf', FONT_SIZE)

TILE_VALUES_INFO, START_VALUE = get_tilevaluesinfo()
TILEMAP = Tilemap()
ACTIVE_VALUE = 0

RED_ARROW, ARROW_UP = get_arrow_images()
ARROW_DOWN = pygame.transform.flip(ARROW_UP, False, True)

TEXTUREGROUPS, SKYTEXTURE, RGBS, LEVEL_NR, ANGLEBOX = create_sidebar_objects()
INPUTBOXES = RGBS + [LEVEL_NR]

QUIT = False
while not QUIT:
    DISPLAY.fill(BLACK)
    MOUSE_X, MOUSE_Y = pygame.mouse.get_pos()

    TILEMAP.status_update()
    events()
    draw_tilemap()
    draw_sidebar()

    pygame.display.flip()
    CLOCK.tick(60)

pygame.quit()
