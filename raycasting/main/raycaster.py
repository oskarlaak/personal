# Main TODOs:
# Try to rework player collision once again
# Revisit and fix comments

# Later:
# Add enemy "AI"
# Add things to README
# Add weapons + shooting

# NOTES:
# Movement keys are handled in movement() and other keys in events()
# All angles are in radians
# Objects are in OBJECTS list only if that object's cell is visible to player
# Enemies are in ENEMIES list at all times
# Wall texture files require two textures side by side (even if they are going to be the same),
# bc raycast() is going to pick one based on the side of interception
# All timed events are tick based,
# meaning that changing fps will change timer time - might want to change

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

import raycasting.main.tilevaluesinfo as tilevaluesinfo

# Game settings
INFO_LAYER = False
D_W = 1024
D_H = 800
FOV = pi / 2  # = 90 degrees
RAYS_AMOUNT = int(D_W / 2)  # Drawing frequency across the screen / Rays casted each frame
SENSITIVITY = 0.003  # Radians turned per every pixel the mouse has moved horizontally

# Pygame stuff
pygame.init()
pygame.display.set_caption('Raycaster')
DISPLAY = pygame.display.set_mode((D_W, D_H))
CLOCK = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Font stuff
pygame.font.init()
FONT_SIZE = 20
myfont = pygame.font.SysFont('franklingothicmedium', FONT_SIZE)


class Player:
    speed = 0.15  # Must be < half_hitbox, otherwise collisions will not work
    half_hitbox = 0.2

    def __init__(self, pos, angle):
        self.x, self.y = pos
        self.viewangle = angle + 0.0000001
        self.hp = 100
        self.ammo = 10

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def move(self, x_move, y_move):
        # Moving player to check collision
        self.x += x_move
        self.y += y_move

        # Hitbox sides
        right = self.x + Player.half_hitbox
        left = self.x - Player.half_hitbox
        down = self.y + Player.half_hitbox
        up = self.y - Player.half_hitbox

        # Everything that player can walk on is less than 0 on tilemap
        # So these will return True if there is a collision
        down_right = TILEMAP[int(down)][int(right)] > 0
        down_left = TILEMAP[int(down)][int(left)] > 0
        up_right = TILEMAP[int(up)][int(right)] > 0
        up_left = TILEMAP[int(up)][int(left)] > 0

        # If hitting something, find the collision type
        if down_right or up_right or down_left or up_left:
            x_collision = False
            y_collision = False

            # If diagonals touching
            if down_right and up_left or down_left and up_right:
                x_collision = True
                y_collision = True

            # If top or bottom touching
            elif down_right and down_left or up_right and up_left:
                y_collision = True

            # If left or right touching
            elif down_right and up_right or down_left and up_left:
                x_collision = True

            # If one corner touching
            else:
                if down_right:
                    edge_x = right
                    edge_y = down
                elif down_left:
                    edge_x = left
                    edge_y = down
                elif up_right:
                    edge_x = right
                    edge_y = up
                else:
                    edge_x = left
                    edge_y = up

                x_offset = edge_x - int(edge_x)
                y_offset = edge_y - int(edge_y)

                # Distance to closest round(x/y)
                deltax = abs(round(x_offset) - x_offset)
                deltay = abs(round(y_offset) - y_offset)
                if deltax < deltay:
                    x_collision = True
                else:
                    y_collision = True

            if x_collision:
                if self.x - int(self.x) < Player.half_hitbox:
                    self.x = int(self.x) + Player.half_hitbox
                else:
                    self.x = ceil(self.x) - Player.half_hitbox

            if y_collision:
                if self.y - int(self.y) < Player.half_hitbox:
                    self.y = int(self.y) + Player.half_hitbox
                else:
                    self.y = ceil(self.y) - Player.half_hitbox


