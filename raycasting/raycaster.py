# Main TODOs:
# Doors
# Enemies/other sprites
# Automated texture loading system from texturesheet - Spritesheet class

# NOTES:
# Movement keys are handled in movement() and other keys in events()
# All angles are in radians

from math import *

import numpy as np
from sklearn.preprocessing import normalize

import pygame
from pygame.locals import *

import sys

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
myfont = pygame.font.SysFont('franklingothicmedium', 20)


class Player:
    speed = 0.15  # Must be < half_hitbox
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
        right = self.x + self.half_hitbox
        left = self.x - self.half_hitbox
        down = self.y + self.half_hitbox
        up = self.y - self.half_hitbox

        down_right = TILEMAP[int(down)][int(right)] != 0
        down_left = TILEMAP[int(down)][int(left)] != 0
        up_right = TILEMAP[int(up)][int(right)] != 0
        up_left = TILEMAP[int(up)][int(left)] != 0

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
                if self.x - int(self.x) < self.half_hitbox:
                    self.x = int(self.x) + self.half_hitbox
                else:
                    self.x = ceil(self.x) - self.half_hitbox

            if y_collision:
                if self.y - int(self.y) < self.half_hitbox:
                    self.y = int(self.y) + self.half_hitbox
                else:
                    self.y = ceil(self.y) - self.half_hitbox


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


def load_textures():
    global TEXTURE_SIZE
    TEXTURE_SIZE = 64

    try:
        stone_wall_01 = pygame.image.load('textures/stone_wall_01_light.png').convert_alpha()
        stone_wall_01_dark = pygame.image.load('textures/stone_wall_01_dark.png').convert_alpha()

        stone_wall_01_naziflag = pygame.image.load('textures/stone_wall_01_naziflag_light.png').convert_alpha()
        stone_wall_01_naziflag_dark = pygame.image.load('textures/stone_wall_01_naziflag_dark.png').convert_alpha()

    except pygame.error as exception:
        sys.exit(exception)

    else:
        # Assigning textures to tilemap indexes
        global TILEMAP_TEXTURES
        TILEMAP_TEXTURES = {
            1: (stone_wall_01, stone_wall_01_dark),
            2: (stone_wall_01_naziflag, stone_wall_01_naziflag_dark),
            3: None
        }


def get_rayangles():
    # Returns a list of angles which raycast() is going to use to add to player's viewangle
    # Because these angles do not depend on player's viewangle, they are calculated even before the main loop starts
    #
    # Rather complicated system which is going to put a theoretical camera plane with a length of 1 unit,
    # certain amount of x away from player, so that the camera plane matches up with the current FOV value
    # Then it calculates the angles so that each angle's end position is on the camera plane,
    # equal distance away from the previous one
    #
    # Could be made faster, but since it's calculated only once before main loop, readability is more important
    # Note that in 2D rendering, camera plane is actually a single line
    # Also FOV has to be < pi (and not <= pi) for it to work properly
    global RAYANGLES
    RAYANGLES = []

    camera_plane_len = 1
    camera_plane_start_y = -camera_plane_len / 2
    y_difference = camera_plane_len / RAYS_AMOUNT

    camera_plane_x = (camera_plane_len / 2) / tan(FOV / 2)
    for i in range(RAYS_AMOUNT):
        camera_plane_y = camera_plane_start_y + i * y_difference

        angle = atan2(camera_plane_y, camera_plane_x)
        RAYANGLES.append(angle)


