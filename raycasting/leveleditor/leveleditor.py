# TO DO
# Level load function
# Level saved indicator

import math
import raycasting.main.tilevaluesinfo as tilevaluesinfo
import pygame
import sys
import os

# Colours
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

NUMBERS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)


class Texturegroup:
    def __init__(self, pos, value):
        self.x, self.y = pos
        self.active = False
        self.rect = pygame.Rect((self.x, self.y), (64, 64))
        self.value = value
        self.values = [value]

    def draw(self, surface):
        texture = TILE_VALUES_INFO[self.value][1]
        surface.blit(texture, (self.x, self.y))

        # If active, draw the rectangle around block red
        if self.active:
            color = (255, 0, 0)
            if self.value - 1 in self.values:
                surface.blit(ARROW_UP, (self.x + 16, self.y - 24))
            if self.value + 1 in self.values:
                surface.blit(ARROW_DOWN, (self.x + 16, self.y + 72))
        else:
            color = (255, 255, 255)
        pygame.draw.rect(surface, color, self.rect, 1)


class Inputbox:
    text_color = BLACK

    def __init__(self, rect, caption, limit=999):
        self.caption = myfont.render(caption, True, WHITE)
        self.active = False
        self.limit = limit
        self.rect = pygame.Rect(rect)
        self.text = ''
        self.text_surface = myfont.render(self.text, True, Inputbox.text_color)

    def draw(self, surface):
        # Draw inputbox background
        if self.text == '' or int(self.text) <= self.limit:
            if self.active:
                background_color = WHITE
            else:
                background_color = GREY
        else:  # if self.text > 255:
            background_color = RED
        pygame.draw.rect(surface, background_color, self.rect)

        # Draw inputbox text
        text_offset = ((self.rect.w - self.text_surface.get_width())  / 2,
                       (self.rect.h - self.text_surface.get_height()) / 2)
        surface.blit(self.text_surface, (self.rect.x + text_offset[0], self.rect.y + text_offset[1]))

        # Draw caption text
        surface.blit(self.caption, (self.rect.x - self.caption.get_width(), self.rect.y + text_offset[1]))


class Anglebox:
    def __init__(self, rect, image):
        self.rect = pygame.Rect(rect)
        self.angle = 0
        self.image = image

    def rotate(self, degrees):
        self.angle += degrees
        if self.angle < -180:
            self.angle += 360
        TILEMAP.starting_angle = math.radians(-self.angle)

    def draw(self, surface):
        pygame.draw.rect(surface, GREEN, self.rect)
        surface.blit(pygame.transform.rotate(self.image, self.angle), (self.rect.x, self.rect.y))


class Tilemap:
    def __init__(self):
        self.list = []
        for _ in range(64):
            row = []
            for _ in range(64):
                row.append(0)
            self.list.append(row)

        self.size = 64  # How many tiles can be seen on screen
        self.offset = [0, 0]  # Position of top left tile when zoomed in or not
        self.tile_size = 16  # Tile size on screen (pixels)
        self.starting_angle = 0  # This value will be in radians

    def new(self):
        self.__init__()

    def save(self):
        def get_player_pos():
            # Scan and find player start pos
            # Getting player pos in function to break out from double for loop with return
            for row in range(len(self.list)):
                for column in range(len(self.list[row])):
                    if TILE_VALUES_INFO[self.list[row][column]][0] == ('Special', 'Start'):
                        # Return tile to normal
                        self.list[row][column] = 0

                        # +0.5 centers player position in tile
                        return column + 0.5, row + 0.5

        start_x, start_y = get_player_pos()

        filepath = '../levels/{}/tilemap.txt'.format(LEVEL_NR.text)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Creates filepath directory if it's not there already
        # Start writing the file
        with open(filepath, 'w') as f:
            f.write('{}, {}, {}\n'.format(start_x, start_y, self.starting_angle))  # Player x, y, starting angle
            f.write('{}, {}, {}\n'.format(RGBS[0].text, RGBS[1].text, RGBS[2].text))  # Ceiling colour
            f.write('{}, {}, {}\n'.format(RGBS[3].text, RGBS[4].text, RGBS[5].text))  # Floor colour
            for row in self.list:
                f.write('{}\n'.format(row))  # Tilemap rows

        # Add player start item back to editor
        for value, (type, _) in TILE_VALUES_INFO.items():
            if type == ('Special', 'Start'):
                self.list[int(start_y)][int(start_x)] = value
                break


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
                texture = TILE_VALUES_INFO[tile_value][1]  # Get the texture
                texture = pygame.transform.scale(texture, (TILEMAP.tile_size, TILEMAP.tile_size))  # Scale it to tile size
                DISPLAY.blit(texture, (x * TILEMAP.tile_size, y * TILEMAP.tile_size))


