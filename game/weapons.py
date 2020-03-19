from game.settings import *
import pygame
import sys
import math


def get():
    class WeaponSounds:
        def __init__(self, fire, hit=None):
            self.fire = fire
            self.hit = hit
            self.no_ammo = no_ammo_sound

    class Weapon:
        cell_size = 192

        def __init__(self, name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic):
            self.name = name
            self.weapon_sheet = weapon_sheet
            self.animation_frames = int(weapon_sheet.get_width() / Weapon.cell_size) - 1
            self.sounds = sounds
            self.ammo_consumption = ammo_consumption
            self.shot_column = shot_column
            self.fire_delay = fire_delay  # Has to match with number of animation frames
            self.damage = damage
            self.automatic = automatic

    class Melee(Weapon):
        type = 'Melee'

        def __init__(self, name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic,
                     range):
            super().__init__(name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic)
            self.range_squared = range**2

    class HitscanWeapon(Weapon):
        type = 'Hitscan'

        def __init__(self, name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic,
                     spread):
            super().__init__(name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)

    class Shotgun(Weapon):
        type = 'Shotgun'

        def __init__(self, name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic,
                     spread, shot_bullets):
            super().__init__(name, weapon_sheet, sounds, ammo_consumption, shot_column, fire_delay, damage, automatic)
            camera_plane_dist = 0.5 / math.tan(FOV / 2)
            self.max_x_spread = int(math.tan(spread) * camera_plane_dist * D_W)
            self.shot_bullets = shot_bullets

    try:
        # Weapon spritesheets
        pistol = pygame.image.load('../textures/weapons/pistol.png').convert_alpha()
        shotgun = pygame.image.load('../textures/weapons/shotgun.png').convert_alpha()
        chaingun = pygame.image.load('../textures/weapons/chaingun.png').convert_alpha()
        supershotgun = pygame.image.load('../textures/weapons/supershotgun.png').convert_alpha()
        fist = pygame.image.load('../textures/weapons/fist.png').convert_alpha()

        # Weapon sounds
        no_ammo_sound = pygame.mixer.Sound('../sounds/weapons/emptygunshot.wav')
        pistol_sound = pygame.mixer.Sound('../sounds/weapons/pistol.wav')
        shotgun_sound = pygame.mixer.Sound('../sounds/weapons/shotgun.wav')
        chaingun_sound = pygame.mixer.Sound('../sounds/weapons/chaingun.wav')
        supershotgun_sound = pygame.mixer.Sound('../sounds/weapons/supershotgun.wav')
        fist_sound = pygame.mixer.Sound('../sounds/weapons/fist.wav')
        fist_hit_sound = pygame.mixer.Sound('../sounds/weapons/fisthit.wav')

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        weapons = [
            None,
            HitscanWeapon(
                name='Pistol',
                weapon_sheet=pistol,
                sounds=WeaponSounds(
                    fire=pistol_sound),
                ammo_consumption=1,
                shot_column=1,
                fire_delay=8,
                damage=14,
                automatic=False,
                spread=0.00),
            Shotgun(
                name='Shotgun',
                weapon_sheet=shotgun,
                sounds=WeaponSounds(
                    fire=shotgun_sound),
                ammo_consumption=3,
                shot_column=1,
                fire_delay=21,
                damage=10,
                automatic=False,
                spread=0.18,
                shot_bullets=5),
            HitscanWeapon(
                name='Chaingun',
                weapon_sheet=chaingun,
                sounds=WeaponSounds(
                    fire=chaingun_sound),
                ammo_consumption=1,
                shot_column=1,
                fire_delay=4,
                damage=14,
                automatic=True,
                spread=0.12),
            Shotgun(
                name='Super Shotgun',
                weapon_sheet=supershotgun,
                sounds=WeaponSounds(
                    fire=supershotgun_sound),
                ammo_consumption=5,
                shot_column=1,
                fire_delay=40,
                damage=10,
                automatic=False,
                spread=0.25,
                shot_bullets=10),
            Melee(
                name='Fist',
                weapon_sheet=fist,
                sounds=WeaponSounds(
                    fire=fist_sound,
                    hit=fist_hit_sound),
                ammo_consumption=0,
                shot_column=2,
                fire_delay=6,
                damage=40,
                automatic=False,
                range=1.25)
        ]
        return weapons
