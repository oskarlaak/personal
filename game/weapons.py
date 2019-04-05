from game.settings import *
import pygame
import sys
import math


def get():
    def scale(image, times):
        return pygame.transform.scale(image, (image.get_width() * times, image.get_height() * times))

    class Weapon:
        cell_size = 192

        def __init__(self, name, weapon_sheet, shot_column, damage_range, fire_delay, automatic):
            self.name = name
            self.animation_frames = int(weapon_sheet.get_width() / Weapon.cell_size) - 1
            self.weapon_sheet = scale(weapon_sheet, 3)
            self.shot_column = shot_column
            self.damage_range = damage_range
            self.fire_delay = fire_delay  # Has to match with number of animation frames
            self.automatic = automatic

    class Melee(Weapon):
        def __init__(self, weapon_attributes, range):
            super().__init__(*weapon_attributes)
            self.range = range
            self.type = 'melee'

    class HitscanWeapon(Weapon):
        def __init__(self, weapon_attributes, max_spread):
            # Max spread = amount of radians bullets can spread
            super().__init__(*weapon_attributes)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_spread = int(math.tan(max_spread) * camera_plane_dist * D_W)
            self.type = 'hitscan'

    class Shotgun(Weapon):
        def __init__(self, weapon_attributes, max_spread, shot_bullets):
            # Max spread = amount of radians bullets can spread
            # Shot bullets = bullets sent out per shot
            super().__init__(*weapon_attributes)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_spread = int(math.tan(max_spread) * camera_plane_dist * D_W)
            self.shot_bullets = shot_bullets
            self.type = 'shotgun'

    class ProjectileWeapon(Weapon):
        def __init__(self, weapon_attributes, projectile):
            super().__init__(*weapon_attributes)
            self.projectile = projectile
            self.type = 'projectile'

    class Projectile:
        def __init__(self, sheet, y_multiplier, speed, hit_range, damage):
            self.sheet = sheet
            self.columns = int(sheet.get_width() / 64)
            self.y_multiplier = y_multiplier
            self.speed = speed
            self.hit_range = hit_range
            self.damage = damage
            self.explosive = False

    class ExplosiveProjectile(Projectile):
        def __init__(self, projectile_attributes, explosion_range, explosion_max_damage):
            super().__init__(*projectile_attributes)
            self.explosive = True
            self.explosion_range = explosion_range
            self.explosion_max_damage = explosion_max_damage

    try:
        fists = pygame.image.load('../textures/weapons/doom_fists.png').convert_alpha()
        chainsaw = pygame.image.load('../textures/weapons/doom_chainsaw.png').convert_alpha()
        pistol = pygame.image.load('../textures/weapons/doom_pistol.png').convert_alpha()
        shotgun = pygame.image.load('../textures/weapons/doom_shotgun.png').convert_alpha()
        super_shotgun= pygame.image.load('../textures/weapons/doom_super_shotgun.png').convert_alpha()
        chaingun = pygame.image.load('../textures/weapons/doom_chaingun.png').convert_alpha()

        rocket_launcher = pygame.image.load('../textures/weapons/doom_rocket_launcher.png').convert_alpha()
        plasma_gun = pygame.image.load('../textures/weapons/doom_plasma_gun.png').convert_alpha()
        bfg = pygame.image.load('../textures/weapons/doom_bfg.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        weapons = [None]  # Makes it so first weapon is index 1 instead of 0
        weapons.append(Melee(('Fists', fists, 3, range(2, 20), 15, False), 1.3))
        weapons.append(Melee(('Chainsaw', chainsaw, 1, range(2, 20), 4, True), 1.3))
        weapons.append(HitscanWeapon(('Pistol', pistol, 1, range(5, 15), 12, False), 0.10))
        weapons.append(Shotgun(('Shotgun', shotgun, 1, range(5, 15), 28, False), 0.17, 7))
        weapons.append(Shotgun(('Super Shotgun', super_shotgun, 1, range(5, 15), 63, False), 0.20, 20))
        weapons.append(HitscanWeapon(('Chaingun', chaingun, 1, range(5, 15), 4, True), 0.10))
        return weapons
