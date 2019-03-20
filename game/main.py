# TO DO:
# Level end system
# Weapon items
# Enemies dropping ammo

# NOTES:
# Game's tick rate is capped at 30
# All angles are in radians
# DOORS list contains all doors currently visible or in motion
# Objects are in OBJECTS list only if that object's cell is visible to player
# Enemies are in ENEMIES list at all time time but are drawn only if their perp_dist is > 0
# Wall texture files require two textures side by side (even if they are going to be the same),
# bc raycast() is going to pick one based on the side of the interception
# All timed events are tick based,
# meaning that changing fps will change timer time


class Player:
    max_ammo = 150
    max_hp = 100

    speed = 0.15  # Must be < half_hitbox, otherwise collisions will not work
    half_hitbox = 0.2

    def __init__(self, pos, angle):
        self.x, self.y = pos
        self.viewangle = angle + 0.0000001

        self.hp = 100
        self.ammo = 0
        self.weapon_nr = 2

    def death(self, enemy):
        delta_x = enemy.x - self.x
        delta_y = enemy.y - self.y
        angle_to_enemy = atan2(delta_y, delta_x)

        difference = (angle_to_enemy + pi) - (self.viewangle + pi)
        if difference < 0:
            difference += 2 * pi
        if difference < pi:
            turn_radians = 0.05
        else:
            turn_radians = -0.05

        ratio = D_H / D_W
        o_color = (255, 26, 26)  # Outline color
        o_size = 0  # Outline thickness/size
        done = False
        while not done:
            # Update enemies
            for e in ENEMIES:
                delta_x = e.x - self.x
                delta_y = e.y - self.y
                angle_from_player = atan2(delta_y, delta_x)
                e.update_perp_dist(delta_x, delta_y, angle_from_player)

            draw_background()
            send_rays()
            draw_frame()

            if abs(self.viewangle - angle_to_enemy) > 0.05:
                self.viewangle = fixed_angle(self.viewangle + turn_radians)
                if abs(self.viewangle - angle_to_enemy) < 0.05:
                    self.viewangle = angle_to_enemy
                self.dir_x = cos(self.viewangle)
                self.dir_y = sin(self.viewangle)
            elif o_size < H_W:
                o_size += 10
                # Sides
                pygame.draw.rect(DISPLAY, o_color, (0, 0, o_size, D_H))
                pygame.draw.rect(DISPLAY, o_color, (D_W - o_size, 0, o_size, D_H))
                # Top/bottom
                pygame.draw.rect(DISPLAY, o_color, (o_size, 0, D_W - 2 * o_size, int(o_size * ratio)))
                pygame.draw.rect(DISPLAY, o_color, (o_size, D_H - int(o_size * ratio),
                                                    D_W - 2 * o_size, int(o_size * ratio)))
            else:
                done = True

            pygame.display.flip()
            CLOCK.tick(30)

        load_level(LEVEL_NR)  # Restarts level

    def hitscan(self, weapon):
        # An instant shot detection system
        # Applies to everything but projectile weapons

        # Find all shootable enemies in ENEMIES list
        shootable_enemies = []
        for e in ENEMIES:
            # If enemy not dead and player can see him
            if not e.dead and can_see((PLAYER.x, PLAYER.y), (e.x, e.y), PLAYER.viewangle, FOV):
                shootable_enemies.append(e)
        shootable_enemies.sort(key=lambda x: x.dist_squared)  # Makes hit register for closest enemy

        for e in shootable_enemies:
            enemy_center_display_x = e.display_x + (e.width / 2)
            x_offset = abs(H_W - enemy_center_display_x)
            hittable_offset = e.hittable_amount / 2 * e.width
            if hittable_offset > x_offset:  # If theoretical crosshair more or less on enemy
                if not weapon.melee:
                    e.hurt()
                elif e.dist_squared <= weapon.hit_radius**2:
                    e.hurt(weapon.damage)
                break

    def reload(self, weapon):
        ammo_needed = weapon.mag_size - weapon.mag_ammo

        if not weapon.ammo_unlimited:
            if ammo_needed > self.ammo:
                ammo_needed = self.ammo
            self.ammo -= ammo_needed

        weapon.mag_ammo += ammo_needed

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def handle_movement(self):
        # Checks for movement (WASD)
        keys_pressed = pygame.key.get_pressed()
        self.moving = False
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)

        # Vector based movement, bc otherwise player could move faster diagonally
        if keys_pressed[K_w] or keys_pressed[K_a] or keys_pressed[K_s] or keys_pressed[K_d]:
            movement_x = 0
            movement_y = 0
            if keys_pressed[K_w]:
                movement_x += self.dir_x
                movement_y += self.dir_y

            if keys_pressed[K_a]:
                movement_x += self.dir_y
                movement_y += -self.dir_x

            if keys_pressed[K_s]:
                movement_x += -self.dir_x
                movement_y += -self.dir_y

            if keys_pressed[K_d]:
                movement_x += -self.dir_y
                movement_y += self.dir_x

            movement_vector = numpy.asarray([[movement_x, movement_y]])  # Needed for normalize() function
            if abs(movement_vector[0][0]) + abs(movement_vector[0][1]) > 0.1:
                self.moving = True
                normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list

                PLAYER.move(normalized_vector[0] * Player.speed,
                            normalized_vector[1] * Player.speed)

    def move(self, x_move, y_move):
        def one_point_collision(y, x):
            if int(x - x_move) == x - x_move:
                return True, False
            if int(y - y_move) == y - y_move:
                return False, True

            x_offset = x - int(x)
            y_offset = y - int(y)

            # Distance to closest round(x/y)
            delta_x = abs(round(x_offset) - x_offset)
            delta_y = abs(round(y_offset) - y_offset)
            if delta_x < delta_y:
                return True, False
            else:
                return False, True

        # Start off by moving player position
        self.x += x_move
        self.y += y_move

        # Hitbox sides
        right = self.x + Player.half_hitbox
        left = self.x - Player.half_hitbox
        down = self.y + Player.half_hitbox
        up = self.y - Player.half_hitbox

        # Hitbox corners
        # Everything that player can walk on is less than 0 on tilemap
        # So these will be True if there is a collision
        down_right = TILEMAP[int(down)][int(right)] > 0
        down_left = TILEMAP[int(down)][int(left)] > 0
        up_right = TILEMAP[int(up)][int(right)] > 0
        up_left = TILEMAP[int(up)][int(left)] > 0

        # Find the collision type
        x_collision = False
        y_collision = False

        if down_right:
            if up_left:
                x_collision = True
                y_collision = True
            elif down_left:
                y_collision = True
                if up_right:
                    x_collision = True
            elif up_right:
                x_collision = True
            else:
                x_collision, y_collision = one_point_collision(down, right)

        elif up_left:
            if down_left:
                x_collision = True
                if up_right:
                    y_collision = True
            elif up_right:
                y_collision = True
            else:
                x_collision, y_collision = one_point_collision(up, left)

        elif down_left:
            if up_right:
                x_collision = True
                y_collision = True
            else:
                x_collision, y_collision = one_point_collision(down, left)

        elif up_right:
            x_collision, y_collision = one_point_collision(up, right)

        # Apply changes to x/y if there was a collision
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
    speed = 0.05
    open_ticks = 60

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.value = tile_value

        self.ticks = 0
        self.opened_state = 0  # 1 is fully opened, 0 is fully closed
        self.state = 0

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

            elif self.state == 2:  # Staying open
                self.ticks += 1
                if self.ticks >= Door.open_ticks:  # If time for door to close
                    # Checking if player is not in door's way
                    safe_dist = 0.5 + Player.half_hitbox
                    if abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist:
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.ticks = 0
                        self.state += 1

            elif self.state == 3:  # Closing
                self.opened_state -= Door.speed
                if self.opened_state < 0:
                    self.opened_state = 0
                    self.state = 0


