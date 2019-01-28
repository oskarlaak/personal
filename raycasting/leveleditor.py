# TO DO
# Save, load, new buttons
# Divide normal walls into different themed groups

import raycasting.tilevaluesinfo as tilevaluesinfo
import pygame


class Texturegroup:
    def __init__(self, pos, value):
        self.pos = pos
        self.active = False
        self.rect = pygame.Rect(self.pos, (64, 64))
        self.value = value
        self.values = [value]

    def draw(self, surface):
        texture = TILE_VALUES_INFO[self.value][1]
        surface.blit(texture, self.pos)

        # If active, draw the rectangle around block red
        if self.active:
            color = (255, 0, 0)
        else:
            color = (255, 255, 255)
        pygame.draw.rect(DISPLAY, color, self.rect, 1)


def draw_tilemap():
    # Draw grid
    pygame.draw.rect(DISPLAY, (255, 255, 255), (0, 0, 1024, 1024))
    lines = int(1024 / TILE_SIZE) + 1
    for x in range(lines):
        pygame.draw.line(DISPLAY, (128, 128, 128), (x * TILE_SIZE, 0), (x * TILE_SIZE, 1024))
    for y in range(lines):
        pygame.draw.line(DISPLAY, (128, 128, 128), (0, y * TILE_SIZE), (1024, y * TILE_SIZE))

    # Draw textures
    for y, row in enumerate(range(TILEMAP_OFFSET[1], TILEMAP_OFFSET[1] + TILEMAP_SIZE)):
        for x, column in enumerate(range(TILEMAP_OFFSET[0], TILEMAP_OFFSET[0] + TILEMAP_SIZE)):
            tile_value = TILEMAP[row][column]
            if tile_value != 0:
                texture = TILE_VALUES_INFO[tile_value][1]  # Get the texture
                texture = pygame.transform.scale(texture, (TILE_SIZE, TILE_SIZE))  # Scale it to tile size
                DISPLAY.blit(texture, (x * TILE_SIZE, y * TILE_SIZE))


def apply_texture():
    tile_x = int(MOUSE_X / TILE_SIZE) + TILEMAP_OFFSET[0]
    tile_y = int(MOUSE_Y / TILE_SIZE) + TILEMAP_OFFSET[1]
    TILEMAP[tile_y][tile_x] = ACTIVE_VALUE


def draw_sidebar():
    # Active value texture
    active_texture = TILE_VALUES_INFO[ACTIVE_VALUE][1]
    DISPLAY.blit(pygame.transform.scale2x(active_texture), (1024, 0))

    # Active value description
    item_type = myfont.render('{}:'.format(TILE_VALUES_INFO[ACTIVE_VALUE][0][0]), True, (255, 255, 255))
    item_description = myfont.render(TILE_VALUES_INFO[ACTIVE_VALUE][0][1], True, (255, 255, 255))

    DISPLAY.blit(       item_type, (1152,  0))
    DISPLAY.blit(item_description, (1152, 20))

    # Draw texturegroups
    for tg in TEXTUREGROUPS:
        tg.draw(DISPLAY)


def zoom(in_):
    global TILE_SIZE
    global TILEMAP_SIZE
    global TILEMAP_OFFSET

    # Calculate the tile the mouse is in when zoomed
    if MOUSE_X < 1024:
        tile_x = int(MOUSE_X / TILE_SIZE) + TILEMAP_OFFSET[0]
        tile_y = int(MOUSE_Y / TILE_SIZE) + TILEMAP_OFFSET[1]

        can_zoom = False
        if in_:
            if TILE_SIZE < 128:
                TILE_SIZE *= 2
                can_zoom = True
        else:
            if TILE_SIZE > 16:
                TILE_SIZE /= 2
                can_zoom = True

        if can_zoom:
            TILE_SIZE = int(TILE_SIZE)
            TILEMAP_SIZE = int(1024 / TILE_SIZE)
            TILEMAP_OFFSET = [int(tile_x - TILEMAP_SIZE / 2),
                              int(tile_y - TILEMAP_SIZE / 2)]

            # Reset x offset if needed
            if TILEMAP_OFFSET[0] < 0:
                TILEMAP_OFFSET[0] = 0
            elif TILEMAP_OFFSET[0] + TILEMAP_SIZE > 64:
                TILEMAP_OFFSET[0] = 64 - TILEMAP_SIZE

            # Reset y offset if needed
            if TILEMAP_OFFSET[1] < 0:
                TILEMAP_OFFSET[1] = 0
            elif TILEMAP_OFFSET[1] + TILEMAP_SIZE > 64:
                TILEMAP_OFFSET[1] = 64 - TILEMAP_SIZE


