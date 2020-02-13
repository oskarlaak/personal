import pygame
import sys


def get():
    try:
        door_open_sound = pygame.mixer.Sound('../sounds/other/dooropen.wav')
        door_close_sound = pygame.mixer.Sound('../sounds/other/doorclose.wav')
        push_wall_sound = pygame.mixer.Sound('../sounds/other/pushwall.wav')
        item_pickup_sound = pygame.mixer.Sound('../sounds/other/itempickup.wav')
        weapon_pickup_sound = pygame.mixer.Sound('../sounds/other/weaponpickup.wav')
        switch_sound = pygame.mixer.Sound('../sounds/other/switch.wav')

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        return door_open_sound, door_close_sound, push_wall_sound, item_pickup_sound, weapon_pickup_sound, switch_sound