class WeaponModel:
    switch_ticks = 20
    w = h = 512

    def __init__(self):
        self.shooting = False
        self.reloading = False
        self.switching = 0

        self.ticks = 0
        self.column = 0
        self.draw_y = 0  # y drawing offset

        self.update()

    def shoot(self, weapon):
        # Shooting animation system
        self.ticks += 1
        if self.ticks == weapon.fire_delay / weapon.animation_frames:
            self.ticks = 0

            self.column += 1

            if self.column > weapon.animation_frames:  # If finished shot animation
                # If weapon automatic, has magazine ammo and mouse down
                if weapon.automatic and weapon.mag_ammo and pygame.mouse.get_pressed()[0]:
                    self.column = 1  # Keep going
                else:
                    self.column = 0  # Ends animation
                    self.shooting = False
                    if weapon.auto_reload:
                        self.reloading = True

            if self.column == weapon.shot_column:
                # Sending out a shot
                if not weapon.melee:
                    weapon.mag_ammo -= 1
                if not weapon.projectile:
                    PLAYER.hitscan(weapon)
                else:
                    p = Projectile((PLAYER.x, PLAYER.y), PLAYER.viewangle, weapon.projectile)
                    PROJECTILES.append(p)

    def reload(self, weapon):
        self.ticks += 1
        if self.ticks <= weapon.reload_time / 2:
            self.draw_y += 20
        elif self.ticks <= weapon.reload_time:
            self.draw_y -= 20
        else:
            self.ticks = 0
            self.reloading = False
            PLAYER.reload(weapon)

    def switch_weapons(self):
        self.ticks += 1
        if self.ticks == WeaponModel.switch_ticks / 2:
            PLAYER.weapon_nr = self.switching  # Switches weapon model when halfway through

        if self.ticks <= WeaponModel.switch_ticks / 2:
            self.draw_y += 40
        elif self.ticks <= WeaponModel.switch_ticks:
            self.draw_y -= 40
        else:
            self.ticks = 0
            self.switching = 0

    def update(self):
        self.weapon = WEAPONS[PLAYER.weapon_nr]

        if self.shooting:
            self.shoot(self.weapon)

        elif self.reloading:
            self.reload(self.weapon)

        elif self.switching:
            self.switch_weapons()

    def draw(self):
        weapon_image = self.weapon.weapon_sheet.subsurface(WeaponModel.w * self.column, 0, WeaponModel.w, WeaponModel.h)
        DISPLAY.blit(weapon_image, ((D_W - WeaponModel.w) / 2, D_H - WeaponModel.h + self.draw_y))


class CameraPlane:
    len = 1

    def __init__(self, rays_amount, fov):
        # Creates a list of rayangle offsets which will be added to player's viewangle to send rays every frame
        # Bc these angle offsets do not change during the game, they are calculated before the game loop starts
        #
        # These offsets are calculated,
        # so that later each casted ray will be equal distance away from other rays on the theoretical camera plane
        # Else the player will see things with a weird fisheye effect
        #
        # Note that in 2D rendering, camera plane is actually a single line, rather than a plane
        # Also fov has to be < pi (and not <= pi) for it to work properly

        self.rayangle_offsets = []

        camera_plane_start = -CameraPlane.len / 2
        camera_plane_step = CameraPlane.len / rays_amount

        self.dist = (CameraPlane.len / 2) / tan(fov / 2)
        for i in range(rays_amount):
            camera_plane_pos = camera_plane_start + i * camera_plane_step

            angle = atan2(camera_plane_pos, self.dist)
            self.rayangle_offsets.append(angle)


class Drawable:
    def adjust_image_height(self):
        # Depending on self.height, (it being the unoptimized image drawing height) this system will crop out
        # as many pixel rows from top and bottom from the unscaled image as possible,
        # while ensuring that the player will not notice a difference, when the image is drawn later
        #
        # It will then also adjust drawing height accordingly
        #
        # Cropping is done before scaling to ensure that the program is not going to be scaling images to enormous sizes

        percentage = D_H / self.height  # Percentage of image that's going to be seen
        perfect_size = TEXTURE_SIZE * percentage  # What would be the perfect cropping size

        # However actual cropping size needs to be the closest even* number rounding up perfect_size
        # For example 10.23 will be turned to 12 and 11.78 will also be turned to 12
        # *number needs to be even bc you can't crop at halfpixel
        cropping_size = ceil(perfect_size / 2) * 2

        # Cropping the image smaller - width stays the same
        rect = pygame.Rect((0, (TEXTURE_SIZE - cropping_size) / 2), (self.image.get_width(), cropping_size))
        self.image = self.image.subsurface(rect)

        # Adjusting image height accordingly
        multiplier = cropping_size / perfect_size
        self.height = int(D_H * multiplier)


