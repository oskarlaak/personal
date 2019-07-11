import pygame
import sys


def get():
    try:
        door_open_sound = pygame.mixer.Sound('../sounds/other/dooropen.wav')
        door_close_sound = pygame.mixer.Sound('../sounds/other/doorclose.wav')
        item_pickup_sound = pygame.mixer.Sound('../sounds/other/itempickup.wav')
        weapon_pickup_sound = pygame.mixer.Sound('../sounds/other/weaponpickup.wav')

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        return door_open_sound, door_close_sound, item_pickup_sound, weapon_pickup_sound
