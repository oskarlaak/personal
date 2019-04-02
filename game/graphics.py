import pygame
import sys


def get_enemy_info():
    try:
        guard = pygame.image.load('../textures/enemies/guard.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/ss.png').convert_alpha()
        officer = pygame.image.load('../textures/enemies/officer.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            # spritesheet: (name, hp, speed, shooting_range, accuracy, memory, patience, pain_chance)
            #
            # Attributes description:
            # shooting_range = maximum distance in units where enemy can shoot player from
            # accuracy = 0 means distance doesn't matter to enemy at all, 1 means he's completely average shooter
            # memory = the time in ticks enemy knows player's position, after player has disappeared from enemy's vision
            # patience = the maximum time enemy stays standing still without an action
            # pain_chance = 1 means enemy will be displayed getting hit for every bullet, 0 means that will never happen
            guard:   (  'Guard', 100, 0.04, 10, 1.0,  90, 120, 0.90),
            ss:      (     'SS', 100, 0.05, 20, 0.6, 150, 120, 0.75),
            officer: ('Officer', 100, 0.06, 15, 0.7, 150,  90, 0.75)
        }
        return enemy_info


def get_door_side_texture():
    try:
        door_side_texture = pygame.image.load('../textures/doors/side.png').convert()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        return door_side_texture


def get_tile_values_info(texture_size, enemy_info):
    class Tile:
        def __init__(self, texture, type, description):
            self.texture = texture
            self.type = type
            self.desc = description

    def assign_texture_sheet(cell_w, cell_h, index_step, texture_sheet, type, description):
        global index  # Sets current index as staring index
        for row in range(int(texture_sheet.get_height() / cell_h)):
            for column in range(int(texture_sheet.get_width() / cell_w)):
                texture = texture_sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                tile_values_info[index] = Tile(texture, type, description)  # Update tile_values_info with Tile object
                index += index_step

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
        dynamic_door_textures = pygame.image.load('../textures/doors/dynamic.png').convert()
        static_door_textures = pygame.image.load('../textures/doors/static.png').convert()

        # Object sprites
        nonsolid_sprites = pygame.image.load('../textures/objects/nonsolids.png').convert_alpha()
        solid_sprites = pygame.image.load('../textures/objects/solids.png').convert_alpha()

        # Dynamic objects
        ammo_sprite = pygame.image.load('../textures/objects/dynamic/ammo.png').convert_alpha()
        health_sprite = pygame.image.load('../textures/objects/dynamic/health.png').convert_alpha()
        machinegun = pygame.image.load('../textures/objects/dynamic/machinegun.png').convert_alpha()
        chaingun = pygame.image.load('../textures/objects/dynamic/chaingun.png').convert_alpha()
        plasmagun = pygame.image.load('../textures/objects/dynamic/plasmagun.png').convert_alpha()
        rocketlauncher = pygame.image.load('../textures/objects/dynamic/rocketlauncher.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        # tile_values_info texture assigning can happen manually and via assign_texture_sheet()
        # Last on is used to assign whole texture sheets (usually same themed textures) at once with same description
        tile_values_info = {}

        # Creates a global index var bc it's needed in assign_texture_sheet()
        global index
        index = 0

        # ---Negative values---
        tile_values_info[index] = Tile(None, 'Empty', '')

        # Dynamic objects
        index -= 1
        tile_values_info[index] = Tile(ammo_sprite, 'Object-dynamic', 'Ammo')
        index -= 1
        tile_values_info[index] = Tile(health_sprite, 'Object-dynamic', 'Health')
        index -= 1
        tile_values_info[index] = Tile(machinegun, 'Object-dynamic', 'Machinegun')
        index -= 1
        tile_values_info[index] = Tile(chaingun, 'Object-dynamic', 'Chaingun')
        index -= 1
        tile_values_info[index] = Tile(plasmagun, 'Object-dynamic', 'Plasmagun')
        index -= 1
        tile_values_info[index] = Tile(rocketlauncher, 'Object-dynamic', 'Rocket launcher')

        # Other non-solid objects
        index -= 1
        assign_texture_sheet(texture_size, texture_size, -1, nonsolid_sprites, 'Object', 'Non-solid')

        # ---Positive values---
        # Solid objects
        index = 1
        assign_texture_sheet(texture_size, texture_size, 1, solid_sprites, 'Object', 'Solid')

        # Doors
        assign_texture_sheet(texture_size * 2, texture_size, 1, dynamic_door_textures, 'Door', 'Dynamic')
        assign_texture_sheet(texture_size * 2, texture_size, 1, static_door_textures, 'Door', 'Static')

        # Walls
        assign_texture_sheet(texture_size * 2, texture_size, 1, bloodycave_textures, 'Wall', 'Bloodycave')
        assign_texture_sheet(texture_size * 2, texture_size, 1, bluecellar_textures, 'Wall', 'Bluecellar')
        assign_texture_sheet(texture_size * 2, texture_size, 1, elevator_textures, 'Wall', 'Elevator')
        assign_texture_sheet(texture_size * 2, texture_size, 1, redbrick_textures, 'Wall', 'Redbrick')
        assign_texture_sheet(texture_size * 2, texture_size, 1, stone_textures, 'Wall', 'Stone')
        assign_texture_sheet(texture_size * 2, texture_size, 1, wood_textures, 'Wall', 'Wood')

        # Both end trigger texture variants
        assign_texture_sheet(texture_size * 2, texture_size, 1, end_trigger_textures, 'Wall', 'End-trigger')

        # For every enemy type in enemy_info, add value to tile_values_info
        for enemy_sheet in enemy_info:
            enemy_name = enemy_info[enemy_sheet][0]
            tile_values_info[index] = Tile(enemy_sheet, 'Enemy', enemy_name)
            index += 1

        return tile_values_info


if __name__ == '__main__':
    # Prints out tile_values_info if executed directly
    pygame.init()
    pygame.display.set_mode((1, 1))
    tile_values_info = get_tile_values_info(64, get_enemy_info())

    for value in sorted(tile_values_info):
        tile_obj = tile_values_info[value]
        print('{}: texture: {}, type: {}, description: {}'
              .format(value, tile_obj.texture, tile_obj.type, tile_obj.desc))