class Wall(Drawable):
    def __init__(self, perp_dist, texture, column, count):
        self.perp_dist = perp_dist  # Needs saving to sort by it later
        self.image = texture.subsurface(column, 0, 1, TEXTURE_SIZE)  # Cropping 1 pixel wide column out of texture

        self.height = int(Drawable.constant / self.perp_dist)
        if self.height > D_H:
            self.adjust_image_height()

        self.display_x = count * Wall.width
        self.display_y = (D_H - self.height) / 2
        self.image = pygame.transform.scale(self.image, (Wall.width, self.height))

    def draw(self):
        DISPLAY.blit(self.image, (self.display_x, self.display_y))


class Sprite:
    animation_ticks = 5  # Sprite animation frames delay

    def draw(self):
        # Optimized sprite drawing function made for Enemies and Objects

        if self.perp_dist > 0:
            column_width = self.width / TEXTURE_SIZE
            column_left_side = self.display_x
            column_right_side = self.display_x + column_width

            for column in range(TEXTURE_SIZE):
                column_left_side += column_width
                column_right_side += column_width

                if column_left_side < D_W and column_right_side > 0:  # If row on screen
                    try:
                        # Getting sprite column out of image
                        sprite_column = self.image.subsurface(column, 0, 1, self.image.get_height())
                        # Scaling that column
                        sprite_column = pygame.transform.scale(sprite_column, (ceil(column_width), self.height))
                        # Blitting that column
                        DISPLAY.blit(sprite_column, (column_left_side, self.display_y))

                    except pygame.error:  # If size too big (happens rarely and only if player too close to sprite)
                        break  # End drawing sprite

    def calc_display_xy(self, angle_from_player, y_multiplier=1.0):
        # In order to calculate sprite's correct display x/y position, we need to calculate it's camera plane position
        camera_plane_pos = CAMERA_PLANE.len / 2 + tan(angle_from_player - PLAYER.viewangle) * CAMERA_PLANE.dist

        self.display_x = D_W * camera_plane_pos - self.width / 2
        self.display_y = (D_H - self.height * y_multiplier) / 2


class Object(Drawable, Sprite):
    def __init__(self, map_pos, tilevalue):
        self.x = map_pos[0] + 0.5
        self.y = map_pos[1] + 0.5

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

        if self.perp_dist > 0:
            self.image = TILE_VALUES_INFO[tilevalue].texture

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            angle_from_player = atan2(delta_y, delta_x)
            self.calc_display_xy(angle_from_player)

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)


