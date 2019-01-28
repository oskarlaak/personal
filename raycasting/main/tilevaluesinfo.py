def get(texture_size):
    def assign_texture_sheet(cell_w, cell_h, sheet, step, type):
        global index
        for row in range(int(sheet.get_height() / cell_h)):

            for column in range(int(sheet.get_width() / cell_w)):

                texture = sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                TILE_VALUES_INFO[index] = (type, texture)
                index += step

    import sys
    import pygame

    try:
        # Wall textures
        wall_textures = pygame.image.load('../textures/walls/other.png').convert()
        end_trigger_textures = pygame.image.load('../textures/walls/endtrigger.png').convert()

        # Door textures
        DOOR_SIDE_TEXTURE = pygame.image.load('../textures/doors/side.png').convert()
        dynamic_door_textures = pygame.image.load('../textures/doors/dynamic.png').convert()
        static_door_textures = pygame.image.load('../textures/doors/static.png').convert()

        # Object sprites
        ammo_sprite = pygame.image.load('../textures/objects/ammo.png').convert_alpha()
        health_sprite = pygame.image.load('../textures/objects/health.png').convert_alpha()
        nonsolid_sprites = pygame.image.load('../textures/objects/nonsolids.png').convert_alpha()
        solid_sprites = pygame.image.load('../textures/objects/solids.png').convert_alpha()

        # Enemy sprites
        # Using enemy names found from https://www.spriters-resource.com/pc_computer/wolfenstein3d/
        guard = pygame.image.load('../textures/enemies/Guard.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/SS.png').convert_alpha()

    except pygame.error as exception:
        sys.exit(exception)

    else:  # If no error when loading textures
        global index
        TILE_VALUES_INFO = {}

        # Negative values
        # Ammo
        TILE_VALUES_INFO[-1] = ('Object', 'Ammo'), ammo_sprite

        # Health
        TILE_VALUES_INFO[-2] = ('Object', 'Health'), health_sprite

        # Other non-solid objects
        index = -3
        assign_texture_sheet(texture_size, texture_size, nonsolid_sprites, -1, ('Object', 'Non-solid'))

        TILE_VALUES_INFO[0] = 'Empty', None

        # Positive values
        # Solid objects
        index = 1
        assign_texture_sheet(texture_size, texture_size, solid_sprites, 1, ('Object', 'Solid'))

        # Doors
        assign_texture_sheet(texture_size * 2, texture_size, dynamic_door_textures, 1, ('Door', 'Dynamic'))
        assign_texture_sheet(texture_size * 2, texture_size, static_door_textures, 1, ('Door', 'Static'))

        # Other walls
        assign_texture_sheet(texture_size * 2, texture_size, wall_textures, 1, ('Wall', 'Normal'))

        # End trigger
        assign_texture_sheet(texture_size * 2, texture_size, end_trigger_textures, 1, ('Wall', 'End-trigger'))

        # Enemies
        ENEMY_INFO = {
            # spritesheet: hp
            # Allows for more attributes than just hp
            guard: (3),
            ss: (5)
        }
        for c, spritesheet in enumerate(ENEMY_INFO):  # For every enemy type in ENEMY_INFO, add value to TILE_VALUES_INFO
            TILE_VALUES_INFO[index + c] = ('Enemy', 'Basic'), spritesheet

        return TILE_VALUES_INFO, ENEMY_INFO, DOOR_SIDE_TEXTURE


if __name__ == '__main__':
    # Prints out TILE_VALUES_INFO if executed directly
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    TILE_VALUES_INFO = get(64)[0]
    for value in TILE_VALUES_INFO:
        print('{}: {}'.format(value, TILE_VALUES_INFO[value]))