class Door:
    speed = 0.04
    open_ticks = 60

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.tile_value = tile_value
        self.ticks = 0
        self.state = 0
        self.opened_state = 0  # 1 is fully opened, 0 is fully closed

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def move(self):
        if self.state > 0:
            if self.state == 1:  # Opening
                self.opened_state += Door.speed
                if self.opened_state > 1:
                    TILEMAP[self.y][self.x] = 0  # Make tile walkable
                    self.opened_state = 1
                    self.state += 1

            if self.state == 2:  # Staying open
                self.ticks += 1
                if self.ticks >= Door.open_ticks:  # If time for door to close
                    # Checking if player is not in door's way
                    safe_dist = 0.5 + Player.half_hitbox
                    if abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist:
                        TILEMAP[self.y][self.x] = self.tile_value  # Make tile non-walkable
                        self.ticks = 0
                        self.state += 1

            if self.state == 3:  # Closing
                self.opened_state -= Door.speed
                if self.opened_state < 0:
                    self.opened_state = 0
                    self.state = 0


class Drawable:
    constant = 0.6 * D_H

    def adjust_image_height(self):
        # Depending on self.height, (it being the unoptimized image drawing height) this system will crop out
        # from given unscaled image as many pixel rows from top and bottom as possible,
        # while ensuring that the player will not notice a difference, when the image is drawn later
        # (that means it will not crop out pixel rows, that are going to be on the screen)
        #
        # It will then also adjust drawing height, so the program later knows, how big to scale the new cropped image
        #
        # Cropping is done before scaling to ensure that the program is not going to be scaling images to enormous sizes

        # Percentage of image that's going to be seen
        percentage = D_H / self.height

        # What would be the perfect cropping size
        perfect_size = TEXTURE_SIZE * percentage

        # However actual cropping size needs to be the closest even* number rounding up perfect_size
        # For example 10.23 will be turned to 12 and 11.78 will also be turned to 12
        # *number needs to be even bc you can't crop at halfpixel
        cropping_size = ceil(perfect_size / 2) * 2

        # Cropping the image smaller - width stays the same
        rect = pygame.Rect((0, (TEXTURE_SIZE - cropping_size) / 2), (self.image.get_width(), cropping_size))
        self.image = self.image.subsurface(rect)

        # Adjusting height accordingly
        multiplier = cropping_size / perfect_size
        self.height = int(D_H * multiplier)


class Wall(Drawable):
    width = int(D_W / RAYS_AMOUNT)

    def __init__(self, perp_dist, texture, column, count):
        self.perp_dist = perp_dist  # Needs saving to sort by it later

        # Cropping 1 pixel wide column out of texture
        self.image = texture.subsurface(column, 0, 1, TEXTURE_SIZE)

        self.height = int(Drawable.constant / self.perp_dist)
        if self.height > D_H:
            self.adjust_image_height()

        # Resizing the image and getting it's position
        self.display_x = count * Wall.width
        self.display_y = (D_H - self.height) / 2
        self.image = pygame.transform.scale(self.image, (Wall.width, self.height))

    def draw(self, surface):
        surface.blit(self.image, (self.display_x, self.display_y))


class Sprite:
    def draw(self, surface):
        # Optimized sprite drawing function made for Enemies and Objects

        if self.perp_dist > 0:
            # Since sprite's out of bounds top and bottom parts are already cut out
            # the program can now draw all sprite pixel columns, that are in display area

            column_width = self.width / TEXTURE_SIZE
            column_left_side = self.display_x
            column_right_side = self.display_x + column_width

            for column in range(TEXTURE_SIZE):
                column_left_side += column_width
                column_right_side += column_width

                if column_left_side < D_W and column_right_side > 0:  # If row on screen

                    # Getting sprite column out of image
                    sprite_column = self.image.subsurface(column, 0, 1, self.image.get_height())

                    # Scaling that column
                    sprite_column = pygame.transform.scale(sprite_column, (ceil(column_width), self.height))

                    # Blitting that column
                    surface.blit(sprite_column, (column_left_side, self.display_y))

    def calc_display_xy(self, angle_from_player):
        # In order to calculate sprite's correct display x/y position, we need to calculate it's camera plane position
        # NOTE: atan2(delta_y, delta_x) is the angle from player to sprite

        camera_plane_pos = CAMERA_PLANE_LEN / 2 + tan(angle_from_player - PLAYER.viewangle) * CAMERA_PLANE_DIST

        self.display_x = D_W * camera_plane_pos - self.width / 2
        self.display_y = (D_H - self.height) / 2


