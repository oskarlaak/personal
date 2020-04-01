import pygame
import sys


def get_floor_textures(raw_floor_texture):
    from game.settings import TEXTURE_SIZE, FLOOR_RES

    floor_texture = pygame.Surface((TEXTURE_SIZE + FLOOR_RES, TEXTURE_SIZE))
    floor_texture.blit(raw_floor_texture, (0, 0))
    floor_texture.blit(raw_floor_texture.subsurface(0, 0, FLOOR_RES, TEXTURE_SIZE), (TEXTURE_SIZE, 0))

    big_floor_texture = pygame.Surface(((TEXTURE_SIZE + FLOOR_RES) * 2, TEXTURE_SIZE * 2))
    big_floor_texture.blit(pygame.transform.scale(raw_floor_texture, (TEXTURE_SIZE * 2, TEXTURE_SIZE * 2)), (0, 0))
    big_floor_texture.blit(pygame.transform.scale(raw_floor_texture.subsurface(0, 0, FLOOR_RES * 2, TEXTURE_SIZE),
                                                  (FLOOR_RES * 2, TEXTURE_SIZE * 2)), (TEXTURE_SIZE * 2, 0))
    return floor_texture, big_floor_texture


def get_door_side_and_portal_textures():
    try:
        door_side = pygame.image.load('../textures/doors/side.png').convert()
        blue_portal = pygame.image.load('../textures/walls/blueportal.png').convert_alpha()
        red_portal = pygame.image.load('../textures/walls/redportal.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        return door_side, blue_portal, red_portal


def get_tile_values_info(enemy_info):
    try:
        # Wall textures
        bloodycave = pygame.image.load('../textures/walls/bloodycave.png').convert()
        bluebrick = pygame.image.load('../textures/walls/bluebrick.png').convert()
        bluecellar = pygame.image.load('../textures/walls/bluecellar.png').convert()
        brownstone = pygame.image.load('../textures/walls/brownstone.png').convert()
        cobblestone = pygame.image.load('../textures/walls/cobblestone.png').convert()
        elevator = pygame.image.load('../textures/walls/elevator.png').convert()
        metal = pygame.image.load('../textures/walls/metal.png').convert()
        purplecave = pygame.image.load('../textures/walls/purplecave.png').convert()
        redbrick = pygame.image.load('../textures/walls/redbrick.png').convert()
        stone = pygame.image.load('../textures/walls/stone.png').convert()
        wood = pygame.image.load('../textures/walls/wood.png').convert()
        secret = pygame.image.load('../textures/walls/secret.png').convert()
        end_trigger = pygame.image.load('../textures/walls/endtrigger.png').convert()

        # Thin wall textures
        seethrough = pygame.image.load('../textures/walls/seethrough.png').convert_alpha()

        # Door textures
        dynamic_doors = pygame.image.load('../textures/doors/dynamic.png').convert()
        locked_doors = pygame.image.load('../textures/doors/locked.png').convert()
        boss_doors = pygame.image.load('../textures/doors/boss.png').convert()

        # Object sprites
        dynamics = pygame.image.load('../textures/objects/dynamics.png').convert_alpha()
        nonsolids = pygame.image.load('../textures/objects/nonsolids.png').convert_alpha()
        exploding_barrel = pygame.image.load('../textures/objects/explodingbarrel.png').convert_alpha()
        solids = pygame.image.load('../textures/objects/solids.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        from game.settings import TEXTURE_SIZE

        class Tile:
            def __init__(self, texture, type, description):
                self.texture = texture
                self.type = type
                self.desc = description

        def assign_texture_sheet(texture_sheet, type, description, cell_w=TEXTURE_SIZE, cell_h=TEXTURE_SIZE, step=1):
            global index  # Sets current index as staring index
            for row in range(int(texture_sheet.get_height() / cell_h)):
                for column in range(int(texture_sheet.get_width() / cell_w)):
                    texture = texture_sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                    tile_values_info[index] = Tile(texture, type,
                                                   description)  # Update tile_values_info with Tile object
                    index += step

        # tile_values_info texture assigning can happen manually and via assign_texture_sheet()
        # Last on is used to assign whole texture sheets (usually same themed textures) at once with same description
        tile_values_info = {}

        # Creating a global index var bc it's needed in assign_texture_sheet()
        global index
        index = 0

        # ---Negative values---
        tile_values_info[index] = Tile(None, 'Empty', '')
        index -= 1

        # Dynamic objects
        assign_texture_sheet(dynamics, 'Object', 'Dynamic', step=-1)

        # Other non-solid objects
        assign_texture_sheet(nonsolids, 'Object', 'Non-solid', step=-1)

        # ---Positive values---
        # Solid objects
        index = 1
        tile_values_info[index] = Tile(exploding_barrel, 'Object', 'Explosive')
        index += 1
        assign_texture_sheet(solids, 'Object', 'Solid')

        # Doors
        assign_texture_sheet(dynamic_doors, 'Door', 'Dynamic', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(locked_doors, 'Door', 'Locked', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(boss_doors, 'Door', 'Boss', cell_w=TEXTURE_SIZE * 2)

        # Thin walls
        assign_texture_sheet(seethrough, 'Thin Wall', 'See-through', cell_w=TEXTURE_SIZE * 2)

        # Walls
        assign_texture_sheet(bloodycave, 'Wall', 'Bloody Cave', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(bluebrick, 'Wall', 'Blue Brick', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(bluecellar, 'Wall', 'Blue Cellar', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(brownstone, 'Wall', 'Brown Stone', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(cobblestone, 'Wall', 'Cobblestone', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(elevator, 'Wall', 'Elevator', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(metal, 'Wall', 'Metal', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(purplecave, 'Wall', 'Purple Cave', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(redbrick, 'Wall', 'Red Brick', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(stone, 'Wall', 'Stone', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(wood, 'Wall', 'Wood', cell_w=TEXTURE_SIZE * 2)
        assign_texture_sheet(secret, 'Wall', 'Secret', cell_w=TEXTURE_SIZE * 2)

        # Both end trigger texture variants
        assign_texture_sheet(end_trigger, 'Wall', 'End-trigger', cell_w=TEXTURE_SIZE * 2)

        # For every enemy type in enemy_info, add value to tile_values_info
        for enemy_sheet in enemy_info:
            tile_values_info[index] = Tile(enemy_sheet, 'Enemy', enemy_info[enemy_sheet].type)
            index += 1

        return tile_values_info


if __name__ == '__main__':
    # Prints out tile_values_info if executed directly
    import game.enemies as enemies
    pygame.init()
    pygame.display.set_mode((1, 1))
    tile_values_info = get_tile_values_info(enemies.get_enemy_info())

    for value in sorted(tile_values_info):
        tile = tile_values_info[value]
        print('{}: texture: {}, type: {}, description: {}'.format(value, tile.texture, tile.type, tile.desc))
