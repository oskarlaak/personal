def get(texture_size):
    import sys
    import pygame

    def assign_texture_sheet(cell_w, cell_h, sheet, step, type):
        global index
        for row in range(int(sheet.get_height() / cell_h)):

            for column in range(int(sheet.get_width() / cell_w)):

                texture = sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                tile_values_info[index] = (type, texture)
                index += step

    try:
        # Wall textures
        bloodycave_textures = pygame.image.load('../textures/walls/bloodycave.png').convert()
        bluecellar_textures = pygame.image.load('../textures/walls/bluecellar.png').convert()
        elevator_textures = pygame.image.load('../textures/walls/elevator.png').convert()
        redbrick_textures = pygame.image.load('../textures/walls/redbrick.png').convert()
        stone_textures = pygame.image.load('../textures/walls/stone.png').convert()
        wood_textures = pygame.image.load('../textures/walls/wood.png').convert()
        end_trigger_textures = pygame.image.load('../textures/walls/endtrigger.png').convert()

        # Door textures
        door_side_texture = pygame.image.load('../textures/doors/side.png').convert()
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
        tile_values_info = {}

        # Negative values
        # Ammo
        tile_values_info[-1] = ('Object', 'Ammo'), ammo_sprite

        # Health
        tile_values_info[-2] = ('Object', 'Health'), health_sprite

        # Other non-solid objects
        index = -3
        assign_texture_sheet(texture_size, texture_size, nonsolid_sprites, -1, ('Object', 'Non-solid'))

        tile_values_info[0] = 'Empty', None

        # Positive values
        # Solid objects
        index = 1
        assign_texture_sheet(texture_size, texture_size, solid_sprites, 1, ('Object', 'Solid'))

        # Doors
        assign_texture_sheet(texture_size * 2, texture_size, dynamic_door_textures, 1, ('Door', 'Dynamic'))
        assign_texture_sheet(texture_size * 2, texture_size, static_door_textures, 1, ('Door', 'Static'))

        # Walls
        assign_texture_sheet(texture_size * 2, texture_size, bloodycave_textures, 1, ('Wall', 'Bloodycave'))
        assign_texture_sheet(texture_size * 2, texture_size, bluecellar_textures, 1, ('Wall', 'Bluecellar'))
        assign_texture_sheet(texture_size * 2, texture_size, elevator_textures, 1, ('Wall', 'Elevator'))
        assign_texture_sheet(texture_size * 2, texture_size, redbrick_textures, 1, ('Wall', 'Redbrick'))
        assign_texture_sheet(texture_size * 2, texture_size, stone_textures, 1, ('Wall', 'Stone'))
        assign_texture_sheet(texture_size * 2, texture_size, wood_textures, 1, ('Wall', 'Wood'))

        # End trigger
        assign_texture_sheet(texture_size * 2, texture_size, end_trigger_textures, 1, ('Wall', 'End-trigger'))

        # Enemies
        enemy_info = {
            # spritesheet: hp, speed, memory, patience
            # Attributes description:
            # memory = the time (in ticks) enemy knows player position after he has disappeared from his vision
            #          (also the time in which enemy's path will be updated towards player)
            # patience = the maximum time enemy stays standing still without an action
            guard: (5, 0.04, 90, 90),
            ss: (10, 0.06, 90, 90)
        }
        for c, spritesheet in enumerate(enemy_info):  # For every enemy type in ENEMY_INFO, add value to TILE_VALUES_INFO
            tile_values_info[index + c] = ('Enemy', 'Basic'), spritesheet

        return tile_values_info, enemy_info, door_side_texture


if __name__ == '__main__':
    # Prints out TILE_VALUES_INFO if executed directly
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    TILE_VALUES_INFO = get(64)[0]
    for value in TILE_VALUES_INFO:
        print('{}: {}'.format(value, TILE_VALUES_INFO[value]))