def apply_texture():
    tile_x = int(MOUSE_X / TILEMAP.tile_size) + TILEMAP.offset[0]
    tile_y = int(MOUSE_Y / TILEMAP.tile_size) + TILEMAP.offset[1]
    TILEMAP.list[tile_y][tile_x] = ACTIVE_VALUE


def draw_sidebar():
    # Active value texture
    active_texture = TILE_VALUES_INFO[ACTIVE_VALUE][1]
    DISPLAY.blit(pygame.transform.scale(active_texture, (128, 128)), (1024 + 32, 0 + 16))

    # Active value description
    activeitem_text = myfont.render('ACTIVE ITEM:', True, WHITE)
    item_type = myfont.render('{}:'.format(TILE_VALUES_INFO[ACTIVE_VALUE][0][0]), True, WHITE)
    item_description = myfont.render(TILE_VALUES_INFO[ACTIVE_VALUE][0][1], True, WHITE)

    DISPLAY.blit(activeitem_text, (1152 + 32, 0 + 16))
    DISPLAY.blit(item_type, (1152 + 32,  20 + 16))
    DISPLAY.blit(item_description, (1152 + 32, 40 + 16))

    # Draw texturegroups
    for tg in TEXTUREGROUPS:
        tg.draw(DISPLAY)

    # Draw rgb boxes
    ceiling_text = myfont.render('CEILING COLOUR', True, WHITE)
    floor_text = myfont.render('FLOOR COLOUR', True, WHITE)
    DISPLAY.blit(ceiling_text, (RGBS[0].rect.x, RGBS[0].rect.y - FONT_SIZE))
    DISPLAY.blit(  floor_text, (RGBS[3].rect.x, RGBS[3].rect.y - FONT_SIZE))
    for ib in RGBS:
        ib.draw(DISPLAY)

    # Draw level number box
    LEVEL_NR.draw(DISPLAY)

    # Draw starting angle box
    starting_angle_text = myfont.render('STARTING ANGLE:', True, WHITE)
    DISPLAY.blit(starting_angle_text, (ANGLEBOX.rect.x, ANGLEBOX.rect.y - FONT_SIZE))
    ANGLEBOX.draw(DISPLAY)


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
    global DONE
    global ACTIVE_VALUE

    # Event handling that checks mouse and keyboard inputs
    # Also checks pygame quit event

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            DONE = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if MOUSE_X > 1024:
                    # Activate/deactivate texturegroups
                    for tg in TEXTUREGROUPS:
                        if tg.rect.collidepoint(MOUSE_X, MOUSE_Y):
                            tg.active = True
                            ACTIVE_VALUE = tg.value
                        else:
                            tg.active = False

                    # Activate/deactivate inputboxes
                    for ib in INPUTBOXES:
                        if ib.rect.collidepoint(MOUSE_X, MOUSE_Y):
                            ib.active = True
                        else:
                            ib.active = False

                    if ANGLEBOX.rect.collidepoint(MOUSE_X, MOUSE_Y):
                        ANGLEBOX.rotate(-90)

            if event.button == 4:  # Scroll wheel up
                # If control pressed down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    zoom(True)

                # If control not pressed down
                else:
                    for tg in TEXTUREGROUPS:
                        if tg.active:
                            if ACTIVE_VALUE - 1 in tg.values:
                                tg.value -= 1
                                ACTIVE_VALUE = tg.value
                            break

            elif event.button == 5:  # Scroll wheel down
                # If control pressed down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    zoom(False)

                # If control not pressed down
                else:
                    for tg in TEXTUREGROUPS:
                        if tg.active:
                            if ACTIVE_VALUE + 1 in tg.values:
                                tg.value += 1
                                ACTIVE_VALUE = tg.value
                            break

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                TILEMAP.save()

            for ib in INPUTBOXES:
                if ib.active:
                    if event.key == pygame.K_BACKSPACE:
                        ib.text = ib.text[:-1]
                    elif pygame.key.name(event.key).isdigit() and len(ib.text) < 3:  # rgb values cannot be < 3 digits
                        ib.text += event.unicode
                    # Re-render the text
                    ib.text_surface = myfont.render(ib.text, True, Inputbox.text_color)
                    break

    # If mouse left button pressed down and mouse inside tilemap area
    if pygame.mouse.get_pressed()[0] == True:
        if MOUSE_X < 1024:
            apply_texture()