class Object(Drawable, Sprite):
    def __init__(self, map_pos, tilevalue):
        self.x = map_pos[0] + 0.5
        self.y = map_pos[1] + 0.5

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        self.perp_dist = delta_x * VIEWANGLE_DIR_X + delta_y * VIEWANGLE_DIR_Y

        if self.perp_dist > 0:
            self.image = TILE_VALUES_INFO[tilevalue][1]  # Name needs to be self.image for it to work in adjust_image_height()

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            angle_from_player = atan2(delta_y, delta_x)

            self.calc_display_xy(angle_from_player)

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)


class Enemy(Drawable, Sprite):
    def __init__(self, spritesheet, pos):
        self.x, self.y = pos
        self.sheet = spritesheet
        # Take attributes from ENEMY_INFO based on spritesheet
        self.hp = ENEMY_INFO[self.sheet]

        self.angle = 0
        self.state = 0

    def update(self):
        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        angle_from_player = atan2(delta_y, delta_x)

        self.perp_dist = delta_x * VIEWANGLE_DIR_X + delta_y * VIEWANGLE_DIR_Y

        if self.perp_dist > 0:
            row = self.state
            if row < 5:  # If walking or standing
                angle = fixed_angle(-angle_from_player - self.angle) + pi  # +pi to get rid of negative values
                column = round(angle / (pi / 4))
                if column == 8:
                    column = 0

            self.image = self.sheet.subsurface(column * TEXTURE_SIZE, row * TEXTURE_SIZE, TEXTURE_SIZE, TEXTURE_SIZE)

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            self.calc_display_xy(angle_from_player)


def events():
    global RUNNING
    global INFO_LAYER

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                RUNNING = False

            if event.key == K_F1:
                INFO_LAYER = not INFO_LAYER

            if event.key == K_e:
                x = int(PLAYER.x + VIEWANGLE_DIR_X)
                y = int(PLAYER.y + VIEWANGLE_DIR_Y)
                tile_id = TILE_VALUES_INFO[TILEMAP[y][x]][0]
                if tile_id[0] == 'Door' and tile_id[1] == 'Dynamic':
                    for d in DOORS:
                        # If found the right door and it's not in motion already
                        if x == d.x and y == d.y and d.state == 0:
                            d.state = 1
                            break
                elif tile_id[0] == 'Wall' and tile_id[1] == 'End-trigger':
                    TILEMAP[y][x] += 1  # Change triggerblock texture
                    #level_end()


def update_doors():
    for d in DOORS:
        d.move()
    for e in ENEMIES:
        e.update()


def draw_frame():
    # Sorting objects by perp_dist so those further away are drawn first
    to_draw = WALLS + ENEMIES + OBJECTS
    to_draw.sort(key=lambda x: x.perp_dist, reverse=True)
    for obj in to_draw:
        obj.draw(DISPLAY)


def load_textures():
    global TEXTURE_SIZE
    TEXTURE_SIZE = 64

    global TILE_VALUES_INFO
    global ENEMY_INFO
    global DOOR_SIDE_TEXTURE
    TILE_VALUES_INFO, ENEMY_INFO, DOOR_SIDE_TEXTURE = tilevaluesinfo.get(TEXTURE_SIZE)


