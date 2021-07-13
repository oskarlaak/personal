import pygame
import sys


def get_enemy_info():
    class EnemySounds:
        def __init__(self, attack, death, appearance=None, step=None):
            self.appearance = appearance
            self.attack = attack
            self.death = death
            self.step = step

    class Enemy:
        type = 'Normal'

        def __init__(self, channel_id, sounds, hp, speed, wandering_radius, shooting_range, looting_ammo, damage_multiplier, accuracy, pain_chance, memory,
                     death_frames, shooting_rows, shot_rows, shooting_pattern):
            # Behaviour description
            self.channel_id = channel_id
            self.sounds = sounds
            self.hp = hp
            self.speed = speed
            self.wandering_radius = wandering_radius
            self.shooting_range_squared = shooting_range**2  # Max shooting range squared
            self.looting_ammo = looting_ammo  # Amount of ammo dropped when killed
            self.damage_multiplier = damage_multiplier
            self.accuracy = accuracy  # 0 will never hit, 1 is normal, can go higher
            self.pain_chance = pain_chance  # From 0 to 1, determines how likely enemy will be shown hurt when shot
            self.memory = memory

            # Spritesheet description
            self.running_rows = (0, 1, 2, 3)  # Rows that contain running frames
            self.hit_row = 4  # Row that contains getting hit frames
            self.death_row = 5  # Row that contains death frames
            self.death_frames = death_frames  # Amount of death frames in death row
            self.shooting_rows = shooting_rows  # Rows that contain shooting frames
            self.shot_rows = shot_rows  # Rows that contain actual attacking/weapon firing
            self.shooting_pattern = shooting_pattern  # The order of which the shooting rows will be displayed
            self.shooting_frames = len(shooting_pattern)  # Amount of shooting frames in a shooting pattern

    class Boss:
        type = 'Boss'

        def __init__(self, name, channel_id, sounds, hp, speed, damage_multiplier, accuracy, running_frames,
                     death_frames, shooting_frames, shot_columns):
            self.name = name
            self.channel_id = channel_id
            self.sounds = sounds
            self.hp = hp
            self.speed = speed
            self.shooting_range_squared = 32**2

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
        # Spritesheets
        # Bosses
        ottogiftmacher = pygame.image.load('../textures/spritesheets/enemies/ottogiftmacher.png').convert_alpha()
        hansgrosse = pygame.image.load('../textures/spritesheets/enemies/hansgrosse.png').convert_alpha()
        hitler = pygame.image.load('../textures/spritesheets/enemies/hitler.png').convert_alpha()

        # Normal enemies
        guard = pygame.image.load('../textures/spritesheets/enemies/guard.png').convert_alpha()
        officer = pygame.image.load('../textures/spritesheets/enemies/officer.png').convert_alpha()
        ss = pygame.image.load('../textures/spritesheets/enemies/ss.png').convert_alpha()
        mutant = pygame.image.load('../textures/spritesheets/enemies/mutant.png').convert_alpha()
        dog = pygame.image.load('../textures/spritesheets/enemies/dog.png').convert_alpha()
        formerhuman = pygame.image.load('../textures/spritesheets/enemies/formerhuman.png').convert_alpha()

        # Sounds
        # Attack
        pistol = pygame.mixer.Sound('../sounds/enemies/pistol.wav')
        revolver = pygame.mixer.Sound('../sounds/enemies/revolver.wav')
        machinegun = pygame.mixer.Sound('../sounds/enemies/machinegun.wav')
        chaingun = pygame.mixer.Sound('../sounds/enemies/chaingun.wav')
        dog_woof = pygame.mixer.Sound('../sounds/enemies/dogwoof.wav')
        # Death
        scream_1 = pygame.mixer.Sound('../sounds/enemies/scream1.wav')
        scream_2 = pygame.mixer.Sound('../sounds/enemies/scream2.wav')
        scream_3 = pygame.mixer.Sound('../sounds/enemies/scream3.wav')
        scream_4 = pygame.mixer.Sound('../sounds/enemies/scream4.wav')
        gib = pygame.mixer.Sound('../sounds/enemies/gib.wav')
        scheisse_koph = pygame.mixer.Sound('../sounds/enemies/scheissekoph.wav')
        dog_pain = pygame.mixer.Sound('../sounds/enemies/dogpain.wav')
        # Appearance
        halt_1 = pygame.mixer.Sound('../sounds/enemies/halt1.wav')
        halt_2 = pygame.mixer.Sound('../sounds/enemies/halt2.wav')
        halten_sie = pygame.mixer.Sound('../sounds/enemies/haltensie.wav')
        achtung = pygame.mixer.Sound('../sounds/enemies/achtung.wav')
        scheisse = pygame.mixer.Sound('../sounds/enemies/scheisse.wav')
        guten_tag = pygame.mixer.Sound('../sounds/enemies/gutentag.wav')
        dog_woof_long = pygame.mixer.Sound('../sounds/enemies/dogwooflong.wav')
        # Step
        boss_step = pygame.mixer.Sound('../sounds/enemies/bossstep.wav')

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            # Bosses
            ottogiftmacher: Boss(
                name='Otto Giftmacher',
                channel_id=7,
                sounds=EnemySounds(
                    attack=revolver,
                    death=scheisse_koph,
                    appearance=halten_sie,
                    step=boss_step),
                hp=666,
                speed=0.10,
                damage_multiplier=3.00,
                accuracy=5.00,
                running_frames=4,
                death_frames=4,
                shooting_frames=8,
                shot_columns=[4]),
            hansgrosse: Boss(
                name='Hans Grosse',
                channel_id=7,
                sounds=EnemySounds(
                    attack=chaingun,
                    death=scream_1,
                    appearance=guten_tag,
                    step=boss_step),
                hp=777,
                speed=0.10,
                damage_multiplier=1.20,
                accuracy=1.00,
                running_frames=4,
                death_frames=4,
                shooting_frames=8,
                shot_columns=[2, 3, 4, 5, 6, 7]),
            hitler: Boss(
                name='Hitler',
                channel_id=7,
                sounds=EnemySounds(
                    attack=chaingun,
                    death=gib,
                    appearance=scheisse,
                    step=boss_step),
                hp=1000,
                speed=0.07,
                damage_multiplier=1.50,
                accuracy=1.00,
                running_frames=4,
                death_frames=8,
                shooting_frames=8,
                shot_columns=[3, 4, 5, 6, 7]),
            # Normal enemies
            guard: Enemy(
                channel_id=4,
                sounds=EnemySounds(
                    attack=machinegun,
                    death=scream_4,
                    appearance=halt_2
                ),
                hp=50,
                speed=0.06,
                wandering_radius=3,
                shooting_range=8,
                looting_ammo=8,
                damage_multiplier=0.00,
                accuracy=1.05,
                pain_chance=0.50,
                memory=90,
                death_frames=5,
                shooting_rows=(6, 7),
                shot_rows=7,
                shooting_pattern=(0, 0, 1, 0, 1)
            ),
            officer: Enemy(
                channel_id=4,
                sounds=EnemySounds(
                    attack=machinegun,
                    death=scream_4,
                    appearance=halt_2
                ),
                hp=50,
                speed=0.06,
                wandering_radius=3,
                shooting_range=8,
                looting_ammo=8,
                damage_multiplier=0.00,
                accuracy=1.05,
                pain_chance=0.50,
                memory=90,
                death_frames=5,
                shooting_rows=(6, 7),
                shot_rows=7,
                shooting_pattern=(0, 0, 1, 0, 1)
            ),
            ss: Enemy(
                channel_id=4,
                sounds=EnemySounds(
                    attack=machinegun,
                    death=scream_4,
                    appearance=halt_2
                ),
                hp=50,
                speed=0.06,
                wandering_radius=3,
                shooting_range=8,
                looting_ammo=8,
                damage_multiplier=0.00,
                accuracy=1.05,
                pain_chance=0.50,
                memory=90,
                death_frames=5,
                shooting_rows=(6, 7),
                shot_rows=7,
                shooting_pattern=(0, 0, 1, 0, 1)
            ),
            mutant: Enemy(
                channel_id=4,
                sounds=EnemySounds(
                    attack=machinegun,
                    death=scream_4,
                    appearance=halt_2
                ),
                hp=50,
                speed=0.06,
                wandering_radius=3,
                shooting_range=8,
                looting_ammo=8,
                damage_multiplier=0.00,
                accuracy=1.05,
                pain_chance=0.50,
                memory=90,
                death_frames=5,
                shooting_rows=(6, 7),
                shot_rows=7,
                shooting_pattern=(0, 0, 1, 0, 1)
            ),
            dog: Enemy(
                channel_id=4,
                sounds=EnemySounds(
                    attack=machinegun,
                    death=scream_4,
                    appearance=halt_2
                ),
                hp=50,
                speed=0.06,
                wandering_radius=3,
                shooting_range=8,
                looting_ammo=8,
                damage_multiplier=0.00,
                accuracy=1.05,
                pain_chance=0.50,
                memory=90,
                death_frames=5,
                shooting_rows=(6, 7),
                shot_rows=7,
                shooting_pattern=(0, 0, 1, 0, 1)
            ),
            formerhuman: Enemy(
                channel_id=4,
                sounds=EnemySounds(
                    attack=machinegun,
                    death=scream_4,
                    appearance=halt_2
                ),
                hp=50,
                speed=0.06,
                wandering_radius=3,
                shooting_range=8,
                looting_ammo=8,
                damage_multiplier=1.10,
                accuracy=1.05,
                pain_chance=0.50,
                memory=90,
                death_frames=5,
                shooting_rows=(6, 7),
                shot_rows=(7),
                shooting_pattern=(0, 0, 1, 0, 1)
            )
        }
        return enemy_info
