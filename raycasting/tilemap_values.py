def get(texture_size):
    def assign_texture_sheet(cell_w, cell_h, sheet, step, name):
        global INDEX
        for row in range(int(sheet.get_height() / cell_h)):

            for column in range(int(sheet.get_width() / cell_w)):

                texture = sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                TILE_VALUES_INFO[INDEX] = (name, texture)
                INDEX += step

    import sys
    import pygame

    pygame.init()
    pygame.display.set_mode((1, 1))

    try:
        # Wall textures
        global DOOR_SIDE_TEXTURE  # Making var global to access it in send_rays()
        DOOR_SIDE_TEXTURE = pygame.image.load('textures/walls/door_side.png').convert()
        door_textures = pygame.image.load('textures/walls/doors.png').convert()
        wall_textures = pygame.image.load('textures/walls/other.png').convert()
        elevator_levers = pygame.image.load('textures/walls/elevator.png').convert()

        # Object sprites
        ammo_sprite = pygame.image.load('textures/objects/ammo.png').convert_alpha()
        health_sprite = pygame.image.load('textures/objects/health.png').convert_alpha()
        nonsolid_sprites = pygame.image.load('textures/objects/nonsolids.png').convert_alpha()
        solid_sprites = pygame.image.load('textures/objects/solids.png').convert_alpha()

        # Enemy sprites
        # Using names found from https://www.spriters-resource.com/pc_computer/wolfenstein3d/
        guard = pygame.image.load('textures/enemies/Guard.png').convert_alpha()
        ss = pygame.image.load('textures/enemies/SS.png').convert_alpha()

    except pygame.error as exception:
        sys.exit(exception)

    else:  # If no error when loading textures
        global ENEMY_INFO
        ENEMY_INFO = {
            # n: (spritesheet, hp)
            0: (guard, 3),
            1: (ss, 5)
        }

        TILE_VALUES_INFO = {}

        # ---OBJECTS---
        # Non-solid objects
        TILE_VALUES_INFO[-1] = ammo_sprite, 'ammo'
        TILE_VALUES_INFO[-2] = health_sprite, 'health'
        INDEX = -3
        assign_texture_sheet(texture_size, texture_size, nonsolid_sprites, -1, 'non-solid')

        # Solid objects
        INDEX = 0
        assign_texture_sheet(texture_size, texture_size, solid_sprites, 1, 'solid')

        # ----WALLS----
        # Because each wall texture "cell" contains two textures,
        # cell width is going to be twice as big as cell height
        cell_w = texture_size * 2
        cell_h = texture_size

        # Doors
        global DOOR_INDEX  # Regular door
        DOOR_INDEX = index
        texture = door_textures.subsurface(0, cell_h * 0, cell_w, cell_h)
        TILEMAP_TEXTURES[DOOR_INDEX] = texture
        TEXTURE_VALUES['door'] = index
        index += 1

        global ELEVATOR_INDEX  # Elevator door
        ELEVATOR_INDEX = index
        texture = door_textures.subsurface(0, cell_h * 1, cell_w, cell_h)
        TILEMAP_TEXTURES[ELEVATOR_INDEX] = texture
        TEXTURE_VALUES['elevator'] = index
        index += 1

        global DARK_ELEVATOR_INDEX  # "Fake" elevator door that can't be moved
        DARK_ELEVATOR_INDEX = index
        texture = door_textures.subsurface(0, cell_h * 2, cell_w, cell_h)
        TILEMAP_TEXTURES[DARK_ELEVATOR_INDEX] = texture
        TEXTURE_VALUES['dark_elevator'] = index
        index += 1

        a = index
        # Other walls
        for row in range(int(wall_textures.get_height() / cell_h)):

            for column in range(int(wall_textures.get_width() / cell_w)):
                texture = wall_textures.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                TILEMAP_TEXTURES[index] = texture
                index += 1
        TEXTURE_VALUES['walls'] = (a, index - 1)

        # Last two textures are always elevator lever textures
        global ELEVATOR_LEVER_INDEX
        ELEVATOR_LEVER_INDEX = index
        texture = elevator_levers.subsurface(0, cell_h * 0, cell_w, cell_h)
        TILEMAP_TEXTURES[index] = texture
        index += 1
        texture = elevator_levers.subsurface(0, cell_h * 1, cell_w, cell_h)
        TILEMAP_TEXTURES[index] = texture
        index += 1

        global ENEMY_START_INDEX
        ENEMY_START_INDEX = index  # index where enemies start to be from

        TEXTURE_VALUES = []
        TEXTURE_VALUES.append(DOOR_INDEX)
        TEXTURE_VALUES.append(ELEVATOR_INDEX)
        TEXTURE_VALUES.append(DARK_ELEVATOR_INDEX)
        TEXTURE_VALUES.append(ELEVATOR_LEVER_INDEX)
        TEXTURE_VALUES.append(ENEMY_START_INDEX)

        pygame.quit()

if __name__ == '__main__':
    get(64)