class Projectile(Drawable, Sprite):
    def __init__(self, pos, angle, projectile):
        # projectile is a Projectile object made in graphics.py get_weapons()
        self.sheet = projectile.sheet
        self.columns = projectile.columns
        self.column = random.randint(0, self.columns - 1)
        self.row = 0
        self.y_multiplier = projectile.y_multiplier  # Makes projectile draw at gun level

        self.angle = angle
        self.speed = projectile.speed
        self.x_step = cos(self.angle) * self.speed
        self.y_step = sin(self.angle) * self.speed
        self.x, self.y = self.came_from = pos

        self.ticks = 0
        self.to_delete = False
        self.hit = False
        self.hit_radius = projectile.hit_radius
        self.damage = projectile.damage
        self.exploding = projectile.exploding

        self.update()  # One update is needed to get self.perp_dist
        self.update()  # Second is to avoid drawing projectile too close to player

    def wall_collision(self):
        # If no collision, returns False
        # Else returns True and sets x/y to contact point

        tile_value = TILEMAP[int(self.y)][int(self.x)]
        if tile_value != 0:
            tile_id = TILE_VALUES_INFO[tile_value].type
            if tile_id == 'Wall':
                # Cancel step
                self.x -= self.x_step
                self.y -= self.y_step
                # Get the exact contact point
                self.x, self.y = simple_raycast(self.angle, (self.x, self.y))
                return True
            elif tile_id == 'Door':
                max_travel_point = simple_raycast(self.angle, self.came_from)
                max_travel_dist_squared = (self.came_from[0] - max_travel_point[0])**2 + \
                                          (self.came_from[1] - max_travel_point[1])**2
                projectile_dist_squared = (self.came_from[0] - self.x)**2 + (self.came_from[1] - self.y)**2
                if max_travel_dist_squared < projectile_dist_squared:
                    # Get the exact contact point
                    self.x, self.y = max_travel_point
                    return True
        return False

    def update(self):
        if not self.hit:
            self.x += self.x_step
            self.y += self.y_step

            # Check for collision
            for e in ENEMIES:
                if not e.dead:
                    squared_dist = (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                    if squared_dist < self.hit_radius ** 2:
                        self.hit = True
                        if not self.exploding:
                            e.hurt(self.damage)
                        break
            else:
                if self.wall_collision():
                    self.hit = True

            if self.hit:
                # Trace back position a little bit
                self.x -= self.x_step * 0.3
                self.y -= self.y_step * 0.3
                self.column = 0
                self.row = 1
                self.ticks = 0
                if self.exploding:
                    for e in ENEMIES:
                        if not e.dead:
                            squared_dist = (self.x - e.x)**2 + (self.y - e.y)**2
                            if squared_dist < 1:  # If enemy in 1 unit distance
                                e.hurt(self.damage)
                self.update()

        self.ticks += 1
        if self.ticks == Sprite.animation_ticks:
            self.ticks = 0
            self.column += 1
            if self.column >= self.columns:
                self.column = 0
                if self.hit:
                    self.to_delete = True

        # Update image for drawing
        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        angle_from_player = atan2(delta_y, delta_x)

        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
        if self.perp_dist > 0:
            self.image = self.sheet.subsurface(self.column * TEXTURE_SIZE, self.row * TEXTURE_SIZE,
                                               TEXTURE_SIZE, TEXTURE_SIZE)

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            #if self.height > D_H:
            #    self.adjust_image_height()
            # Not adjusting image height bc it will not work properly with y_multiplier

            self.calc_display_xy(angle_from_player, self.y_multiplier)


class Enemy(Drawable, Sprite):
    turning_speed = 0.08  # Stationary enemy turning speed in radians per tick

    def __init__(self, spritesheet, pos):
        self.x, self.y = self.home = pos
        self.angle = 0  # Enemy actual facing angle
        self.wanted_angle = 0  # Angle to which enemy is turning

        self.sheet = spritesheet
        self.row = 0  # Spritesheet row
        self.column = 0  # Spritesheet column

        self.path = []
        self.alerted = False
        self.shooting = False
        self.dead = False
        self.hit = False

        # Take attributes from ENEMY_INFO based on spritesheet (enemy type)
        # What each attribute means see graphics.py get_enemy_info() enemy_info dictionary description
        self.name, self.hp, self.speed, self.shooting_range, self.accuracy, self.instant_alert_dist,\
        self.memory, self.patience, self.hittable_amount = ENEMY_INFO[self.sheet]

        # Timed events tick variables (frames passed since some action)
        self.anim_ticks = 0
        self.last_hit_anim_ticks = Sprite.animation_ticks
        self.last_saw_ticks = self.memory
        self.stationary_ticks = 0

    def get_look_angles(self):
        # Creates a list of angles that are going to be chosen by random when stationary every once in a while
        # Angles which enemy can further are chosen more often
        self.look_angles = []
        rayangles = [x/10*pi for x in range(10, -10, -1)]  # 20 different viewangles should be enough
        for rayangle in rayangles:

            ray_x, ray_y = simple_raycast(rayangle, (self.x, self.y))
            ray_dist = sqrt((ray_x - self.x)**2 + (ray_y - self.y)**2)

            for _ in range(int(ray_dist)):
                self.look_angles.append(rayangle)

    def get_home_room(self):
        # Makes a self.home_room list which contains all the map points in his room

        def get_unvisited(pos):
            # Gets new unvisited points
            all_points = visited + unvisited
            for x in (-1, 0, 1):  # -1, 0, 1
                for y in (-1, 0, 1):  # -1, 0, 1
                    pos_x, pos_y = (pos[0] + x, pos[1] + y)
                    if (pos_x, pos_y) not in all_points and TILEMAP[pos_y][pos_x] <= 0:
                        unvisited.append((pos_x, pos_y))

        visited = [(int(self.x), int(self.y))]
        unvisited = []
        get_unvisited((int(self.x), int(self.y)))

        while unvisited:  # While there is unscanned/unvisited points
            current = unvisited[0]  # Get new point
            del unvisited[0]  # Delete it from unvisited bc it's about to get visited
            visited.append(current)  # Add point to visited
            get_unvisited(current)  # Scan new points from that location

        self.home_room = visited

    def hurt(self, damage=1):
        self.hp -= damage
        self.shooting = False
        if self.hp <= 0:
            self.hit = True
            self.row = 5  # Choose death/hurt animation row
            self.anim_ticks = 0
            self.dead = True
            self.column = 0  # Choose first death animation frame
        elif self.last_hit_anim_ticks >= Sprite.animation_ticks:  # If enough time passed to show new hit animation
            self.hit = True
            self.row = 5
            self.anim_ticks = 0
            self.last_hit_anim_ticks = 0

    def shoot(self):
        # Player shot hit and damage logic / enemy hitscan
        # https://wolfenstein.fandom.com/wiki/Damage

        dist = sqrt(self.dist_squared)
        if PLAYER.moving:
            speed = 160
        else:
            speed = 256
        if can_see((PLAYER.x, PLAYER.y), (self.x, self.y), PLAYER.viewangle, FOV):
            look = 16
        else:
            look = 8
        rand = random.randint(0, 255)

        player_hit = rand < speed - dist * self.accuracy * look
        if player_hit:
            rand = random.randint(0, 255)
            if dist < 2:
                damage = rand / 4
            elif dist > 4:
                damage = rand / 16
            else:
                damage = rand / 8
            PLAYER.hp -= int(damage)
            if PLAYER.hp <= 0:
                PLAYER.death(self)

    def ready_to_shoot(self):
        return self.alerted and \
               self.dist_squared < self.shooting_range**2 and \
               can_see((self.x, self.y), (PLAYER.x, PLAYER.y))

    def could_see_alerted_enemies(self):
        # NOTE: Other alerted enemies don't have to be in enemy's fov
        for e in ENEMIES:
            if e.alerted and self.home != e.home:
                if can_see((self.x, self.y), (e.x, e.y)):
                    return True
        return False

    def strafe(self):
        # Gets new path to a random empty neighbour tile (if possible)
        available_tiles = []
        for x in (-1, 0, 1):
            for y in (-1, 0, 1):
                tile_x = int(self.x) + x
                tile_y = int(self.y) + y
                if TILEMAP[tile_y][tile_x] <= 0:  # If tile steppable
                    for e in ENEMIES:  # Check if no enemies standing there
                        if (int(e.x), int(e.y)) == (tile_x, tile_y):
                            break
                    else:
                        available_tiles.append((tile_x, tile_y))

        if available_tiles:
            self.path = pathfinding.pathfind((self.x, self.y), random.choice(available_tiles))
        else:
            self.path = []

    def turn_towards(self, angle):
        self.stationary_ticks = 0

        difference = (angle + pi) - (self.angle + pi)
        if difference < 0:
            difference += 2 * pi

        if difference < pi:
            self.angle += Enemy.turning_speed
        else:
            self.angle -= Enemy.turning_speed

        if abs(self.angle - angle) < Enemy.turning_speed:  # If self.angle close enough
            self.angle = angle  # Finish turning

    def update(self):

        # If door underneath enemy, create a door obj if it isn't there already and start opening it immediately
        tile_value = TILEMAP[int(self.y)][int(self.x)]
        if TILE_VALUES_INFO[tile_value].type == 'Door':
            for d in DOORS:
                if (d.x, d.y) == (int(self.x), int(self.y)):
                    d.state = 1
                    break
            else:
                d = Door((int(self.x), int(self.y)), tile_value)
                d.state = 1
                DOORS.append(d)

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        angle_from_player = atan2(delta_y, delta_x)
        self.dist_squared = delta_x**2 + delta_y**2

        # Make enemy shoot when he's in player's tile
        if not self.hit and (int(self.x), int(self.y)) == (int(PLAYER.x), int(PLAYER.y)):
            if random.randint(0, 10) == 0:
                self.shooting = True

        if self.shooting:
            self.row = 6
            self.anim_ticks += 1
            self.column = int(self.anim_ticks / Sprite.animation_ticks)
            if self.anim_ticks == Sprite.animation_ticks * 2:
                self.shoot()
            if self.column > 2:
                self.column = 2
                self.shooting = False

                self.anim_ticks = 0
                self.last_saw_ticks = 0
                self.stationary_ticks = 0

        elif not self.hit:
            if self.last_hit_anim_ticks != Sprite.animation_ticks:
                self.last_hit_anim_ticks += 1

            # Assume these two values (program is going to change them if needed)
            self.alerted = True
            self.wanted_angle = atan2(-delta_y, -delta_x)

            can_see_player = can_see((self.x, self.y), (PLAYER.x, PLAYER.y), self.angle, Enemy.fov)
            if can_see_player or self.could_see_alerted_enemies():
                self.last_saw_ticks = 0
            elif self.last_saw_ticks < self.memory:
                self.last_saw_ticks += 1
            elif self.dist_squared > self.instant_alert_dist**2:
                self.alerted = False
                self.wanted_angle = self.angle  # Reset wanted_angle / Don't look at player

            # Turn towards wanted angle
            if self.angle != self.wanted_angle:
                self.turn_towards(self.wanted_angle)

            if not self.path:
                # If enemy can see player:
                #   Set path to player
                # Elif enemy's been stationary for a while:
                #   Choose a new action

                self.stationary_ticks += 1
                if self.alerted:
                    self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))

                elif self.stationary_ticks > self.patience:
                    if (self.x, self.y) == self.home:
                        # If at home:
                        # Either look at semi-random angle
                        # Or go to a random location in his room
                        if random.randint(0, 1) == 0:
                            self.wanted_angle = random.choice(self.look_angles)
                        else:
                            self.path = pathfinding.pathfind((self.x, self.y), random.choice(self.home_room))
                    else:
                        self.path = pathfinding.pathfind((self.x, self.y), self.home)

            if self.path:
                # If other enemy(s) in step tile:
                #   Empty path and don't step
                # Else:
                #   Make a step

                step_x, step_y = self.path[0]
                for e in ENEMIES:
                    if not e.dead and e.home != self.home and (int(e.x), int(e.y)) == (step_x, step_y):
                        # Enemy has path but can't move --> either shoot (if possible) or move position
                        if random.randint(0, 1) == 0:
                            if self.ready_to_shoot():
                                self.shooting = True
                                self.angle = atan2(-delta_y, -delta_x)
                                self.path = []  # Need to draw enemy standing
                        else:
                            self.strafe()  # Gets new path to a random neighbour tile
                        break
                else:
                    self.stationary_ticks = 0
                    step_x += 0.5  # Centers tile pos
                    step_y += 0.5

                    self.angle = self.wanted_angle = atan2(step_y - self.y, step_x - self.x)
                    self.x += cos(self.angle) * self.speed
                    self.y += sin(self.angle) * self.speed

                    # Could recalculate delta_x/delta_y here but it makes next to no difference

                    # If enemy close enough to the path step / If enemy has finished his step
                    if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                        self.x = step_x
                        self.y = step_y
                        # If alerted, close enough to player and possible for the shot to make it
                        if self.ready_to_shoot():
                            self.shooting = True
                            self.angle = atan2(-delta_y, -delta_x)
                            self.path = []  # Needed to draw enemy standing
                        elif self.alerted:
                            self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
                        else:
                            del self.path[0]
                            if not self.path:  # If reached path end
                                self.angle = atan2(-delta_y, -delta_x)  # Face player

            # Find the right spritesheet column
            angle = fixed_angle(-angle_from_player + self.angle) + pi  # +pi to get rid of negative values
            self.column = round(angle / (pi / 4))
            if self.column == 8:
                self.column = 0

            if self.path:
                if self.row == 0 or self.row > 4:
                    self.row = 1

                # Cycle through running animations
                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks:
                    self.anim_ticks = 0
                    self.row += 1
                    if self.row == 5:
                        self.row = 1
            else:
                self.anim_ticks = 0
                self.row = 0

        else:
            if self.dead:  # If dead/dying
                if self.column < 4:  # 4 is the final death animation frame ; If death animation not completed
                    self.anim_ticks += 1
                    if self.anim_ticks == Sprite.animation_ticks:
                        self.anim_ticks = 0
                        self.column += 1
            else:  # If just hit
                self.column = 7
                self.anim_ticks += 1
                if self.anim_ticks == Sprite.animation_ticks - 2:  # - 2 makes hit animation show for less frames
                    self.hit = False

                    self.anim_ticks = 0
                    self.last_saw_ticks = 0
                    self.stationary_ticks = 0

        self.update_perp_dist(delta_x, delta_y, angle_from_player)

    def update_perp_dist(self, delta_x, delta_y, angle_from_player):
        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
        if self.perp_dist > 0:
            self.image = self.sheet.subsurface(self.column * TEXTURE_SIZE, self.row * TEXTURE_SIZE,
                                               TEXTURE_SIZE, TEXTURE_SIZE)

            self.height = self.width = int(Drawable.constant / self.perp_dist)
            if self.height > D_H:
                self.adjust_image_height()

            self.calc_display_xy(angle_from_player)


