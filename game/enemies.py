import pygame
import sys


def get_enemy_info():
    class EnemySounds:
        def __init__(self, appearance, attack, death, step=None):
            self.appearance = appearance
            self.attack = attack
            self.death = death
            self.step = step

    class Enemy:
        type = 'Normal'

        def __init__(self, channel_id, sounds, hp, speed, wandering_radius, shooting_range, damage_multiplier, accuracy,
                     pain_chance, patience, death_frames, shooting_frames, shot_columns):
            self.channel_id = channel_id
            self.sounds = sounds
            self.hp = hp
            self.speed = speed
            self.wandering_radius = wandering_radius
            self.shooting_range = shooting_range  # Max shooting range

            self.damage_multiplier = damage_multiplier
            self.accuracy = accuracy  # 0 will never hit, 1 is normal, can go higher
            self.pain_chance = pain_chance  # From 0 to 1, determines how likely enemy will be shown hurt when shot

            self.patience = patience  # Max time in ticks enemy will remain without action

            self.running_rows = (1, 2, 3, 4)

            self.death_frames = death_frames
            self.hit_row = 5

            self.shooting_frames = shooting_frames
            self.shot_columns = shot_columns
            self.shooting_row = 6

    class Boss:
        type = 'Boss'

        def __init__(self, name, channel_id, sounds, hp, speed, damage_multiplier, accuracy, running_frames,
                     death_frames, shooting_frames, shot_columns):
            self.name = name
            self.channel_id = channel_id
            self.sounds = sounds
            self.hp = hp
            self.speed = speed
            self.shooting_range = 32

            self.damage_multiplier = damage_multiplier
            self.accuracy = accuracy
            self.pain_chance = 0

            self.running_frames = running_frames

            self.death_frames = death_frames
            self.hit_row = 2

            self.shooting_frames = shooting_frames
            self.shot_columns = shot_columns
            self.shooting_row = 1

    try:
        # Bosses
        ottogiftmacher = pygame.image.load('../textures/enemies/ottogiftmacher.png').convert_alpha()
        hansgrosse = pygame.image.load('../textures/enemies/hansgrosse.png').convert_alpha()
        hitler = pygame.image.load('../textures/enemies/hitler.png').convert_alpha()

        # Normal enemies
        guard = pygame.image.load('../textures/enemies/guard.png').convert_alpha()
        dog = pygame.image.load('../textures/enemies/guarddog.png').convert_alpha()
        officer = pygame.image.load('../textures/enemies/officer.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/ss.png').convert_alpha()
        mutant = pygame.image.load('../textures/enemies/mutant.png').convert_alpha()

        # Boss sounds
        halten_sie = pygame.mixer.Sound('../sounds/enemies/haltensie.wav')
        heavy_pistol = pygame.mixer.Sound('../sounds/enemies/heavypistol.wav')
        scheisse_koph = pygame.mixer.Sound('../sounds/enemies/scheissekoph.wav')
        boss_step = pygame.mixer.Sound('../sounds/enemies/bossstep.wav')

        guten_tag = pygame.mixer.Sound('../sounds/enemies/gutentag.wav')
        chaingun = pygame.mixer.Sound('../sounds/enemies/chaingun.wav')
        death_1 = pygame.mixer.Sound('../sounds/enemies/death1.wav')

        scheisse = pygame.mixer.Sound('../sounds/enemies/scheisse.wav')
        death_5 = pygame.mixer.Sound('../sounds/enemies/death5.wav')

        # Normal enemy sounds
        achtung = pygame.mixer.Sound('../sounds/enemies/achtung.wav')
        pistol = pygame.mixer.Sound('../sounds/enemies/pistol.wav')
        death_2 = pygame.mixer.Sound('../sounds/enemies/death2.wav')

        dog_attack = pygame.mixer.Sound('../sounds/enemies/dogattack.wav')
        dog_death = pygame.mixer.Sound('../sounds/enemies/dogdeath.wav')

        halt_1 = pygame.mixer.Sound('../sounds/enemies/halt1.wav')
        death_3 = pygame.mixer.Sound('../sounds/enemies/death3.wav')

        halt_2 = pygame.mixer.Sound('../sounds/enemies/halt2.wav')
        heavy_machine_gun = pygame.mixer.Sound('../sounds/enemies/heavymachinegun.wav')
        death_4 = pygame.mixer.Sound('../sounds/enemies/death4.wav')

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            ottogiftmacher: Boss('Otto Giftmacher', 7, EnemySounds(halten_sie, heavy_pistol, scheisse_koph, boss_step),
                                  666, 0.10, 3.00, 5.00, 4, 4, 8, [4]),
            hansgrosse:     Boss('Hans Grosse', 7, EnemySounds(guten_tag, chaingun, death_1, boss_step),
                                  777, 0.10, 1.20, 1.00, 4, 4, 8, [2, 3, 4, 5, 6, 7]),
            hitler:         Boss('Hitler', 7, EnemySounds(scheisse, chaingun, death_5, boss_step),
                                 1000, 0.07, 1.50, 1.00, 4, 8, 8, [3, 4, 5, 6, 7]),
            guard:   Enemy(2, EnemySounds(achtung, pistol, death_2),
                           20, 0.07, 2,   5, 1.00, 1.00, 1.00,  60, 5, 6, [4]),
            dog:     Enemy(3, EnemySounds(dog_attack, dog_attack, dog_death),
                            5, 0.10, 4, 1.2, 0.50, 5.00, 0.00,   0, 5, 6, [1, 2, 3, 4, 5]),
            officer: Enemy(4, EnemySounds(halt_1, pistol, death_3),
                           40, 0.08, 2,   8, 0.90, 1.10, 0.75,  90, 5, 6, [2, 4]),
            ss:      Enemy(5, EnemySounds(halt_2, heavy_machine_gun, death_4),
                           50, 0.06, 3,   8, 1.00, 1.05, 0.50, 180, 5, 6, [3, 4, 5]),
            mutant:  Enemy(6, EnemySounds(None, pistol, death_2),
                           30, 0.07, 5,   6, 0.60, 1.00, 0.75,  60, 5, 6, [1, 3])
        }
        return enemy_info
