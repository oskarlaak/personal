# Main TODOs:
# Add doors opening/closing system
# Add enemies - spritesheet class

# NOTES:
# Movement keys are handled in movement() and other keys in events()
# All angles are in radians
# Sprites class is currently unused

# Current tilemap system:
# 0 - empty
# 1 - door
# 2 - ... walls

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

import sys

# Game settings
INFO_LAYER = False
SHADES = True
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

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.viewangle = angle

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def move(self, x_move, y_move):
        self.x += x_move
        self.y += y_move

        # Hitbox sides
        right = self.x + Player.half_hitbox
        left = self.x - Player.half_hitbox
        down = self.y + Player.half_hitbox
        up = self.y - Player.half_hitbox

        down_right = TILEMAP[int(down)][int(right)] > 0  # <-- Number of sprites you can walk through/over
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


class Object:
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


class Wall(Object):
    width = int(D_W / RAYS_AMOUNT)

    def __init__(self, perp_dist, texture, column, count):
        self.perp_dist = perp_dist  # Needs saving to sort by it later

        # Cropping 1 pixel wide column out of texture
        self.image = texture.subsurface(column, 0, 1, TEXTURE_SIZE)

        self.height = int(Object.constant / perp_dist)
        if self.height > D_H:
            self.adjust_image_height()

        # Resizing the image and getting it's position
        self.display_x = count * Wall.width
        self.display_y = (D_H - self.height) / 2
        self.image = pygame.transform.scale(self.image, (Wall.width, self.height))

    def draw(self, surface):
        surface.blit(self.image, (self.display_x, self.display_y))


class Sprite(Object):
    def __init__(self, perp_dist, sprite, x, y):
        self.perp_dist = perp_dist
        self.image = sprite  # Name needs to be self.image for it to work in adjust_image_height()
        self.x = x
        self.y = y

        self.height = self.width = int(Object.constant / perp_dist)
        if self.height > D_H:
            self.adjust_image_height()

        # To find the sprite's display_x position, we need to know it's camera plane position
        # NOTE:
        # atan2(delta_y, delta_x) is the angle from player to sprite
        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y

        angle_from_viewangle = atan2(delta_y, delta_x) - PLAYER.viewangle
        camera_plane_pos = CAMERA_PLANE_LEN / 2 + tan(angle_from_viewangle) * CAMERA_PLANE_DIST

        self.display_x = D_W * camera_plane_pos - self.width / 2
        self.display_y = (D_H - self.height) / 2

    def draw(self, surface):
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


class Door:
    def __init__(self, map_x, map_y):
        self.x = map_x
        self.y = map_y
        self.opened_state = 0  # 1 is fully opened, 0 is fully closed

    def __eq__(self, other):
        # Two doors are "equal" if their position is the same, opened_state doesn't matter
        return (self.x, self.y) == (other.x, other.y)


def draw_walls():
    # Sorting objects by perp_dist so those further away are drawn first
    TO_DRAW = WALLS
    TO_DRAW.sort(key=lambda x: x.perp_dist, reverse=True)
    for obj in TO_DRAW:
        obj.draw(DISPLAY)


def load_textures():
    global TILEMAP_TEXTURES
    global TEXTURE_SIZE
    TEXTURE_SIZE = 64

    try:
        door_textures = pygame.image.load('textures/door.png').convert()
        wall_textures = pygame.image.load('textures/wall_textures.png').convert()

    except pygame.error as exception:
        sys.exit(exception)

    else:  # If no error when loading textures
        TILEMAP_TEXTURES = {}
        index = 1  # Starting at 1 bc 0 means empty

        # Doors
        TILEMAP_TEXTURES[index] = door_textures
        index += 1

        # Walls
        # Because each texture "cell" contains two textures, cell width is going to be twice as big as cell height
        cell_w = TEXTURE_SIZE * 2
        cell_h = TEXTURE_SIZE
        for row in range(int(wall_textures.get_height() / cell_h)):

            for column in range(int(wall_textures.get_width() / cell_w)):

                texture = wall_textures.subsurface(column * cell_w, row * cell_h, cell_w, cell_h)
                TILEMAP_TEXTURES[index] = texture
                index += 1


