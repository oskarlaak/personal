# TO DO
# Make sidebar where you can choose textures with mouse
# Replace endtrigger textures with just one end trigger block
# Add player start block and a place to put starting angle in

import raycasting.tilevaluesinfo as tilevaluesinfo
import pygame

# Make an empty 64x64 tilemap
TILEMAP = []
for _ in range(64):
    row = []
    for _ in range(64):
        row.append(0)
    TILEMAP.append(row)


def draw_tilemap():
    # Draw 64x64 grid
    for x in range(65):
        pygame.draw.line(DISPLAY, (128, 128, 128), (x * TILE_SIZE, 0), (x * TILE_SIZE, 1024))
    for y in range(65):
        pygame.draw.line(DISPLAY, (128, 128, 128), (0, y * TILE_SIZE), (1024, y * TILE_SIZE))

    # Draw textures
    for row in range(len(TILEMAP)):
        for column in range(len(TILEMAP[row])):
            tile_value = TILEMAP[row][column]
            if tile_value != 0:
                texture = TILE_VALUES_INFO[tile_value][1]  # Get the full texture
                texture = texture.subsurface(0, 0, 64, 64)  # Crop 64x64 image out of image
                texture = pygame.transform.scale(texture, (TILE_SIZE, TILE_SIZE))  # Scale it to tile size
                DISPLAY.blit(texture, (column * TILE_SIZE, row * TILE_SIZE))


def mouse():
    # If mouse left button pressed down
    if pygame.mouse.get_pressed()[0] == True:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x < 64 * TILE_SIZE and mouse_y < 64 * TILE_SIZE:
            tile_x = int(mouse_x / TILE_SIZE)
            tile_y = int(mouse_y / TILE_SIZE)
            TILEMAP[tile_y][tile_x] = ACTIVE_VALUE


def draw_sidebar():
    pygame.draw.rect(DISPLAY, (0, 0, 0), (1024, 0, 1024 + SIDEBAR_W, 1024))

    # Draw active texture
    if ACTIVE_VALUE != 0:
        active_texture = TILE_VALUES_INFO[ACTIVE_VALUE][1].subsurface(0, 0, 64, 64)
        DISPLAY.blit(active_texture, (1024, 0))


pygame.init()
SIDEBAR_W = 64
DISPLAY = pygame.display.set_mode((1024 + SIDEBAR_W, 1024))
CLOCK = pygame.time.Clock()

TILE_VALUES_INFO = tilevaluesinfo.get(64)[0]
TILE_SIZE = 16  # Tile size on screen (pixels)
ACTIVE_VALUE = 0

done = False
while not done:
    DISPLAY.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                ACTIVE_VALUE += 1
                if ACTIVE_VALUE not in TILE_VALUES_INFO:
                    ACTIVE_VALUE -= 1
            elif event.button == 5:
                ACTIVE_VALUE -= 1
                if ACTIVE_VALUE not in TILE_VALUES_INFO:
                    ACTIVE_VALUE += 1

    mouse()
    draw_tilemap()
    draw_sidebar()

    pygame.display.flip()
    CLOCK.tick(30)

pygame.quit()