def load_level(level_nr):
    global DOORS
    DOORS = []

    # Decoding tilemap
    with open('../levels/{}/tilemap.txt'.format(level_nr), 'r') as f:
        global PLAYER
        row = f.readline().replace('\n', '').split(',')
        row = [float(i) for i in row]
        PLAYER = Player((row[0], row[1]), row[2])  # Creates player

        global BACKGROUND_COLOURS
        BACKGROUND_COLOURS = []
        for _ in range(2):
            row = f.readline().replace('\n', '').split(',')  # Split the line to a list and get rid of newline (\n)
            row = [int(i) for i in row]  # Turn all number strings to an int
            BACKGROUND_COLOURS.append(tuple(row))

        global TILEMAP
        TILEMAP = []
        for line in f:
            row = line.replace('\n', '')  # Get rid of newline (\n)
            row = row[1:-1]  # Get rid of '[' and ']'
            row = row.split(',')  # Split line into list
            row = [int(i) for i in row]  # Turn all number strings to an int
            TILEMAP.append(row)

    # Scan through all of tilemap
    # Create a enemy if tile id is correct
    global ENEMIES
    ENEMIES = []
    for row in range(len(TILEMAP)):
        for column in range(len(TILEMAP[row])):
            tile_id = TILE_VALUES_INFO[TILEMAP[row][column]][0]
            if tile_id[0] == 'Enemy':
                spritesheet = TILE_VALUES_INFO[TILEMAP[row][column]][1]
                pos = (column + 0.5, row + 0.5)
                ENEMIES.append(Enemy(spritesheet, pos))
                TILEMAP[row][column] = 0  # Clears tile


def get_rayangles():
    # Returns a list of angles which raycast() is going to use to add to player's viewangle
    # Because these angles do not depend on player's viewangle, they are calculated even before the main loop starts
    #
    # It calculates these angles so that each angle's end position is on the camera plane,
    # equal distance away from the previous one
    #
    # Could be made faster, but since it's calculated only once before main loop, readability is more important
    # Note that in 2D rendering, camera plane is actually a single line
    # Also FOV has to be < pi (and not <= pi) for it to work properly
    global RAYANGLES
    RAYANGLES = []

    # These global values are needed to calculate sprite display_x position
    global CAMERA_PLANE_LEN
    global CAMERA_PLANE_DIST

    CAMERA_PLANE_LEN = 1
    camera_plane_start = -CAMERA_PLANE_LEN / 2
    camera_plane_step = CAMERA_PLANE_LEN / RAYS_AMOUNT

    CAMERA_PLANE_DIST = (CAMERA_PLANE_LEN / 2) / tan(FOV / 2)
    for i in range(RAYS_AMOUNT):
        camera_plane_pos = camera_plane_start + i * camera_plane_step

        angle = atan2(camera_plane_pos, CAMERA_PLANE_DIST)
        RAYANGLES.append(angle)


def send_rays():
    global WALLS
    WALLS = []

    global OBJECTS
    OBJECTS = []

    for c, d in enumerate(DOORS):
        if d.state == 0:  # If door not in motion
            del DOORS[c]

    # Checking if player is standing on an object
    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:  # If anything under player
        tile_id = TILE_VALUES_INFO[tile_value][0]
        if tile_id[1] == 'Ammo':
            if PLAYER.ammo < 99:
                PLAYER.ammo += 6
                if PLAYER.ammo > 99:
                    PLAYER.ammo = 99
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0  # "Deletes" object
        elif tile_id[1] == 'Health':
            if PLAYER.hp < 100:
                PLAYER.hp += 20
                if PLAYER.hp > 100:
                    PLAYER.hp = 100
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0  # "Deletes" object
        OBJECTS.append(Object((int(PLAYER.x), int(PLAYER.y)), tile_value))

    # Sending rays
    for i in range(len(RAYANGLES)):
        # Get the rayangle that's going to be raycasted
        rayangle = fixed_angle(PLAYER.viewangle + RAYANGLES[i])

        # Get values from raycast()
        tile_value, ray_x, ray_y, column = raycast(rayangle)
        delta_x = ray_x - PLAYER.x
        delta_y = ray_y - PLAYER.y

        # Calculate perpendicular distance (needed to avoid fisheye effect)
        perp_dist = delta_x * VIEWANGLE_DIR_X + delta_y * VIEWANGLE_DIR_Y

        # Get wall texture
        for d in DOORS:
            # Ray x and y abs(distances) to door center position
            x_diff = abs(d.x + 0.5 - ray_x)
            y_diff = abs(d.y + 0.5 - ray_y)
            if (x_diff == 0.5 and y_diff <= 0.5) or (y_diff == 0.5 and x_diff <= 0.5):
                texture = DOOR_SIDE_TEXTURE
                break
        else:
            texture = TILE_VALUES_INFO[tile_value][1]

        # Create Wall object
        WALLS.append(Wall(perp_dist, texture, column, i))