def fixed_angle(angle):
    # Function made for angles to stay between -pi and pi
    # For example 3.18 will be turned to -3.10

    if angle > pi:  # 3.14+
        angle -= 2 * pi
    elif angle < -pi:  # 3.14-
        angle += 2 * pi
    return angle


def can_see(from_, to, viewangle=0.0, fov=0.0):
    # Universal function for checking if it's possible to see one point from another in tilemap
    # Returns True if end point visible, False if not visible

    start_x, start_y = from_
    end_x, end_y = to
    angle_to_end = atan2(end_y - start_y, end_x - start_x)

    if viewangle and fov:  # If viewangle and fov given
        if abs(angle_to_end - viewangle) > fov / 2:  # If end position outside viewangle
            return False

    # Check if there is something between end and start point
    ray_x, ray_y = simple_raycast(angle_to_end, from_)
    ray_dist_squared = (start_x - ray_x) ** 2 + (start_y - ray_y) ** 2
    end_dist_squared = (start_x - end_x) ** 2 + (start_y - end_y) ** 2
    return ray_dist_squared > end_dist_squared  # Returns True if interception farther than end point


def send_rays():
    global WALLS
    WALLS = []
    global OBJECTS
    OBJECTS = []
    for c, rayangle_offset in enumerate(CAMERA_PLANE.rayangle_offsets):
        # Get the rayangle that's going to be raycasted
        rayangle = fixed_angle(PLAYER.viewangle + rayangle_offset)

        # Get values from raycast()
        tile_value, ray_x, ray_y, column = raycast(rayangle, (PLAYER.x, PLAYER.y))
        delta_x = ray_x - PLAYER.x
        delta_y = ray_y - PLAYER.y

        # Calculate perpendicular distance (needed to avoid fisheye effect)
        perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

        # Get wall texture
        for d in DOORS:
            # Ray x and y abs(distances) to door center position
            x_diff = abs(d.x + 0.5 - ray_x)
            y_diff = abs(d.y + 0.5 - ray_y)
            if (x_diff == 0.5 and y_diff <= 0.5) or (y_diff == 0.5 and x_diff <= 0.5):
                texture = DOOR_SIDE_TEXTURE
                break
        else:
            texture = TILE_VALUES_INFO[tile_value].texture

        # Create Wall object
        WALLS.append(Wall(perp_dist, texture, column, c))


