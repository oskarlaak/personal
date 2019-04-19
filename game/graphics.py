import pygame
import sys


def get_door_side_texture():
    try:
        door_side_texture = pygame.image.load('../textures/doors/side.png').convert()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        return door_side_texture


def get_tile_values_info(texture_size, enemy_info):
    class Tile:
        def __init__(self, texture, type, description):
            self.texture = texture
            self.type = type
            self.desc = description

    def assign_texture_sheet(cell_w, cell_h, index_step, texture_sheet, type, description):
        global index  # Sets current index as staring index
        for row in range(int(texture_sheet.get_height() / cell_h)):
            for column in range(int(texture_sheet.get_width() / cell_w)):
                texture = texture_sheet.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                tile_values_info[index] = Tile(texture, type, description)  # Update tile_values_info with Tile object
                index += index_step

    try:
        # Wall textures
        bloodycave = pygame.image.load('../textures/walls/bloodycave.png').convert()
        bluebrick = pygame.image.load('../textures/walls/bluebrick.png').convert()
        bluecellar = pygame.image.load('../textures/walls/bluecellar.png').convert()
        browncobblestone = pygame.image.load('../textures/walls/browncobblestone.png').convert()
        brownstone = pygame.image.load('../textures/walls/brownstone.png').convert()
        cobblestone = pygame.image.load('../textures/walls/cobblestone.png').convert()
        elevator = pygame.image.load('../textures/walls/elevator.png').convert()
        metal = pygame.image.load('../textures/walls/metal.png').convert()
        purplecave = pygame.image.load('../textures/walls/purplecave.png').convert()
        redbrick = pygame.image.load('../textures/walls/redbrick.png').convert()
        stone = pygame.image.load('../textures/walls/stone.png').convert()
        wood = pygame.image.load('../textures/walls/wood.png').convert()
        end_trigger = pygame.image.load('../textures/walls/endtrigger.png').convert()

        # Door textures
        dynamic_doors = pygame.image.load('../textures/doors/dynamic.png').convert()
        static_doors = pygame.image.load('../textures/doors/static.png').convert()

        # Object sprites
        nonsolids = pygame.image.load('../textures/objects/nonsolids.png').convert_alpha()
        solids = pygame.image.load('../textures/objects/solids.png').convert_alpha()

        # Dynamic objects
        firstaid = pygame.image.load('../textures/objects/dynamic/firstaid.png').convert_alpha()
        food = pygame.image.load('../textures/objects/dynamic/food.png').convert_alpha()
        dogfood = pygame.image.load('../textures/objects/dynamic/dogfood.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        # tile_values_info texture assigning can happen manually and via assign_texture_sheet()
        # Last on is used to assign whole texture sheets (usually same themed textures) at once with same description
        tile_values_info = {}

        # Creates a global index var bc it's needed in assign_texture_sheet()
        global index
        index = 0

        # ---Negative values---
        tile_values_info[index] = Tile(None, 'Empty', '')

        # Dynamic objects
        index -= 1
        tile_values_info[index] = Tile(firstaid, 'Object', '+25 Health')
        index -= 1
        tile_values_info[index] = Tile(food, 'Object', '+10 Health')
        index -= 1
        tile_values_info[index] = Tile(dogfood, 'Object', '+4 Health')

        # Other non-solid objects
        index -= 1
        assign_texture_sheet(texture_size, texture_size, -1, nonsolids, 'Object', 'Non-solid')

        # ---Positive values---
        # Solid objects
        index = 1
        assign_texture_sheet(texture_size, texture_size, 1, solids, 'Object', 'Solid')

        # Doors
        assign_texture_sheet(texture_size * 2, texture_size, 1, dynamic_doors, 'Door', 'Dynamic')
        assign_texture_sheet(texture_size * 2, texture_size, 1, static_doors, 'Door', 'Static')

        # Walls
        assign_texture_sheet(texture_size * 2, texture_size, 1, bloodycave, 'Wall', 'Bloody Cave')
        assign_texture_sheet(texture_size * 2, texture_size, 1, bluebrick, 'Wall', 'Blue Brick')
        assign_texture_sheet(texture_size * 2, texture_size, 1, bluecellar, 'Wall', 'Blue Cellar')
        assign_texture_sheet(texture_size * 2, texture_size, 1, browncobblestone, 'Wall', 'Brown Cobblestone')
        assign_texture_sheet(texture_size * 2, texture_size, 1, brownstone, 'Wall', 'Brown Stone')
        assign_texture_sheet(texture_size * 2, texture_size, 1, cobblestone, 'Wall', 'Cobblestone')
        assign_texture_sheet(texture_size * 2, texture_size, 1, elevator, 'Wall', 'Elevator')
        assign_texture_sheet(texture_size * 2, texture_size, 1, metal, 'Wall', 'Metal')
        assign_texture_sheet(texture_size * 2, texture_size, 1, purplecave, 'Wall', 'Purple Cave')
        assign_texture_sheet(texture_size * 2, texture_size, 1, redbrick, 'Wall', 'Red Brick')
        assign_texture_sheet(texture_size * 2, texture_size, 1, stone, 'Wall', 'Stone')
        assign_texture_sheet(texture_size * 2, texture_size, 1, wood, 'Wall', 'Wood')

        # Both end trigger texture variants
        assign_texture_sheet(texture_size * 2, texture_size, 1, end_trigger, 'Wall', 'End-trigger')

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
    tile_values_info = get_tile_values_info(64, enemies.get_enemy_info())

    for value in sorted(tile_values_info):
        tile_obj = tile_values_info[value]
        print('{}: texture: {}, type: {}, description: {}'
              .format(value, tile_obj.texture, tile_obj.type, tile_obj.desc))
