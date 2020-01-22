from game.settings import *
import pygame
import sys
import math


def get():
    class WeaponSounds:
        def __init__(self, fire, idle=None):
            self.fire = fire
            self.idle = idle

    class Weapon:
        cell_size = 192

        def __init__(self, name, sounds, weapon_sheet, shot_column, fire_delay, damage, automatic):
            self.name = name
            self.sounds = sounds
            self.animation_frames = int(weapon_sheet.get_width() / Weapon.cell_size) - 1
            self.weapon_sheet = weapon_sheet
            self.shot_column = shot_column
            self.fire_delay = fire_delay  # Has to match with number of animation frames
            self.damage = damage
            self.automatic = automatic

    class Melee(Weapon):
        type = 'Melee'

        def __init__(self, name, sounds, weapon_sheet, shot_column, fire_delay, damage, automatic, range):
            super().__init__(name, sounds, weapon_sheet, shot_column, fire_delay, damage, automatic)
            self.range = range

    class HitscanWeapon(Weapon):
        type = 'Hitscan'

        def __init__(self, name, sounds, weapon_sheet, shot_column, fire_delay, damage, automatic, spread):
            super().__init__(name, sounds, weapon_sheet, shot_column, fire_delay, damage, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)

    class Shotgun(Weapon):
        type = 'Shotgun'

        def __init__(self, name, sounds, weapon_sheet, shot_column, fire_delay,
                     damage, automatic, spread, shot_bullets):
            super().__init__(name, sounds, weapon_sheet, shot_column, fire_delay, damage, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)
            self.shot_bullets = shot_bullets

    try:
        # Weapon spritesheets
        pistol = pygame.image.load('../textures/weapons/pistol.png').convert_alpha()
        shotgun = pygame.image.load('../textures/weapons/shotgun.png').convert_alpha()
        chaingun = pygame.image.load('../textures/weapons/chaingun.png').convert_alpha()
        supershotgun = pygame.image.load('../textures/weapons/supershotgun.png').convert_alpha()
        chainsaw = pygame.image.load('../textures/weapons/chainsaw.png').convert_alpha()

        # Weapon sounds
        pistol_sound = pygame.mixer.Sound('../sounds/weapons/pistol.wav')
        shotgun_sound = pygame.mixer.Sound('../sounds/weapons/shotgun.wav')
        chaingun_sound = pygame.mixer.Sound('../sounds/weapons/chaingun.wav')
        supershotgun_sound = pygame.mixer.Sound('../sounds/weapons/supershotgun.wav')
        chainsaw_sound = pygame.mixer.Sound('../sounds/weapons/chainsaw.wav')
        chainsaw_idle = pygame.mixer.Sound('../sounds/weapons/chainsawidle.wav')

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        weapons = [None,  # Makes it so first weapon is index 1 instead of 0
        HitscanWeapon('Pistol', WeaponSounds(pistol_sound), pistol,
                      1,  9, 14, False, 0.00),
              Shotgun('Shotgun', WeaponSounds(shotgun_sound), shotgun,
                      1, 28, 10, False, 0.18,  7),
        HitscanWeapon('Chaingun', WeaponSounds(chaingun_sound), chaingun,
                      1,  4, 14,  True, 0.12),
              Shotgun('Super Shotgun', WeaponSounds(supershotgun_sound), supershotgun,
                      1, 50, 10, False, 0.25, 14),
                Melee('Chainsaw', WeaponSounds(chainsaw_sound, chainsaw_idle), chainsaw,
                      1,  4, 40,  True, 1.25)
        ]
        return weapons
