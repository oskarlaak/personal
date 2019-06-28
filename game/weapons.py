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
        type = 'Melee'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic, range):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage_range, automatic)
            self.range = range


    class HitscanWeapon(Weapon):
        type = 'Hitscan'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic, spread):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage_range, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)

    class Shotgun(Weapon):
        type = 'Shotgun'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage_range, automatic, spread, shot_bullets):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage_range, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)
            self.shot_bullets = shot_bullets

    try:
        chainsaw = pygame.image.load('../textures/weapons/chainsaw.png').convert_alpha()
        pistol = pygame.image.load('../textures/weapons/pistol.png').convert_alpha()
        shotgun = pygame.image.load('../textures/weapons/shotgun.png').convert_alpha()
        supershotgun = pygame.image.load('../textures/weapons/supershotgun.png').convert_alpha()
        chaingun = pygame.image.load('../textures/weapons/chaingun.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        weapons = [None,  # Makes it so first weapon is index 1 instead of 0
        HitscanWeapon(       'Pistol',       pistol, 1,  9, range(10, 16), False, 0.096),
              Shotgun(      'Shotgun',      shotgun, 1, 32, range( 5, 11), False, 0.171,  7),
        HitscanWeapon(     'Chaingun',     chaingun, 1,  4, range(10, 16),  True, 0.096),
              Shotgun('Super Shotgun', supershotgun, 1, 50, range( 5, 11), False, 0.342, 20),
                Melee(     'Chainsaw',     chainsaw, 1,  4, range( 2, 21),  True, 1.25)
        ]
        return weapons