def raycast(rayangle, start_pos):
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

    ray_x, ray_y = start_pos
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
        # to determine the interception type and to calculate other variables depending on that interception type
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
        if tile_value != 0:
            tile_id = TILE_VALUES_INFO[tile_value].type

            if tile_id == 'Object':
                for obj in OBJECTS:
                    if (obj.x - 0.5, obj.y - 0.5) == (map_x, map_y):
                        break
                else:
                    OBJECTS.append(Object((map_x, map_y), tile_value))
                continue

            if tile_id == 'Door':
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                # Add door to DOORS if it's not in it already
                for d in DOORS:
                    if (d.x, d.y) == (map_x, map_y):
                        door = d
                        break
                else:
                    door = Door((map_x, map_y), tile_value)
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

            else:  # If wall
                if side == 0:
                    offset = abs(ray_y - int(ray_y) - (1 - A))
                else:
                    offset = abs(ray_x - int(ray_x) - B)
                column = int(TEXTURE_SIZE * offset)

            if side == 0:
                column += TEXTURE_SIZE  # Makes block sides different

            return tile_value, ray_x, ray_y, column


def simple_raycast(rayangle, start_pos, side_needed=False):
    # Used to only get the ray interception point without creating objects that are in the way

    if abs(rayangle) > pi / 2:
        A = 0
    else:
        A = 1
    if rayangle < 0:
        B = 0
    else:
        B = 1

    ray_x, ray_y = start_pos
    tan_rayangle = tan(rayangle)

    while True:
        x_offset = ray_x - int(ray_x)
        if x_offset == A:
            x_offset = 1

        y_offset = ray_y - int(ray_y)
        if y_offset == B:
            y_offset = 1

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
        if tile_value != 0:
            tile_id = TILE_VALUES_INFO[tile_value].type

            if tile_id == 'Object':
                continue

            if tile_id == 'Door':
                # Update (x/y)_offset values
                x_offset = ray_x - int(ray_x)
                if x_offset == A:
                    x_offset = 1

                y_offset = ray_y - int(ray_y)
                if y_offset == B:
                    y_offset = 1

                for d in DOORS:
                    if (d.x, d.y) == (map_x, map_y):
                        door = d
                        break
                else:
                    # Create a closed door
                    door = Door((map_x, map_y), tile_value)

                if side == 0:  # If vertical ( | )
                    interception_y = (-0.5 + A) * tan_rayangle
                    offset = ray_y + interception_y - int(ray_y + interception_y)
                    if int(ray_y - y_offset) == int(ray_y + interception_y) and offset > door.opened_state:
                        ray_x += (-0.5 + A)
                        ray_y += interception_y
                    else:
                        continue

                else:  # If horizontal ( -- )
                    interception_x = (-0.5 + B) / tan_rayangle
                    offset = ray_x + interception_x - int(ray_x + interception_x)
                    if int(ray_x - x_offset) == int(ray_x + interception_x) and offset > door.opened_state:
                        ray_x += interception_x
                        ray_y += (-0.5 + B)
                    else:
                        continue
            if not side_needed:
                return ray_x, ray_y
            else:
                return ray_x, ray_y, side