def read_tilemap():
    # Getting tilemap from text file
    global TILEMAP
    TILEMAP = []
    with open('tilemap.txt', 'r') as f:
        for line in f:
            if len(line) == 1:  # If line only consists of '\n' / If line empty ; Allows comments in tilemap.txt
                break

            row = line.replace('\n', '').split(',')  # Split the line to a list and get rid of newline (\n)
            row = [int(i) for i in row]  # Turn all number strings to an int
            TILEMAP.append(row)


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

    for c, d in enumerate(DOORS):
        if d.opened_state == 0:  # If door closed
            del DOORS[c]

    viewangle_dir_x = cos(PLAYER.viewangle)
    viewangle_dir_y = sin(PLAYER.viewangle)

    # Sending rays
    for c, angle in enumerate(RAYANGLES):
        # Get the rayangle that's going to be raycasted
        rayangle = fixed_angle(PLAYER.viewangle + angle)

        # Get values from raycast()
        grid_value, delta_x, delta_y, column = raycast(rayangle)

        # Calculate perpendicular distance (needed to avoid fisheye effect)
        perp_dist = delta_x * viewangle_dir_x + delta_y * viewangle_dir_y

        # Get wall texture from TILEMAP_TEXTURES
        texture = TILEMAP_TEXTURES[grid_value]

        # Create Wall object
        WALLS.append(Wall(perp_dist, texture, column, c))


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

    tan_rayangle = tan(rayangle)

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

        grid_value = TILEMAP[map_y][map_x]
        if grid_value != 0:  # If ray touching something

            if grid_value == 1:  # If door
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                # Add door to DOORS if it's not in it already
                door = Door(map_x, map_y)
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
                    offset = ray_y - int(ray_y)
                else:
                    offset = ray_x - int(ray_x)
                column = int(TEXTURE_SIZE * offset)

            if SHADES and side == 0:
                column += TEXTURE_SIZE  # Makes block sides different

            delta_x = ray_x - PLAYER.x
            delta_y = ray_y - PLAYER.y

            return grid_value, delta_x, delta_y, column


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
    keys = pygame.key.get_pressed()

    # Vector based movement, bc otherwise player could move faster diagonally
    if keys[K_w] or keys[K_a] or keys[K_s] or keys[K_d]:
        movement_x = 0
        movement_y = 0
        if keys[K_w]:
            movement_x += cos(PLAYER.viewangle)
            movement_y += sin(PLAYER.viewangle)

        if keys[K_a]:
            movement_x += cos(PLAYER.viewangle - pi / 2)
            movement_y += sin(PLAYER.viewangle - pi / 2)

        if keys[K_s]:
            movement_x += cos(PLAYER.viewangle - pi)
            movement_y += sin(PLAYER.viewangle - pi)

        if keys[K_d]:
            movement_x += cos(PLAYER.viewangle + pi / 2)
            movement_y += sin(PLAYER.viewangle + pi / 2)

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


def events():
    global RUNNING
    global INFO_LAYER
    global SHADES

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                RUNNING = False

            if event.key == K_F1:
                INFO_LAYER = not INFO_LAYER

            if event.key == K_F2:
                SHADES = not SHADES


def bottom_layer():
    pygame.draw.rect(DISPLAY, ( 50,  50,  50), ((0,       0), (D_W, D_H / 2)))  # Ceiling
    pygame.draw.rect(DISPLAY, (100, 100, 100), ((0, D_H / 2), (D_W, D_H / 2)))  # Floor


def top_layer():
    if INFO_LAYER:
        text_color = (255, 255, 255)
        decimals = 3

        FPS_text = 'FPS: {}'.format(int(CLOCK.get_fps()))
        FPS_image = myfont.render(FPS_text, True, text_color)

        player_x_text = 'X: {}'.format(round(PLAYER.x, decimals))
        player_x_image = myfont.render(player_x_text, True, text_color)

        player_y_text = 'Y: {}'.format(round(PLAYER.y, decimals))
        player_y_image = myfont.render(player_y_text, True, text_color)

        viewangle_text = 'RAD: {}'.format(round(PLAYER.viewangle, decimals))
        viewangle_image = myfont.render(viewangle_text, True, text_color)

        DISPLAY.blit(      FPS_image, (4, FONT_SIZE * 0))
        DISPLAY.blit( player_x_image, (4, FONT_SIZE * 1))
        DISPLAY.blit( player_y_image, (4, FONT_SIZE * 2))
        DISPLAY.blit(viewangle_image, (4, FONT_SIZE * 3))


def game_loop():
    get_rayangles()
    load_textures()
    read_tilemap()

    global DOORS
    DOORS = []

    global PLAYER
    PLAYER = Player(7.8, 3.5, 0)  # Creates player

    global RUNNING
    RUNNING = True

    while RUNNING:
        events()
        mouse()
        movement()

        bottom_layer()
        send_rays()
        draw_walls()
        top_layer()

        pygame.display.flip()
        CLOCK.tick(30)

    pygame.quit()


game_loop()
