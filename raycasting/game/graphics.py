def get_weapons(sys_module, pygame_module):
    class Weapon:
        def __init__(self, name, weapon_sheet, animation_frames, fire_delay, mag_size, reload_time,
                     automatic, ammo_unlimited, silenced):
            self.name = name
            self.weapon_sheet = weapon_sheet
            self.animation_frames = animation_frames  # Amount of shot animation frames in weapon_sheet

            self.fire_delay = fire_delay  # Has to be dividable by animation frames
            self.mag_size = mag_size  # Mag's total capacity
            self.mag_ammo = self.mag_size  # Currently ammo in weapon's mag
            self.reload_time = reload_time  # Reloading time in ticks, has to be even number

            self.automatic = automatic
            self.ammo_unlimited = ammo_unlimited
            self.silenced = silenced

    sys = sys_module
    pygame = pygame_module

    try:
        # Weapon cells are all 48x32
        ak47 = pygame.image.load('../textures/weapons/ak47.png')
        ak47 = pygame.transform.scale(ak47, (ak47.get_width() * 10, ak47.get_height() * 10)).convert_alpha()
        usps = pygame.image.load('../textures/weapons/usp-s.png')
        usps = pygame.transform.scale(usps, (usps.get_width() * 10, usps.get_height() * 10)).convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        weapons = [None]  # Makes it so first weapon is index 1 insted of 0
        weapons.append(Weapon('AK-47', ak47, 3, 3, 30, 72, True, False, False))
        weapons.append(Weapon('USP-S', usps, 2, 4, 12, 64, False, True, True))
        return weapons


def get_door_side_texture(sys_module, pygame_module):
    sys = sys_module
    pygame = pygame_module
    try:
        door_side_texture = pygame.image.load('../textures/doors/side.png').convert()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        return door_side_texture


def get_enemy_info(sys_module, pygame_module):
    sys = sys_module
    pygame = pygame_module
    try:
        # Enemy spritesheets
        # Using original Wolfenstein 3D enemy names
        guard = pygame.image.load('../textures/enemies/Guard.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/SS.png').convert_alpha()
        officer = pygame.image.load('../textures/enemies/Officer.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            # spritesheet: name, hp, speed, memory, patience
            #
            # Attributes description:
            # memory = the time (in ticks) enemy knows player position after he has disappeared from his vision
            #          (also the time in which enemy's path will be updated towards player)
            # patience = the maximum time enemy stays standing still without an action
            guard: ('Guard', 5, 0.04, 90, 120),
            ss: ('SS', 10, 0.06, 150, 120),
            officer: ('Officer', 8, 0.07, 150, 90)
        }
        return enemy_info


def get_tile_values_info(sys_module, pygame_module, texture_size, enemy_info):

    def assign_texture_sheet(cell_w, cell_h, index_step, description, texture_sheet):
        global index  # Sets current index as staring index
        for row in range(int(texture_sheet.get_height() / cell_h)):
            for column in range(int(texture_sheet.get_width() / cell_w)):
                texture = texture_sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                tile_values_info[index] = (description, texture)  # Update tile_values_info with texture
                index += index_step

    sys = sys_module
    pygame = pygame_module
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
        ammo_sprite = pygame.image.load('../textures/objects/ammo.png').convert_alpha()
        health_sprite = pygame.image.load('../textures/objects/health.png').convert_alpha()
        nonsolid_sprites = pygame.image.load('../textures/objects/nonsolids.png').convert_alpha()
        solid_sprites = pygame.image.load('../textures/objects/solids.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        # tile_values_info texture assigning can happen manually and via assign_texture_sheet()
        # Last on is used to assign whole texture sheets (usually same themed textures) at once with same decription
        tile_values_info = {}

        # Creates a global index var bc it's needed in assign_texture_sheet()
        global index
        index = 0

        # ---Negative values---
        tile_values_info[index] = 'Empty', None

        # Ammo
        index -= 1
        tile_values_info[index] = ('Object', 'Ammo'), ammo_sprite

        # Health
        index -= 1
        tile_values_info[index] = ('Object', 'Health'), health_sprite

        # Other non-solid objects
        index -= 1
        assign_texture_sheet(texture_size, texture_size, -1, ('Object', 'Non-solid'), nonsolid_sprites)

        # ---Positive values---
        # Solid objects
        index = 1
        assign_texture_sheet(texture_size, texture_size, 1, ('Object', 'Solid'), solid_sprites)

        # Doors
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Door', 'Dynamic'), dynamic_door_textures)
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Door', 'Static'), static_door_textures)

        # Walls
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'Bloodycave'), bloodycave_textures)
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'Bluecellar'), bluecellar_textures)
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'Elevator'), elevator_textures)
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'Redbrick'), redbrick_textures)
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'Stone'), stone_textures)
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'Wood'), wood_textures)

        # Both end trigger texture variants
        assign_texture_sheet(texture_size * 2, texture_size, 1, ('Wall', 'End-trigger'), end_trigger_textures)

        # For every enemy type in enemy_info, add value to tile_values_info
        for spritesheet in enemy_info:
            enemy_name = enemy_info[spritesheet][0]
            tile_values_info[index] = ('Enemy', enemy_name), spritesheet
            index += 1

        return tile_values_info


if __name__ == '__main__':
    # Prints out tile_values_info if executed directly
    import sys
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))

    enemy_info = get_enemy_info(sys, pygame)
    tile_values_info = get_tile_values_info(sys, pygame, 64, enemy_info)

    for value in sorted(tile_values_info):
        print('{}: {}'.format(value, tile_values_info[value]))