def mouse_input():
    global DONE
    global ACTIVE_VALUE

    # Event handling that mainly checks for mouse inputs
    # Also checks pygame quit event

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            DONE = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if MOUSE_X > 1024:
                    for tg in TEXTUREGROUPS:
                        if tg.rect.collidepoint(MOUSE_X, MOUSE_Y):
                            tg.active = True
                            ACTIVE_VALUE = tg.value
                        else:
                            tg.active = False

            if event.button == 4:  # Scroll wheel up
                # If control pressed down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    zoom(True)

                # If control not pressed down
                else:
                    for tg in TEXTUREGROUPS:
                        if tg.rect.collidepoint(MOUSE_X, MOUSE_Y):
                            if tg.active and ACTIVE_VALUE + 1 in tg.values:
                                tg.value += 1
                                ACTIVE_VALUE += 1
                            break

            elif event.button == 5:  # Scroll wheel down
                # If control pressed down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    zoom(False)

                # If control not pressed down
                else:
                    for tg in TEXTUREGROUPS:
                        if tg.rect.collidepoint(MOUSE_X, MOUSE_Y):
                            if tg.active and ACTIVE_VALUE - 1 in tg.values:
                                tg.value -= 1
                                ACTIVE_VALUE -= 1
                            break

    # If mouse left button pressed down and mouse inside tilemap area
    if pygame.mouse.get_pressed()[0] == True:
        if MOUSE_X < 1024:
            apply_texture()


def get_tilevaluesinfo():
    # Get TILE_VALUES_INFO from tilevaluesinfo.py
    # and replace all textures in it with 64x64 pixel textures
    tile_values_info = tilevaluesinfo.get(64, True)[0]
    for value in tile_values_info:
        if value != 0:
            texture = tile_values_info[value][1]
            tile_values_info[value] = tile_values_info[value][0], texture.subsurface(0, 0, 64, 64)
    return tile_values_info


def new_tilemap():
    # Create an empty 64x64 tilemap
    tilemap = []
    for _ in range(64):
        row = []
        for _ in range(64):
            row.append(0)
        tilemap.append(row)

    tilemap_size = 64  # How many tiles can be seen on screen
    tilemap_offset = [0, 0]  # Position of top left tile when zoomed in or not
    tile_size = 16  # Tile size on screen (pixels)
    active_value = 0
    return tilemap, tilemap_size, tilemap_offset, tile_size, active_value


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

    return texturegroups


pygame.init()

DISPLAY = pygame.display.set_mode((1024 + 528, 1024))  # 528 is the sidebar width
CLOCK = pygame.time.Clock()

pygame.font.init()
FONT_SIZE = 20
myfont = pygame.font.SysFont('franklingothicmedium', FONT_SIZE)

TILEMAP,\
TILEMAP_SIZE,\
TILEMAP_OFFSET,\
TILE_SIZE,\
ACTIVE_VALUE = new_tilemap()

TILE_VALUES_INFO = get_tilevaluesinfo()

TEXTUREGROUPS = get_texturegroups()

DONE = False
while not DONE:
    DISPLAY.fill((0, 0, 0))
    MOUSE_X, MOUSE_Y = pygame.mouse.get_pos()

    mouse_input()
    draw_tilemap()
    draw_sidebar()

    pygame.display.flip()
    CLOCK.tick(30)

pygame.quit()
