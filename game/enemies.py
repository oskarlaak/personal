import pygame
import sys


def get_enemy_info():
    class Enemy:
        type = 'Normal'

        def __init__(self, hp, speed, shooting_range, accuracy, damage_multiplier, memory, patience, pain_chance):
            self.hp = hp
            self.speed = speed
            self.shooting_range = shooting_range  # Max shooting range
            self.accuracy = accuracy  # 0 will never hit, 1 is normal, can go higher
            self.damage_multiplier = damage_multiplier
            self.memory = memory  # Time in ticks enemy knows player's pos after player has disappeared from enemy's POV
            self.patience = patience  # Max time in ticks enemy will remain without action
            self.pain_chance = pain_chance  # From 0 to 1, how likely player will be shown hurt when shot

    class Boss:
        type = 'Boss'

        def __init__(self, hp, speed, accuracy, damage_multiplier, shot_columns):
            self.hp = hp
            self.speed = speed
            self.accuracy = accuracy
            self.damage_multiplier = damage_multiplier
            self.shot_columns = shot_columns

    try:
        # Bosses
        generalfettgesicht = pygame.image.load('../textures/enemies/generalfettgesicht.png').convert_alpha()
        gretelgrosse = pygame.image.load('../textures/enemies/gretelgrosse.png').convert_alpha()
        hansgrosse = pygame.image.load('../textures/enemies/hansgrosse.png').convert_alpha()
        hitler = pygame.image.load('../textures/enemies/hitler.png').convert_alpha()
        ottogiftmacher = pygame.image.load('../textures/enemies/ottogiftmacher.png').convert_alpha()
        # Normal enemies
        guard = pygame.image.load('../textures/enemies/guard.png').convert_alpha()
        guarddog = pygame.image.load('../textures/enemies/guarddog.png').convert_alpha()
        mutant = pygame.image.load('../textures/enemies/mutant.png').convert_alpha()
        officer = pygame.image.load('../textures/enemies/officer.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/ss.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            generalfettgesicht: Boss( 525, 0.04, 0.90, 1.25, (1, 2, 3)),
            gretelgrosse:       Boss( 525, 0.05, 1.00, 1.00, (1, 2, 3)),
            hansgrosse:         Boss( 525, 0.05, 1.33, 1.00, (1, 2, 3)),
            hitler:             Boss(1050, 0.04, 1.00, 1.50, (1, 2, 3)),
            ottogiftmacher:     Boss( 525, 0.04, 0.50, 2.00,    (1, 3)),
            guard:    Enemy(20, 0.04, 10, 1.00, 1.00,  90,  90, 1.00),
            guarddog: Enemy( 1, 0.06,  1, 9.99, 0.75,  90,   0, 0.00),
            mutant:   Enemy(30, 0.04, 15, 1.00, 1.50,  90, 180, 0.75),
            officer:  Enemy(40, 0.06, 15, 1.00, 1.25, 150,  90, 0.75),
            ss:       Enemy(50, 0.05, 20, 1.33, 1.50, 150, 180, 0.50)
        }
        return enemy_info