def create_inputboxes():
    rgbs = []
    # Ceiling colour
    rgbs.append(Inputbox((1024 +  64, 1024 - 256, 40, FONT_SIZE), 'R:', 255))
    rgbs.append(Inputbox((1024 + 128, 1024 - 256, 40, FONT_SIZE), 'G:', 255))
    rgbs.append(Inputbox((1024 + 192, 1024 - 256, 40, FONT_SIZE), 'B:', 255))
    # Floor colour
    rgbs.append(Inputbox((1024 +  64, 1024 - 192, 40, FONT_SIZE), 'R:', 255))
    rgbs.append(Inputbox((1024 + 128, 1024 - 192, 40, FONT_SIZE), 'G:', 255))
    rgbs.append(Inputbox((1024 + 192, 1024 - 192, 40, FONT_SIZE), 'B:', 255))
    # Level number
    level_nr = Inputbox((1024 + 384, 1024 - 192, 40, FONT_SIZE), 'LEVEL NR:')

    # Create starting angle "box" on sidebar
    anglebox = Anglebox((1024 + 288, 1024 - 256, 32, 32), RED_ARROW)
    return rgbs, level_nr, anglebox


def get_tilevaluesinfo():
    try:
        global ARROW_UP
        global ARROW_DOWN
        global RED_ARROW
        ARROW_UP = pygame.image.load('arrow.png').convert()
        ARROW_DOWN = pygame.transform.flip(ARROW_UP, False, True)
        RED_ARROW = pygame.image.load('redarrow.png').convert_alpha()

        eraser = pygame.image.load('eraser.png').convert()
        start = pygame.transform.scale(pygame.image.load('start.png').convert(), (64, 64))
        end = pygame.transform.scale(pygame.image.load('end.png').convert(), (64, 64))

    except pygame.error as exception:
        sys.exit(exception)

    else:
        # Get TILE_VALUES_INFO from tilevaluesinfo.py
        tile_values_info = tilevaluesinfo.get(64)[0]

        # Replace all textures in it with 64x64 pixel textures
        for value in tile_values_info:
            if value != 0:
                texture = tile_values_info[value][1]
                tile_values_info[value] = tile_values_info[value][0], texture.subsurface(0, 0, 64, 64)

        # Replace two end-trigger textures with start and end texture
        for value, (info, _) in tile_values_info.items():
            if info == ('Wall', 'End-trigger'):
                tile_values_info[value] = ('Special', 'End-trigger'), end
                tile_values_info[value + 1] = ('Special', 'Start'), start
                break

        # Add eraser texture to value 0
        tile_values_info[0] = ('Special', 'Eraser'), eraser

        return tile_values_info


def get_texturegroups():
    heights = {
        'Enemy': 192,
        'Object': 288,
        'Door': 384,
        'Wall': 480,
        'Special': 576
    }

    texturegroups = []
    infos = []
    start_x = 1024 + 32

    for value, (info, _) in TILE_VALUES_INFO.items():
        if info not in infos:  # If the need to create a new texturegroup
            x = start_x
            for i in infos:  # For every texturegroup with same tpye, add 80 to x
                if i[0] == info[0]:
                    x += 80
            texturegroups.append(Texturegroup((x, heights[info[0]]), value))
            infos.append(info)
        else:
            texturegroups[-1].values.append(value)
            if value < 0:
                texturegroups[-1].value = value

    return texturegroups


pygame.init()

DISPLAY = pygame.display.set_mode((1024 + 528, 1024))  # 528 is the sidebar width
CLOCK = pygame.time.Clock()

pygame.font.init()
FONT_SIZE = 20
myfont = pygame.font.SysFont('franklingothicmedium', FONT_SIZE)

TILEMAP = Tilemap()
ACTIVE_VALUE = 0

TILE_VALUES_INFO = get_tilevaluesinfo()
TEXTUREGROUPS = get_texturegroups()

RGBS, LEVEL_NR, ANGLEBOX = create_inputboxes()
INPUTBOXES = RGBS + [LEVEL_NR]

DONE = False
while not DONE:
    DISPLAY.fill(BLACK)
    MOUSE_X, MOUSE_Y = pygame.mouse.get_pos()

    events()
    draw_tilemap()
    draw_sidebar()

    pygame.display.flip()
    CLOCK.tick(30)

pygame.quit()