def raycast(rayangle):
    #   Variables depending
    #     on the rayangle
    #            |
    #      A = 0 | A = 1
    # -pi  B = 0 | B = 0  -
    #     -------|------- 0 rad
    #  pi  A = 0 | A = 1  +
    #      B = 1 | B = 1
    #            |

    if abs(rayangle) > pi / 2:
        A = 0
    else:
        A = 1
    if rayangle < 0:
        B = 0
    else:
        B = 1

    ray_x = PLAYER.x
    ray_y = PLAYER.y
    tan_rayangle = tan(rayangle)  # Calculating tay(rayangle) once to not calculate it over every step

    while True:
        # "if (x/y)_offset == (A/B)" only resets offset depending on the rayangle
        # This will help to determine interception type correctly
        # and it also prevents rays getting stuck on some angles

        x_offset = ray_x - int(ray_x)
        if x_offset == A:
            x_offset = 1

        y_offset = ray_y - int(ray_y)
        if y_offset == B:
            y_offset = 1

        # Very simple system
        # Every loop it blindly calculates vertical* gridline interception_y and checks it's distance
        # to determine the interception type and to calculate other varibles depending on that interception type
        # Originally it remembered previous interception type to calculate the new one
        # but doing it this way turns out to be faster
        #
        # *It calculates vertical gridline interception by default bc in those calculations
        # there are no divisions which could bring up ZeroDivisionError

        interception_y = (A - x_offset) * tan_rayangle
        if int(ray_y - y_offset) == int(ray_y + interception_y):
            # Hitting vertical gridline ( | )
            interception_x = A - x_offset

            ray_x += interception_x
            ray_y += interception_y
            map_y = int(ray_y)
            map_x = int(ray_x) + (A - 1)
            side = 0

        else:
            # Hitting horizontal gridline ( -- )
            interception_x = (B - y_offset) / tan_rayangle
            interception_y = B - y_offset

            ray_x += interception_x
            ray_y += interception_y
            map_y = int(ray_y) + (B - 1)
            map_x = int(ray_x)
            side = 1

        tile_value = TILEMAP[map_y][map_x]
        if tile_value != 0:  # If ray touching something

            tile_id = TILE_VALUES_INFO[tile_value][0]

            if tile_id[0] == 'Object':
                obj = Object((map_x, map_y), tile_value)
                for o in OBJECTS:
                    if o == obj:
                        break
                else:
                    OBJECTS.append(obj)
                continue

            if tile_id[0] == 'Door':
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                # Add door to DOORS if it's not in it already
                door = Door((map_x, map_y), tile_value)
                for d in DOORS:
                    if d == door:
                        door = d
                        break
                else:
                    DOORS.append(door)

                if side == 0:  # If vertical ( | )
                    interception_y = (-0.5 + A) * tan_rayangle
                    offset = ray_y + interception_y - int(ray_y + interception_y)
                    if int(ray_y - y_offset) == int(ray_y + interception_y) and offset > door.opened_state:
                        ray_x += (-0.5 + A)
                        ray_y += interception_y
                        column = int(TEXTURE_SIZE * (offset - door.opened_state))
                    else:
                        continue

                else:  # If horizontal ( -- )
                    interception_x = (-0.5 + B) / tan_rayangle
                    offset = ray_x + interception_x - int(ray_x + interception_x)
                    if int(ray_x - x_offset) == int(ray_x + interception_x) and offset > door.opened_state:
                        ray_x += interception_x
                        ray_y += (-0.5 + B)
                        column = int(TEXTURE_SIZE * (offset - door.opened_state))
                    else:
                        continue

            else:  # If anything other but a door (door sides count here aswell)
                if side == 0:
                    offset = abs(ray_y - int(ray_y) - (1 - A))
                else:
                    offset = abs(ray_x - int(ray_x) - B)
                column = int(TEXTURE_SIZE * offset)

            if side == 0:
                column += TEXTURE_SIZE  # Makes block sides different

            return tile_value, ray_x, ray_y, column


