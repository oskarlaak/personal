def get_weapons(sys_module, pygame_module):
    class Weapon:
        def __init__(self, name, weapon_sheet, animation_frames, fire_delay, shot_column,
                     reload_time, mag_size, automatic, ammo_unlimited, projectile=False):
            self.name = name
            self.weapon_sheet = weapon_sheet
            self.animation_frames = animation_frames  # Amount of shot animation frames in weapon_sheet
            self.fire_delay = fire_delay  # Has to be dividable by animation frames
            self.shot_column = shot_column  # Weapon sheet column that shoots (1 would mean 1st shot animation frame)

            self.reload_time = reload_time  # Reloading time in ticks, has to be even number
            self.mag_size = mag_size  # Mag's total capacity
            self.mag_ammo = self.mag_size  # Currently ammo in weapon's mag
            if self.mag_size == 1:
                self.auto_reload = True  # Automatically reloads one shot weapons
            else:
                self.auto_reload = False
            self.automatic = automatic
            self.ammo_unlimited = ammo_unlimited

            self.melee = False
            self.projectile = projectile

    class Melee:
        def __init__(self, name, weapon_sheet, animation_frames, fire_delay, shot_column, hit_radius, damage):
            self.name = name
            self.weapon_sheet = weapon_sheet
            self.animation_frames = animation_frames
            self.fire_delay = fire_delay
            self.shot_column = shot_column

            self.hit_radius = hit_radius
            self.damage = damage

            self.mag_ammo = False
            self.auto_reload = False
            self.automatic = False

            self.melee = True
            self.projectile = False

    class Projectile:
        def __init__(self, sheet, columns, y_multiplier, speed, hit_radius, damage, exploding):
            self.sheet = sheet
            self.columns = columns
            self.y_multiplier = y_multiplier
            self.speed = speed
            self.hit_radius = hit_radius
            self.damage = damage
            self.exploding = exploding

    sys = sys_module
    pygame = pygame_module

    try:
        def scale(image, times):
            return pygame.transform.scale(image, (image.get_width() * times, image.get_height() * times))

        knife = scale(pygame.image.load('../textures/weapons/knife.png').convert_alpha(), 8)
        pistol = scale(pygame.image.load('../textures/weapons/pistol.png').convert_alpha(), 8)
        machinegun = scale(pygame.image.load('../textures/weapons/machinegun.png').convert_alpha(), 8)
        chaingun = scale(pygame.image.load('../textures/weapons/chaingun.png').convert_alpha(), 8)
        plasmagun = scale(pygame.image.load('../textures/weapons/plasmagun.png').convert_alpha(), 8)
        rocketlauncher = scale(pygame.image.load('../textures/weapons/rocketlauncher.png').convert_alpha(), 8)

        plasma = pygame.image.load('../textures/projectiles/plasma.png').convert_alpha()
        rocket = pygame.image.load('../textures/projectiles/rocket.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        plasma = Projectile(plasma, 4, 0.55, 0.25, 0.2, 2, False)
        rocket = Projectile(rocket, 3, 0.75, 0.3, 0.3, 10, True)

        weapons = [None]  # Makes it so first weapon is index 1 instead of 0
        weapons.append(Melee('Knife', knife, 3, 9, 2, 1.3, 3))
        weapons.append(Weapon('Pistol', pistol, 4, 8, 2, 50, 12, False, True))
        weapons.append(Weapon('Machinegun', machinegun, 4, 4, 2, 60, 25, True, False))
        weapons.append(Weapon('Chaingun', chaingun, 3, 3, 1, 120, 50, True, False))
        weapons.append(Weapon('Plasmagun', plasmagun, 2, 4, 2, 80, 20, True, False, plasma))
        weapons.append(Weapon('Rocket launcher', rocketlauncher, 5, 10, 1, 40, 1, False, False, rocket))
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
            # spritesheet: name, hp, speed, shooting_range, instant_alert_dist, memory, patience, hittable_amount
            #
            # Attributes description:
            # shooting_range = maximum distance in units where enemy can shoot player from
            # instant_alert_dist = distance in which enemy automatically starts chasing player even if he can't see him
            # memory = the time (in ticks) enemy knows player position after he has disappeared from his vision
            #          (also the time in which enemy's path will be updated towards player)
            # patience = the maximum time enemy stays standing still without an action
            # hittable_amount = "average amount enemy" in each enemy's spritesheets cells
            #                   (basically how much of average cell is non-transparent)
            guard:   (  'Guard',  3, 0.04, 10, 1.4,  90, 120, 1/3),
            ss:      (     'SS', 10, 0.05, 20, 1.4, 150, 120, 1/2),
            officer: ('Officer',  6, 0.06, 15, 1.4, 150,  90, 1/3)
        }
        return enemy_info


def get_tile_values_info(sys_module, pygame_module, texture_size, enemy_info):
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
        # Last on is used to assign whole texture sheets (usually same themed textures) at once with same description
        tile_values_info = {}

        # Creates a global index var bc it's needed in assign_texture_sheet()
        global index
        index = 0

        # ---Negative values---
        tile_values_info[index] = Tile(None, 'Empty', '')

        # Ammo
        index -= 1
        tile_values_info[index] = Tile(ammo_sprite, 'Object', 'Ammo')

        # Health
        index -= 1
        tile_values_info[index] = Tile(health_sprite, 'Object', 'Health')

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
    import sys
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))

    enemy_info = get_enemy_info(sys, pygame)
    tile_values_info = get_tile_values_info(sys, pygame, 64, enemy_info)

    for value in sorted(tile_values_info):
        tile_obj = tile_values_info[value]
        print('{}: texture: {}, type: {}, description: {}'
              .format(value, tile_obj.texture, tile_obj.type, tile_obj.desc))