def events():
    global QUIT
    weapon = WEAPON_MODEL.weapon

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                QUIT = True

            elif event.key == K_e:
                x = int(PLAYER.x + PLAYER.dir_x)
                y = int(PLAYER.y + PLAYER.dir_y)
                tile_value = TILEMAP[y][x]
                tile_type = TILE_VALUES_INFO[tile_value].type
                tile_desc = TILE_VALUES_INFO[tile_value].desc
                if tile_type == 'Door' and tile_desc == 'Dynamic':
                    for d in DOORS:
                        # If found the right door and it's not in motion already
                        if x == d.x and y == d.y:
                            d.state = 1
                            break
                elif tile_type == 'Wall' and tile_desc == 'End-trigger':
                    TILEMAP[y][x] += 1  # Change trigger block texture
                    #level_end()

            elif event.key == K_r and not weapon.melee:
                # If magazine not full and weapon not shooting
                if weapon.mag_ammo < weapon.mag_size and not WEAPON_MODEL.shooting and not WEAPON_MODEL.switching:
                    if weapon.ammo_unlimited:
                        WEAPON_MODEL.reloading = True
                    elif PLAYER.ammo:
                        WEAPON_MODEL.reloading = True

            elif not WEAPON_MODEL.shooting and not WEAPON_MODEL.reloading:
                key = pygame.key.name(event.key)
                numbers = (str(x) for x in range(1, 10))  # Skips 0 bc that can't be weapon slot
                if key in numbers:
                    key = int(key)
                    # If requested weapon not equipped already and key index in WEAPONS
                    if key != PLAYER.weapon_nr and key <= len(WEAPONS) - 1:
                        WEAPON_MODEL.switching = key

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not WEAPON_MODEL.reloading and not WEAPON_MODEL.switching:
                    if weapon.mag_ammo or weapon.melee:
                        WEAPON_MODEL.shooting = True

            elif not WEAPON_MODEL.shooting and not WEAPON_MODEL.reloading:
                if event.button == 4:  # Mousewheel up
                    if PLAYER.weapon_nr > 1:  # Can't go under 1
                        WEAPON_MODEL.switching = PLAYER.weapon_nr - 1
                if event.button == 5:  # Mousewheel down
                    if PLAYER.weapon_nr < len(WEAPONS) - 1:
                        WEAPON_MODEL.switching = PLAYER.weapon_nr + 1


def update_gameobjects():
    # Function made for updating game objects every frame

    for c, d in enumerate(DOORS):
        d.move()
        if d.state == 0:
            del DOORS[c]
    for c, p in enumerate(PROJECTILES):
        p.update()
        if p.to_delete:
            del PROJECTILES[c]
    for e in ENEMIES:
        e.update()
    WEAPON_MODEL.update()

    # Checking if player is standing on an object,
    # bc raycast() will miss objects player is standing on
    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:
        OBJECTS.append(Object((int(PLAYER.x), int(PLAYER.y)), tile_value))
        tile_id = TILE_VALUES_INFO[tile_value].desc

        if tile_id == 'Ammo':
            if PLAYER.ammo < PLAYER.max_ammo:
                PLAYER.ammo += 10
                if PLAYER.ammo > PLAYER.max_ammo:
                    PLAYER.ammo = PLAYER.max_ammo
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0

        elif tile_id == 'Health':
            if PLAYER.hp < PLAYER.max_hp:
                PLAYER.hp += 20
                if PLAYER.hp > PLAYER.max_hp:
                    PLAYER.hp = PLAYER.max_hp
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0


def load_level(level_nr):
    # Create tilemap
    with open('../levels/{}/tilemap.txt'.format(level_nr), 'r') as f:
        global TILEMAP
        TILEMAP = []
        for line in f:
            row = line.replace('\n', '')  # Get rid of newline (\n)
            row = row[1:-1]  # Get rid of '[' and ']'
            row = row.split(',')  # Split line into list
            row = [int(i) for i in row]  # Turn all number strings to an int
            TILEMAP.append(row)

    # Create player
    with open('../levels/{}/player.txt'.format(level_nr), 'r') as f:
        player_pos = f.readline().replace('\n', '').split(',')
        player_pos = [float(i) for i in player_pos]
        player_angle = float(f.readline().replace('\n', ''))
        global PLAYER
        PLAYER = Player(player_pos, player_angle)

    # Background
    with open('../levels/{}/background.txt'.format(level_nr), 'r') as f:
        global BACKGROUND_COLOURS
        BACKGROUND_COLOURS = []
        for _ in range(2):
            colour = f.readline().replace('\n', '').split(',')
            colour = [int(i) for i in colour]
            BACKGROUND_COLOURS.append(tuple(colour))

        global SKYTEXTURE
        SKYTEXTURE = None
        value = int(f.readline().replace('\n', ''))
        if value > 0:
            skytextures = os.listdir('../textures/skies')
            try:
                SKYTEXTURE = pygame.image.load('../textures/skies/{}'.format(skytextures[value - 1])).convert()
            except pygame.error:
                pass
            else:
                SKYTEXTURE = pygame.transform.scale(SKYTEXTURE, (D_W * 4, H_H))

    # Empty projectiles and doors
    global DOORS
    DOORS = []
    global PROJECTILES
    PROJECTILES = []

    global WEAPON_MODEL
    WEAPON_MODEL = WeaponModel()

    for w in WEAPONS[1:]:
        if not w.melee:
            w.mag_ammo = w.mag_size

    # Enemies
    global ENEMIES
    ENEMIES = []
    for row in range(len(TILEMAP)):
        for column in range(len(TILEMAP[row])):
            if TILE_VALUES_INFO[TILEMAP[row][column]].type == 'Enemy':
                spritesheet = TILE_VALUES_INFO[TILEMAP[row][column]].texture
                pos = (column + 0.5, row + 0.5)
                ENEMIES.append(Enemy(spritesheet, pos))
                TILEMAP[row][column] = 0  # Clears tile
    # Process some stuff after enemies have been cleared from tilemap
    for e in ENEMIES:
        e.get_look_angles()
        e.get_home_room()

    # Run pathfinding setup function
    pathfinding.setup(TILEMAP, TILE_VALUES_INFO)

    game_loop()