def raycast():
    global WALL_DATA
    WALL_DATA = []

    # Precalculating PLAYER's viewangle dir(x/y) to use it when collision found
    viewangle_dir_x = cos(PLAYER.viewangle)
    viewangle_dir_y = sin(PLAYER.viewangle)

    # Sending rays
    for angle in RAYANGLES:
        rayangle = fixed_angle(PLAYER.viewangle + angle)
        tan_rayangle = tan(rayangle)

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
            # Every loop it blindly calculates vertical* gridline Interception_y and checks it's distance
            # to determine the interception type and to calculate other varibles depending on that interception type
            # Originally it remembered previous interception type to calculate the new one
            # but doing it this way turns out to be slightly faster
            #
            # *It calculates vertical gridline interception by default bc in those calculations
            # there are no divisions which could bring up ZeroDivisionError

            interception_y = (A - x_offset) * tan_rayangle
            if int(ray_y - y_offset) == int(ray_y + interception_y):
                # Hitting vertical gridline
                interception_x = A - x_offset

                ray_x += interception_x
                ray_y += interception_y
                map_y = int(ray_y)
                map_x = int(ray_x) + (A - 1)
                side = 1

            else:
                # Hitting horizontal gridline
                interception_x = (B - y_offset) / tan_rayangle
                interception_y = B - y_offset

                ray_x += interception_x
                ray_y += interception_y
                map_y = int(ray_y) + (B - 1)
                map_x = int(ray_x)
                side = 0

            grid_value = TILEMAP[map_y][map_x]

            if grid_value != 0:  # If anything other than 0 ; If hitting a wall/something
                delta_x = ray_x - PLAYER.x
                delta_y = ray_y - PLAYER.y

                # Perpendicular distance needed to avoid fisheye
                perpendicular_distance = delta_x * viewangle_dir_x + delta_y * viewangle_dir_y

                wall_texture = TILEMAP_TEXTURES[grid_value][side]
                if side == 0:
                    offset = ray_x - int(ray_x)
                else:
                    offset = ray_y - int(ray_y)

                # Column that the draw_walls() is going to take from the texture
                column = int(TEXTURE_SIZE * offset)

                WALL_DATA.append((perpendicular_distance, wall_texture, column))

                break


def draw_walls():
    constant = 0.6 * D_H
    wall_width = int(D_W / RAYS_AMOUNT)

    for i, wall in enumerate(WALL_DATA):
        # Naming the values stored in element
        perp_dist = wall[0]
        texture = wall[1]
        column = wall[2]
        wall_height = int(constant / perp_dist)

        # Getting the part of texture that's going to be scaled and blitted
        image = texture.subsurface(column, 0, 1, TEXTURE_SIZE)

        # For optimization, walls that are bigger than D_H are going to be cropped
        # Without it, framerates drop drastically when staring into a wall
        if wall_height > D_H:
            # Complicated system that will crop the image and then adjust wall_height accordingly
            # Cropping before scaling bc it removes the need to scale to enormous sizes

            # Percentage of image that's going to be seen
            percentage = D_H / wall_height

            # What would be the perfect cropping size
            perfect_size = TEXTURE_SIZE * percentage

            # Actual (cropping) size needs to be the closest even number rounding up perfect_size
            # For example 10.23 will be turned to 12 and 11.78 will also be turned to 12
            actual_size = ceil(perfect_size)
            if actual_size % 2 != 0:  # If odd
                actual_size += 1  # Make it even

            image = image.subsurface(0, (TEXTURE_SIZE - actual_size) / 2, 1, actual_size)

            # Adjusting wall_height so it later blits it in the right position
            multiplier = actual_size / perfect_size
            wall_height = int(D_H * multiplier)

        image = pygame.transform.scale(image, (wall_width, wall_height))
        image_pos = (i * wall_width, (D_H - wall_height) / 2)

        DISPLAY.blit(image, image_pos)


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

        # Normalized vector
        normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list with one element
        movement_x = normalized_vector[0] * PLAYER.speed
        movement_y = normalized_vector[1] * PLAYER.speed

        PLAYER.move(movement_x, movement_y)


def events():
    global RUNNING
    global INFO_LAYER

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                RUNNING = False

            if event.key == K_F1:
                INFO_LAYER = not INFO_LAYER


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

        DISPLAY.blit(FPS_image, (4, 0))
        DISPLAY.blit(player_x_image, (4, 20))
        DISPLAY.blit(player_y_image, (4, 40))
        DISPLAY.blit(viewangle_image, (4, 60))


def game_loop():
    get_rayangles()
    load_textures()
    read_tilemap()

    global PLAYER
    PLAYER = Player(2.5, 29.5, 0)  # Creates player

    global RUNNING
    RUNNING = True

    while RUNNING:
        events()
        mouse()
        movement()

        bottom_layer()
        raycast()
        draw_walls()
        top_layer()

        pygame.display.flip()
        CLOCK.tick(30)

    pygame.quit()

game_loop()