def fixed_angle(angle):
    # Function made for angles to never go over +-pi
    # For example 3.18 will be turned to -3.10, bc it's 0.04 over pi

    if angle > pi:  # 3.14+
        angle -= 2 * pi

    elif angle < -pi:  # 3.14-
        angle += 2 * pi

    return angle


def mouse():
    radians = pygame.mouse.get_rel()[0] * SENSITIVITY
    PLAYER.rotate(radians)


def movement():
    global VIEWANGLE_DIR_X
    global VIEWANGLE_DIR_Y
    VIEWANGLE_DIR_X = cos(PLAYER.viewangle)
    VIEWANGLE_DIR_Y = sin(PLAYER.viewangle)

    keys = pygame.key.get_pressed()
    # Vector based movement, bc otherwise player could move faster diagonally
    if keys[K_w] or keys[K_a] or keys[K_s] or keys[K_d]:
        movement_x = 0
        movement_y = 0
        if keys[K_w]:
            movement_x += VIEWANGLE_DIR_X
            movement_y += VIEWANGLE_DIR_Y

        if keys[K_a]:
            movement_x += VIEWANGLE_DIR_Y
            movement_y += -VIEWANGLE_DIR_X

        if keys[K_s]:
            movement_x += -VIEWANGLE_DIR_X
            movement_y += -VIEWANGLE_DIR_Y

        if keys[K_d]:
            movement_x += -VIEWANGLE_DIR_Y
            movement_y += VIEWANGLE_DIR_X

        # Needed for normalize() function
        movement_vector = np.asarray([[movement_x, movement_y]])

        # Removes the errors where pressing both (or all) opposite movement keys, player would still move,
        # bc the movement vector would not be a perfect (0, 0)
        if abs(movement_vector[0][0]) + abs(movement_vector[0][1]) > 0.1:

            # Normalized vector
            normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list with one element
            movement_x = normalized_vector[0] * PLAYER.speed
            movement_y = normalized_vector[1] * PLAYER.speed

            PLAYER.move(movement_x, movement_y)


def bottom_layer():
    pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[0], ((0,       0), (D_W, D_H / 2)))  # Ceiling
    pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[1], ((0, D_H / 2), (D_W, D_H / 2)))  # Floor


def top_layer():
    if INFO_LAYER:
        text_color = (255, 255, 255)
        decimals = 3

        fps_text = 'FPS: {}'.format(int(CLOCK.get_fps()))
        fps_image = myfont.render(fps_text, True, text_color)

        player_x_text = 'X: {}'.format(round(PLAYER.x, decimals))
        player_x_image = myfont.render(player_x_text, True, text_color)

        player_y_text = 'Y: {}'.format(round(PLAYER.y, decimals))
        player_y_image = myfont.render(player_y_text, True, text_color)

        viewangle_text = 'RAD: {}'.format(round(PLAYER.viewangle, decimals))
        viewangle_image = myfont.render(viewangle_text, True, text_color)

        DISPLAY.blit(      fps_image, (4, FONT_SIZE * 0))
        DISPLAY.blit( player_x_image, (4, FONT_SIZE * 1))
        DISPLAY.blit( player_y_image, (4, FONT_SIZE * 2))
        DISPLAY.blit(viewangle_image, (4, FONT_SIZE * 3))


def game_loop():
    get_rayangles()
    load_textures()
    load_level(1)

    global RUNNING
    RUNNING = True
    while RUNNING:
        events()
        mouse()
        movement()

        bottom_layer()
        update_doors()
        send_rays()
        draw_frame()
        top_layer()

        pygame.display.flip()
        CLOCK.tick(30)

    pygame.quit()


game_loop()
