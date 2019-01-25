# TO DO
# Make sidebar where you can choose textures with mouse
# Replace endtrigger textures with just one end trigger block
# Add player start block and a place to put starting angle in

import raycasting.tilevaluesinfo as tilevaluesinfo
import pygame


def draw_tilemap():
    # Draw grid
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


def apply_texture(mouse_x, mouse_y):
    tile_x = int(mouse_x / TILE_SIZE) + TILEMAP_OFFSET[0]
    tile_y = int(mouse_y / TILE_SIZE) + TILEMAP_OFFSET[1]
    TILEMAP[tile_y][tile_x] = ACTIVE_VALUE


def draw_sidebar():
    pygame.draw.rect(DISPLAY, (0, 0, 0), (1024, 0, 1024 + SIDEBAR_W, 1024))

    # Draw active texture
    if ACTIVE_VALUE != 0:
        active_texture = TILE_VALUES_INFO[ACTIVE_VALUE][1]
        DISPLAY.blit(active_texture, (1024, 0))


def get_tilevaluesinfo():
    # Get TILE_VALUES_INFO from tilevaluesinfo.py
    # and replace all textures in it with 64x64 pixel textures
    global TILE_VALUES_INFO
    TILE_VALUES_INFO = tilevaluesinfo.get(64)[0]
    for value in TILE_VALUES_INFO:
        if value != 0:
            texture = TILE_VALUES_INFO[value][1]
            TILE_VALUES_INFO[value] = TILE_VALUES_INFO[value][0], texture.subsurface(0, 0, 64, 64)


def zoom(in_):
    global TILE_SIZE
    global TILEMAP_SIZE
    global TILEMAP_OFFSET

    # Calculate the tile the mouse is in when zoomed
    mouse_x, mouse_y = pygame.mouse.get_pos()
    tile_x = int(mouse_x / TILE_SIZE) + TILEMAP_OFFSET[0]
    tile_y = int(mouse_y / TILE_SIZE) + TILEMAP_OFFSET[1]

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


pygame.init()

SIDEBAR_W = 64
DISPLAY = pygame.display.set_mode((1024 + SIDEBAR_W, 1024))
CLOCK = pygame.time.Clock()

# Create an empty 64x64 tilemap
TILEMAP = []
for _ in range(64):
    row = []
    for _ in range(64):
        row.append(0)
    TILEMAP.append(row)

TILEMAP_SIZE = 64  # How many tiles can be seen on screen
TILEMAP_OFFSET = [0, 0]  # Position of top left tile when zoomed in or not
TILE_SIZE = 16  # Tile size on screen (pixels)
ACTIVE_VALUE = 0

get_tilevaluesinfo()

done = False
while not done:
    DISPLAY.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll wheel up
                if pygame.key.get_mods() & pygame.KMOD_CTRL:  # If control pressed down
                    zoom(True)
                else:
                    ACTIVE_VALUE += 1
                    if ACTIVE_VALUE not in TILE_VALUES_INFO:
                        ACTIVE_VALUE -= 1
            elif event.button == 5:  # Scroll wheel down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:  # If control pressed down
                    zoom(False)
                else:
                    ACTIVE_VALUE += -1
                    if ACTIVE_VALUE not in TILE_VALUES_INFO:
                        ACTIVE_VALUE -= -1

    # If mouse left button pressed down and mouse inside tilemap area
    if pygame.mouse.get_pressed()[0] == True:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x < 1024:
            apply_texture(mouse_x, mouse_y)

    draw_tilemap()
    draw_sidebar()

    pygame.display.flip()
    CLOCK.tick(30)

pygame.quit()