def draw_background():
    if SKYTEXTURE:
        # x_offset is a value ranging from 0 to 1
        x_offset = (PLAYER.viewangle + pi) / (2*pi)
        x = x_offset * SKYTEXTURE.get_width()

        if x_offset <= 0.75:
            # Sky texture can be drawn as one image
            sky = SKYTEXTURE.subsurface(x, 0, D_W, H_H)
            DISPLAY.blit(sky, (0, 0))
        else:
            # Sky texture needs to be drawn as two separate parts
            sky_left = SKYTEXTURE.subsurface(x, 0, SKYTEXTURE.get_width() - x, H_H)
            sky_right = SKYTEXTURE.subsurface(0, 0, D_W - sky_left.get_width(), H_H)
            DISPLAY.blit(sky_left, (0, 0))
            DISPLAY.blit(sky_right, (sky_left.get_width(), 0))
    else:
        pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[0], ((0, 0), (D_W, H_H)))  # Ceiling
    pygame.draw.rect(DISPLAY, BACKGROUND_COLOURS[1], ((0, H_H), (D_W, H_H)))  # Floor


def draw_frame():
    # Sorting objects by perp_dist so those further away are drawn first
    to_draw = WALLS + ENEMIES + OBJECTS + PROJECTILES
    to_draw.sort(key=lambda x: x.perp_dist, reverse=True)
    for obj in to_draw:
        obj.draw()


def draw_hud():
    def dynamic_colour(current, maximum):
        ratio = current / maximum  # 1 is completely green, 0 completely red
        if ratio < 0.5:
            red = 255
            green = int(ratio * 2 * 255)
        else:
            ratio = 1 - ratio
            green = 255
            red = int(ratio * 2 * 255)

        return red, green, 0

    x_safezone = 6  # In pixels

    # Simulates blinking effect
    global ALPHA
    ALPHA -= 15
    if ALPHA == -255:
        ALPHA = 255

    # FPS counter
    text_surface = GAME_FONT.render(str(round(CLOCK.get_fps())), False, (0, 255, 0))
    DISPLAY.blit(text_surface, (3, 3))

    # Weapon HUD
    WEAPON_MODEL.draw()
    current_weapon = WEAPON_MODEL.weapon

    weapon_name_surface = GAME_FONT.render(str(current_weapon.name), False, (255, 255, 255))
    if current_weapon.melee:
        weapon_ammo_surface = GAME_FONT.render('--/--', False, (0, 255, 0))
    else:
        if not WEAPON_MODEL.reloading:
            if current_weapon.ammo_unlimited:
                total_ammo = 'Unlimited'
            else:
                total_ammo = PLAYER.ammo

            weapon_ammo = '{}/{}'.format(current_weapon.mag_ammo, total_ammo)

            if current_weapon.mag_ammo:
                ALPHA = 255  # Resets blinking
                weapon_ammo_surface = GAME_FONT.render(weapon_ammo, False,
                                                       dynamic_colour(current_weapon.mag_ammo, current_weapon.mag_size))
            else:
                weapon_ammo_surface = GAME_FONT.render(weapon_ammo, False, (255, 0, 0), (0, 0, 0))  # Black background
                weapon_ammo_surface.set_colorkey((0, 0, 0))  # Tell program to treat black as transparent
                weapon_ammo_surface.set_alpha(abs(ALPHA))
        else:
            weapon_ammo_surface = GAME_FONT.render('Reloading', False, (255, 0, 0), (0, 0, 0))  # Black background
            weapon_ammo_surface.set_colorkey((0, 0, 0))  # Tell program to treat black as transparent
            weapon_ammo_surface.set_alpha(abs(ALPHA))

    DISPLAY.blit(weapon_name_surface, (D_W - weapon_name_surface.get_width() - x_safezone, D_H - 64))
    DISPLAY.blit(weapon_ammo_surface, (D_W - weapon_ammo_surface.get_width() - x_safezone, D_H - 32))

    # Player hp HUD
    hp_text_surface = GAME_FONT.render('HP:', False, (255, 255, 255))
    hp_amount_surface = GAME_FONT.render(str(PLAYER.hp), False, dynamic_colour(PLAYER.hp, 100))
    DISPLAY.blit(hp_text_surface, (x_safezone, D_H - 64))
    DISPLAY.blit(hp_amount_surface, (x_safezone, D_H - 32))


def game_loop():
    PLAYER.rotate(pygame.mouse.get_rel()[0] * SENSITIVITY)
    PLAYER.handle_movement()

    events()
    update_gameobjects()

    draw_background()
    send_rays()
    draw_frame()
    draw_hud()

    pygame.display.flip()
    CLOCK.tick(30)


if __name__ == '__main__':
    import sys
    import os

    from math import *
    import random

    import numpy
    from sklearn.preprocessing import normalize

    import pygame
    from pygame.locals import *

    import game.graphics as graphics
    import game.pathfinding as pathfinding

    # Game settings
    D_W = 800
    D_H = 600
    H_W = int(D_W / 2)  # Half width
    H_H = int(D_H / 2)  # Half height
    FOV = pi / 2  # = 90 degrees
    LEVEL_NR = 1
    RAYS_AMOUNT = H_W  # Drawing frequency across the screen / Rays casted each frame
    SENSITIVITY = 0.003  # Radians turned per every pixel the mouse has moved horizontally
    CAMERA_PLANE = CameraPlane(RAYS_AMOUNT, FOV)
    TEXTURE_SIZE = 64
    # Make class constants
    Drawable.constant = 0.6 * D_H
    Wall.width = int(D_W / RAYS_AMOUNT)
    Enemy.fov = FOV  # Enemies share the same fov as player

    # Pygame stuff
    pygame.init()
    pygame.display.set_caption('Raycaster')
    DISPLAY = pygame.display.set_mode((D_W, D_H))
    CLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    GAME_FONT = pygame.font.Font('../font/LCD_Solid.ttf', 32)
    ALPHA = 255  # Text transparency value used to create blinking texts in draw_hud()

    DOOR_SIDE_TEXTURE = graphics.get_door_side_texture(sys, pygame)
    ENEMY_INFO = graphics.get_enemy_info(sys, pygame)
    TILE_VALUES_INFO = graphics.get_tile_values_info(sys, pygame, TEXTURE_SIZE, ENEMY_INFO)
    WEAPONS = graphics.get_weapons(sys, pygame)

    load_level(LEVEL_NR)
    QUIT = False
    while not QUIT:
        game_loop()
    pygame.quit()
