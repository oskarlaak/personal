from game.settings import *
import pygame
import sys
import math


def get():
    def scale(image, times):
        return pygame.transform.scale(image, (image.get_width() * times, image.get_height() * times))

    class Weapon:
        cell_size = 192

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic):
            self.name = name
            self.animation_frames = int(weapon_sheet.get_width() / Weapon.cell_size) - 1
            self.weapon_sheet = scale(weapon_sheet, 3)
            self.shot_column = shot_column
            self.fire_delay = fire_delay  # Has to match with number of animation frames
            self.damage_range = damage_range
            self.automatic = automatic

    class Melee(Weapon):
        type = 'melee'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic, range):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage_range, automatic)
            self.range = range


    class HitscanWeapon(Weapon):
        type = 'hitscan'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic, spread):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage_range, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_spread = int(math.tan(spread) * camera_plane_dist * D_W)

    class Shotgun(Weapon):
        type = 'shotgun'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic, spread, shot_bullets):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage_range, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_spread = int(math.tan(spread) * camera_plane_dist * D_W)
            self.shot_bullets = shot_bullets

    try:
        fists = pygame.image.load('../textures/weapons/fists.png').convert_alpha()
        chainsaw = pygame.image.load('../textures/weapons/chainsaw.png').convert_alpha()
        pistol = pygame.image.load('../textures/weapons/pistol.png').convert_alpha()
        shotgun = pygame.image.load('../textures/weapons/shotgun.png').convert_alpha()
        super_shotgun= pygame.image.load('../textures/weapons/super_shotgun.png').convert_alpha()
        chaingun = pygame.image.load('../textures/weapons/chaingun.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        weapons = [None]  # Makes it so first weapon is index 1 instead of 0
        weapons.append(        Melee(        'Fists',         fists, 3, 15, range(2, 21), False, 1.25))
        weapons.append(        Melee(     'Chainsaw',      chainsaw, 1,  4, range(2, 21),  True, 1.25))
        weapons.append(HitscanWeapon(       'Pistol',        pistol, 1, 12, range(5, 16), False, 0.096))
        weapons.append(      Shotgun(      'Shotgun',       shotgun, 1, 32, range(5, 16), False, 0.171,  7))
        weapons.append(      Shotgun('Super Shotgun', super_shotgun, 1, 54, range(5, 16), False, 0.342, 20))
        weapons.append(HitscanWeapon(     'Chaingun',      chaingun, 1,  4, range(5, 16),  True, 0.096))
        return weapons
