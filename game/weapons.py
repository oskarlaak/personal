from game.settings import *
import pygame
import sys
import math


def get():
    def scale(image, times):
        return pygame.transform.scale(image, (image.get_width() * times, image.get_height() * times))

    class Weapon:
        cell_size = 192

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage, automatic):
            self.name = name
            self.animation_frames = int(weapon_sheet.get_width() / Weapon.cell_size) - 1
            self.weapon_sheet = scale(weapon_sheet, 3)
            self.shot_column = shot_column
            self.fire_delay = fire_delay  # Has to match with number of animation frames
            self.damage = damage
            self.automatic = automatic

    class Melee(Weapon):
        type = 'Melee'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage, automatic, range):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage, automatic)
            self.range = range


    class HitscanWeapon(Weapon):
        type = 'Hitscan'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage, automatic, spread):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)

    class Shotgun(Weapon):
        type = 'Shotgun'

        def __init__(self, name, weapon_sheet, shot_column, fire_delay, damage, automatic, spread, shot_bullets):
            super().__init__(name, weapon_sheet, shot_column, fire_delay, damage, automatic)
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
        HitscanWeapon(       'Pistol',       pistol, 1,  9, 14, False, 0.096),
              Shotgun(      'Shotgun',      shotgun, 1, 32,  7, False, 0.262,  7),
        HitscanWeapon(     'Chaingun',     chaingun, 1,  6, 10,  True, 0.096),
              Shotgun('Super Shotgun', supershotgun, 1, 50, 10, False, 0.524, 20),
                Melee(     'Chainsaw',     chainsaw, 1,  4, 40,  True, 1.25)
        ]
        return weapons
