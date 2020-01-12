# TO DO:
# Create levels
# Level number hud
# Add weapon speed penalties
# Add more enemy spritesheet visual descriptions like amount of shot columns and so
# Move leveleditor textures to texture folder
# Draw only non-transparent parts of sprites somehow - maybe some lookout table that tells non-transparent rect

# NOTES:
# Game's tick rate is at 30
# Due to poor optimization, big open areas will drop fps
# All timed events are tick based
# All angles are in radians
# Enemies can travel through Dynamic and Locked doors, but not Static or Boss doors
# Killing a boss gives the player a key
# There is no support for multiple bosses in one level

# Sound Channels:
# 0 = door and pickup sounds
# 1 = player's weapon sounds
# 2 - 6 = normal enemy sounds
# 7 = boss sounds


class Player:
    max_hp = 100
    speed = 0.15  # Must be < half_hitbox, otherwise player can clip through walls
    half_hitbox = 0.2

    def __init__(self):
        self.weapon_nr = 1
        self.saved_weapon_loadout = [1]

    def setup(self, pos, angle):
        self.x = pos[0]
        self.y = pos[1]
        self.viewangle = angle
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)
        self.hp = Player.max_hp
        self.has_key = False

        self.weapon_loadout = self.saved_weapon_loadout[:]
        if self.weapon_nr not in self.weapon_loadout:
            self.weapon_nr = 1

    def save_weapon_loadout(self):
        self.saved_weapon_loadout = self.weapon_loadout

    def hurt(self, damage, enemy):
        EFFECTS.update((255, 0, 0))
        self.hp -= damage
        if self.hp <= 0:
            #last_chance_hp = random.randint(1, 10)
            #if self.hp + damage > last_chance_hp:
            #    self.hp = last_chance_hp
            #else:
            for channel_id in range(8):
                pygame.mixer.Channel(channel_id).fadeout(150)
            LEVEL.restart(enemy)

    def rotate(self, radians):
        self.viewangle = fixed_angle(self.viewangle + radians)

    def handle_movement(self):  # OPTIMIZE
        # Checks for movement (WASD)
        keys_pressed = pygame.key.get_pressed()
        self.dir_x = cos(self.viewangle)
        self.dir_y = sin(self.viewangle)
        old_pos = (self.x, self.y)

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
                normalized_vector = normalize(movement_vector)[0]  # [0] because vector is inside of list

                PLAYER.move(normalized_vector[0] * Player.speed,
                            normalized_vector[1] * Player.speed)
        self.total_movement = sqrt(squared_dist(old_pos, (self.x, self.y)))

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
    type = 'Normal'
    locked = False  # Only needed to avoid AttributeError
    speed = 0.065
    open_ticks = 90

    def __init__(self, map_pos, tile_value):
        self.x, self.y = map_pos
        self.value = tile_value

        self.ticks = 0
        self.closed_state = 1  # 1 is fully closed, 0 is fully opened
        self.state = 0

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def play_sound(self, sound):
        volume = (1 - sqrt(squared_dist((PLAYER.x, PLAYER.y), (self.x + 0.5, self.y + 0.5))) / 32) ** 2
        if volume > 0:
            sound.set_volume(volume)
            sound.play()

    def move(self):
        if self.state > 0:
            if self.state == 1:  # Opening
                if self.closed_state == 1:
                    self.play_sound(self.open_sound)
                self.closed_state -= Door.speed
                if self.closed_state <= 0:
                    TILEMAP[self.y][self.x] = 0  # Make tile walkable
                    self.closed_state = 0
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
                if self.closed_state == 0:
                    self.play_sound(self.close_sound)
                self.closed_state += Door.speed
                if self.closed_state >= 1:
                    self.closed_state = 1
                    self.state = 0


class BossDoor(Door):
    # Boss door is a one way door that stays unlocked until both of the door sides have been visited
    # This makes sure that once you've gone to the other side of the door there's no going back
    # Going through the door also automatically "wakes up" the boss in the level if there is one
    type = 'Boss'

    def __init__(self, map_pos, tile_value):
        super().__init__(map_pos, tile_value)

        self.locked = False
        if TILEMAP[self.y][self.x + 1] <= 0:
            self.door_fronts = [(self.x + 1.5, self.y + 0.5), (self.x - 0.5, self.y + 0.5)]
        else:
            self.door_fronts = [(self.x + 0.5, self.y + 1.5), (self.x + 0.5, self.y - 0.5)]

    def move(self):
        if self.state > 0:
            if self.state == 1 and not self.locked:  # Opening
                if self.closed_state == 1:
                    self.play_sound(self.open_sound)
                    if len(self.door_fronts) == 2:
                        player_pos = (PLAYER.x, PLAYER.y)
                        if squared_dist(player_pos, self.door_fronts[0]) < squared_dist(player_pos, self.door_fronts[1]):
                            del self.door_fronts[0]
                        else:
                            del self.door_fronts[1]
                self.closed_state -= Door.speed
                if self.closed_state <= 0:
                    TILEMAP[self.y][self.x] = 0  # Make tile walkable
                    self.closed_state = 0
                    self.state += 1

            elif self.state == 2:  # Staying open
                self.ticks += 1
                safe_dist = 0.5 + Player.half_hitbox
                if abs(self.x + 0.5 - PLAYER.x) > safe_dist or abs(self.y + 0.5 - PLAYER.y) > safe_dist:
                    player_pos = (PLAYER.x, PLAYER.y)
                    if squared_dist(player_pos, self.door_fronts[0]) < 1:
                        # "Spawn boss"
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.locked = True
                        self.state += 1
                        for e in ENEMIES:
                            if e.type == 'Boss':
                                BOSSHEALTHBAR.start_showing(e)
                                e.status = 'default'
                                e.chasing = True
                                break

                    elif self.ticks >= Door.open_ticks:
                        TILEMAP[self.y][self.x] = self.value  # Make tile non-walkable
                        self.ticks = 0
                        self.state += 1

            elif self.state == 3:  # Closing
                if self.closed_state == 0:
                    self.play_sound(self.close_sound)
                self.closed_state += Door.speed
                if self.closed_state >= 1:
                    self.closed_state = 1
                    self.state = 0


class WeaponModel:
    switch_ticks = 6

    def __init__(self):
        self.sound_channel = pygame.mixer.Channel(1)
        self.shooting = False
        self.switching = False

        self.ticks = 0
        self.column = 0
        self.display_y = 0
        self.update()

    def shoot(self, weapon):
        def get_shootable_enemies():
            # Moving weapon x and y behind the player so enemies up close will be harder to miss
            weapon_x = PLAYER.x - PLAYER.dir_x * 0.2
            weapon_y = PLAYER.y - PLAYER.dir_y * 0.2
            shootable_enemies = []
            for e in ENEMIES:
                if e.needs_to_be_drawn and not e.status == 'dead':
                    angle = fixed_angle(e.angle_from_player + pi / 2)
                    if e.type == 'Normal':
                        dir_x = cos(angle) / 4
                        dir_y = sin(angle) / 4
                    else:
                        dir_x = cos(angle) / 2
                        dir_y = sin(angle) / 2
                    enemy_left_side = (e.x - dir_x, e.y - dir_y)
                    enemy_right_side = (e.x + dir_x, e.y + dir_y)
                    enemy_center = (e.x, e.y)
                    hittable_amount = 0
                    if can_see((weapon_x, weapon_y), enemy_left_side, PLAYER.viewangle, FOV):
                        hittable_amount += 0.25
                    if can_see((weapon_x, weapon_y), enemy_right_side, PLAYER.viewangle, FOV):
                        hittable_amount += 0.25
                    if can_see((weapon_x, weapon_y), enemy_center, PLAYER.viewangle, FOV):
                        hittable_amount += 0.5
                    if hittable_amount:
                        shootable_enemies.append((e, hittable_amount))
            shootable_enemies.sort(key=lambda x: x[0].dist_squared)  # Sort for closest dist first
            return shootable_enemies

        def bullet_hitscan(shootable_enemies, x_spread, max_range=False):
            # Each bullet can hit maximum 3 enemies
            damage_multiplier = 1
            for e, hittable_amount in shootable_enemies:
                shot_x_offset = abs(H_W - e.display_pos) + x_spread
                hittable_offset = e.width / 2 * hittable_amount
                if shot_x_offset < hittable_offset:  # If bullet more or less on enemy
                    if not max_range or e.dist_squared <= max_range ** 2:
                        if not e.status == 'dead':
                            pain = weapon.pain_chance * e.pain_chance > random.random()
                            e.hurt(weapon.damage * damage_multiplier, pain)
                        if damage_multiplier == 0.25:
                            break
                        else:
                            damage_multiplier /= 2
                    else:
                        break

        # Shooting animation system
        self.ticks += 1
        if self.ticks == int(weapon.fire_delay / weapon.animation_frames):
            self.ticks = 0
            self.column += 1

            if self.column > weapon.animation_frames:  # If finished shot animation
                # If weapon automatic and mouse down
                if weapon.automatic and pygame.mouse.get_pressed()[0]:
                    self.column = 1  # Keep going
                else:
                    self.column = 0  # Ends animation
                    self.shooting = False

            if self.column == weapon.shot_column:
                shootable_enemies = get_shootable_enemies()

                if weapon.type == 'Melee':
                    bullet_hitscan(shootable_enemies, 0, weapon.range)

                elif weapon.type == 'Hitscan':
                    bullet_hitscan(shootable_enemies, random.randint(-weapon.max_x_spread, weapon.max_x_spread))

                elif weapon.type == 'Shotgun':
                    x_spread_difference = (weapon.max_x_spread * 2) / (weapon.shot_bullets - 1)
                    for i in range(weapon.shot_bullets):
                        bullet_hitscan(shootable_enemies, -weapon.max_x_spread + round(i * x_spread_difference))

                self.sound_channel.play(self.weapon.sounds.fire)

    def switch_weapons(self):
        self.ticks += 1
        if self.ticks == WeaponModel.switch_ticks / 2:
            PLAYER.weapon_nr = self.switching  # Switches weapon model when halfway through
            self.sound_channel.stop()

        if self.ticks <= WeaponModel.switch_ticks / 2:
            self.display_y += int(WeaponModel.size / WeaponModel.switch_ticks)
        elif self.ticks <= WeaponModel.switch_ticks:
            self.display_y -= int(WeaponModel.size / WeaponModel.switch_ticks)
        else:
            self.ticks = 0
            self.switching = False

    def update(self):
        self.weapon = WEAPONS[PLAYER.weapon_nr]

        if self.weapon.sounds.idle:
           if not self.shooting:
                if self.sound_channel.get_sound() == self.weapon.sounds.idle:
                    self.sound_channel.queue(self.weapon.sounds.idle)
                else:
                    self.sound_channel.play(self.weapon.sounds.idle)

        if self.shooting:
            self.shoot(self.weapon)

        elif self.switching:
            self.switch_weapons()

    def draw(self):
        #pygame.draw.line(DISPLAY, (0, 255, 0), (H_W - self.weapon.max_x_spread, H_H - 10),
        #                 (H_W - self.weapon.max_x_spread, H_H + 10), 2)
        #pygame.draw.line(DISPLAY, (0, 255, 0), (H_W + self.weapon.max_x_spread, H_H - 10),
        #                 (H_W + self.weapon.max_x_spread, H_H + 10), 2)
        weapon_image = self.weapon.weapon_sheet.subsurface(self.weapon.cell_size * self.column, 0,
                                                           self.weapon.cell_size, self.weapon.cell_size)
        weapon_image = pygame.transform.scale(weapon_image, (WeaponModel.size, WeaponModel.size))
        DISPLAY.blit(weapon_image, ((D_W - WeaponModel.size) / 2, D_H - WeaponModel.size + self.display_y))


class Effects:
    def __init__(self):
        self.colour = None
        self.alpha = 0

    def update(self, colour):
        self.colour = colour
        self.alpha = 128

    def draw(self):
        if self.alpha:
            effect = pygame.Surface((D_W, D_H))
            effect.set_alpha(self.alpha)
            effect.fill(self.colour)
            DISPLAY.blit(effect, (0, 0))
            self.alpha -= 16


class Hud:
    safezone_w = 5
    safezone_h = 5
    font_h = 28

    def draw(self):
        # Messages
        y = Hud.safezone_h
        for m in reversed(MESSAGES):
            message = render_text(m.text, m.colour, m.alpha)
            DISPLAY.blit(message, (Hud.safezone_w, y))
            y += Hud.font_h

        # FPS counter
        if SHOW_FPS:
            fps_counter = render_text(str(ceil(CLOCK.get_fps())), (0, 255, 0))
            DISPLAY.blit(fps_counter, (D_W - Hud.safezone_w - fps_counter.get_width(), Hud.safezone_h))

        # Weapon HUD
        WEAPON_MODEL.draw()
        current_weapon = WEAPON_MODEL.weapon

        weapon_name = render_text(str(current_weapon.name), (0, 0, 0))
        DISPLAY.blit(weapon_name, (D_W - weapon_name.get_width() - Hud.safezone_w, D_H - Hud.font_h*2 - Hud.safezone_h))

        # Player hp HUD
        hp_text = render_text('HP:', (0, 0, 0))
        hp_amount = render_text(str(PLAYER.hp), dynamic_colour(PLAYER.hp, Player.max_hp))
        DISPLAY.blit(hp_text, (Hud.safezone_w, D_H - Hud.font_h*2 - Hud.safezone_h))
        DISPLAY.blit(hp_amount, (Hud.safezone_w, D_H - Hud.font_h - Hud.safezone_h))

        # Loadout HUD
        x = D_W - Hud.safezone_w
        for w in reversed(WEAPONS):
            if w:
                weapon_nr = WEAPONS.index(w)
                if w == WEAPON_MODEL.weapon:  # If equipped
                    colour = (0, 255, 0)
                elif weapon_nr in PLAYER.weapon_loadout:  # If picked up
                    colour = (0, 128, 0)
                else:  # If not picked up
                    colour = (0, 32, 0)
                number = render_text(str(weapon_nr), colour)
                x -= number.get_width()
                DISPLAY.blit(number, (x, D_H - Hud.font_h - Hud.safezone_h))
                x -= 10

        BOSSHEALTHBAR.draw()
        EFFECTS.draw()


class Message:
    display_ticks = 150  # How many ticks message stays on screen
    fade_speed = 15  # Rate at which text alpha decreases after display_ticks has gone down to 0
    max_amount = 10  # Max amount of messages that can be on screen

    def __init__(self, text, colour=(255, 255, 255)):
        self.text = text
        self.colour = colour
        self.ticks = 0
        self.alpha = 255
        if len(MESSAGES) == Message.max_amount:
            del MESSAGES[0]

    def update(self):
        if self.ticks == Message.display_ticks:
            self.alpha -= Message.fade_speed
            if self.alpha <= 0:
                MESSAGES.remove(self)
        else:
            self.ticks += 1


class CameraPlane:
    half_len = 0.5

    def __init__(self, rays_amount, fov):
        # Creates a list of rayangle offsets which will be added to player's viewangle when sending rays every frame
        # Bc these offsets do not change during the game, they are calculated before the game starts
        # Offsets are calculated so that each ray will be equal distance away from previous ray on the camera plane
        # Of course in 2D rendering camera plane is acutally a line
        # Also FOV has to be < pi (and not <= pi) for it to work properly

        self.rayangle_offsets = []

        camera_plane_start = -CameraPlane.half_len
        camera_plane_step = CameraPlane.half_len * 2 / rays_amount

        self.dist = CameraPlane.half_len / tan(fov / 2)
        for i in range(rays_amount):
            camera_plane_pos = camera_plane_start + i * camera_plane_step

            angle = atan2(camera_plane_pos, self.dist)
            self.rayangle_offsets.append(angle)


class Drawable:
    def get_cropping_height(self):
        if self.height > D_H:
            # Based on image height, get cropping_height
            # Adjust height if cropping_height < TEXTURE_SIZE

            # Calculate how much of height is needed
            # Calculate the ideal cropping height
            # Calculate the actual cropping height which will be the closest even number rounding up perfect_height
            amount_of_height_needed = D_H / self.height
            perfect_height = TEXTURE_SIZE * amount_of_height_needed
            self.cropping_height = ceil(perfect_height / 2) * 2
            if self.cropping_height < TEXTURE_SIZE:
                self.height = int(self.cropping_height / perfect_height * D_H)
        else:
            self.cropping_height = TEXTURE_SIZE


class WallColumn(Drawable):
    def __init__(self, texture, column, perp_dist, display_x):
        self.perp_dist = perp_dist
        self.height = int(Drawable.constant / self.perp_dist)
        self.get_cropping_height()
        self.image = texture.subsurface((column, (TEXTURE_SIZE - self.cropping_height) / 2, 1, self.cropping_height))
        self.display_x = display_x
        self.display_y = int((D_H - self.height) / 2)

    def draw(self):
        DISPLAY.blit(pygame.transform.scale(self.image, (WallColumn.width, self.height)),
                     (self.display_x, self.display_y))


class Sprite(Drawable):
    def draw(self):
        self.height = self.width = int(Drawable.constant / self.perp_dist)
        self.get_cropping_height()
        display_y = (D_H - self.height) / 2

        half_width = self.width / 2
        left_side = self.display_pos - half_width
        right_side = left_side + self.width

        precision = 2
        for w in WALLS[::precision]:
            if self.perp_dist < w.perp_dist:  # If sprite in front of wall
                x_start = w.display_x - precision
                if x_start > left_side:
                    start_column = int((x_start - left_side) / self.width * TEXTURE_SIZE)
                    break
        for w in WALLS[::-precision]:
            if self.perp_dist < w.perp_dist:  # If sprite in front of wall
                x_end = w.display_x + precision
                if x_end < right_side:
                    end_column = int((x_end - left_side) / self.width * TEXTURE_SIZE)
                    break
        try:
            rect = (start_column, (TEXTURE_SIZE - self.cropping_height) / 2,
                    end_column - start_column, self.cropping_height)
            self.image = self.image.subsurface(rect)
            DISPLAY.blit(pygame.transform.scale(self.image, (x_end - x_start, self.height)),
                         (x_start, display_y))
        except UnboundLocalError:
            # start_column and or end_column doesn't exist
            pass
        except ValueError:
            # Problem with scaling
            print('x_end={}, x_start={}'.format(x_end, x_start))

        #try:
        #    DISPLAY.blit(pygame.transform.scale(self.image, (self.width, self.height)), (int(self.display_pos - self.width / 2), display_y))
        #except pygame.error:
        #    pass
        #x_start = int(self.display_pos - self.width / 2)
        #x_start -= x_start % WallColumn.width
        #for c, draw_x in enumerate(range(x_start, x_start + self.width, WallColumn.width)):
        #    if draw_x < D_W and draw_x >= 0:
        #        if self.perp_dist < WALLS[int(draw_x / WallColumn.width)].perp_dist:
        #            column = int(c * WallColumn.width / self.width * TEXTURE_SIZE)
        #            rect = (column, self.cropping_y, 1, self.cropping_height)
        #            try:
        #                DISPLAY.blit(pygame.transform.scale(self.image.subsurface(rect),
        #                                                    (WallColumn.width, self.height)), (draw_x, display_y))
        #            except pygame.error:
        #                print(self.width, self.height)


class Object(Sprite):
    def __init__(self, map_x, map_y, tilevalue):
        self.x = map_x + 0.5
        self.y = map_y + 0.5

        delta_x = self.x - PLAYER.x
        delta_y = self.y - PLAYER.y
        self.perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y
        if self.perp_dist > 0:
            self.display_pos = \
                int((CAMERA_PLANE.half_len + tan(atan2(delta_y, delta_x) - PLAYER.viewangle) * CAMERA_PLANE.dist) * D_W)
            self.image = TILE_VALUES_INFO[tilevalue].texture
            self.needs_to_be_drawn = True
        else:
            self.needs_to_be_drawn = False

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)


class Enemy(Sprite):
    type = 'Normal'
    animation_ticks = 5  # Enemy animation frames delay

    def __init__(self, spritesheet, pos):
        self.x, self.y = pos
        self.home = int(self.x), int(self.y)
        self.viewangle = 0

        self.sheet = spritesheet
        self.row = 0  # Spritesheet row
        self.column = 0  # Spritesheet column

        self.path = []
        self.target_tile = self.home
        self.status = 'default'  # (default, shooting, hit, dead)
        self.chasing = False

        # Take attributes from ENEMY_INFO based on spritesheet
        self.channel = pygame.mixer.Channel(ENEMY_INFO[self.sheet].id)
        self.sounds = ENEMY_INFO[self.sheet].sounds
        self.hp = ENEMY_INFO[self.sheet].hp
        self.speed = ENEMY_INFO[self.sheet].speed
        self.wandering_radius = ENEMY_INFO[self.sheet].wandering_radius
        self.shooting_range = ENEMY_INFO[self.sheet].shooting_range
        self.accuracy = ENEMY_INFO[self.sheet].accuracy
        self.damage_multiplier = ENEMY_INFO[self.sheet].damage_multiplier
        self.memory = ENEMY_INFO[self.sheet].memory
        self.patience = ENEMY_INFO[self.sheet].patience
        self.pain_chance = ENEMY_INFO[self.sheet].pain_chance
        self.shot_columns = ENEMY_INFO[self.sheet].shot_columns
        self.running_rows = ENEMY_INFO[self.sheet].running_rows
        self.shooting_row = ENEMY_INFO[self.sheet].shooting_row
        self.hit_row = ENEMY_INFO[self.sheet].hit_row

        # Timed events tick variables (frames passed since some action)
        self.anim_ticks = 0
        self.last_saw_ticks = self.memory
        self.stationary_ticks = 0

    def __eq__(self, other):
        return self.home == other.home

    def get_home_room(self):
        # Makes a self.home_room list which contains all the map points in his room

        def get_unvisited(pos):
            # Gets new unvisited points
            pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            for pos_offset in pos_offsets:
                pos_x = pos[0] + pos_offset[0]
                pos_y = pos[1] + pos_offset[1]
                if (pos_x, pos_y) not in visited + unvisited and TILEMAP[pos_y][pos_x] <= 0:
                    unvisited.append((pos_x, pos_y))

        visited = [(self.home[0], self.home[1])]
        unvisited = []
        get_unvisited((self.home[0], self.home[1]))

        while unvisited:  # While there is unscanned/unvisited points
            current = unvisited[0]  # Get new point
            del unvisited[0]  # Delete it from unvisited bc it's about to get visited
            visited.append(current)  # Add point to visited
            get_unvisited(current)  # Scan new points from that location

        self.home_room = []
        for room_point in visited:
            if squared_dist(self.home, room_point) <= self.wandering_radius**2:
                self.home_room.append(room_point)

    def get_row_and_column(self, moved):
        angle = fixed_angle(self.viewangle - self.angle_from_player)
        self.column = round(angle / (pi / 4)) + 4
        if self.column == 8:
            self.column = 0

        if moved:
            if self.row not in self.running_rows:
                self.row = 1

            # Cycle through running animations
            self.anim_ticks += 1
            if self.anim_ticks == Enemy.animation_ticks:
                self.anim_ticks = 0
                self.row += 1
                if self.row not in self.running_rows:
                    self.row = 1
        else:
            self.row = 0
            self.anim_ticks = 0

    def can_step(self, step_x, step_y):
        if (int(PLAYER.x), int(PLAYER.y)) == (step_x, step_y) and self.shooting_range > 1:  # If dog and close
            return False

        for e in ENEMIES:
            if not self == e and not e.status == 'dead':  # Ignore self and dead enemies
                if (int(e.x), int(e.y)) == (step_x, step_y):  # If enemy in way
                    return False
        return True

    def get_nearby_alerted_enemy(self):
        for e in ENEMIES:
            if not self == e and e.chasing and can_see((self.x, self.y), (e.x, e.y)):
                    return e
        return None

    def get_sides(self):
        angle = fixed_angle(self.angle_from_player + pi / 2)
        x = cos(angle) / 2
        y = sin(angle) / 2
        return (self.x - x, self.y - y), (self.x + x, self.y + y)  # Left side, right side

    def ready_to_shoot(self):
        return self.dist_squared < self.shooting_range**2 and can_see((self.x, self.y), (PLAYER.x, PLAYER.y))

    def start_shooting(self):
        self.status = 'shooting'
        self.row = self.shooting_row
        self.column = 0
        self.anim_ticks = 0

    def shoot(self):
        # speed_factor ranges between 24 (when player's running) and 32 (when not)
        speed_factor = 24 + 8 * (1 - PLAYER.total_movement / PLAYER.speed)

        dist_from_player = sqrt(self.dist_squared)

        player_hit = random.randint(0, int(32 / self.accuracy)) < speed_factor - dist_from_player
        if player_hit:
            if dist_from_player < 2:
                damage = random.randint(21, 30)
            elif dist_from_player > 4:
                damage = random.randint(1, 10)
            else:
                damage = random.randint(11, 20)
            PLAYER.hurt(int(damage * self.damage_multiplier), self)

    def hurt(self, damage, pain):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.chasing = False
            self.status = 'dead'
            self.anim_ticks = 0
            self.row = self.hit_row
            self.column = 0
            self.play_sound(self.sounds.death)
        elif pain:
            self.status = 'hit'
            self.anim_ticks = 0
            self.row = self.hit_row
            self.column = 7

    def strafe(self):
        # Gets new path to a random empty neighbour tile (if possible)
        available_tiles = []
        pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for pos_offset in pos_offsets:
            tile_x = int(self.x) + pos_offset[0]
            tile_y = int(self.y) + pos_offset[1]
            if TILEMAP[tile_y][tile_x] <= 0:  # If tile steppable
                available_tiles.append((tile_x, tile_y))

        if available_tiles:
            self.path = pathfinding.pathfind((self.x, self.y) ,random.choice(available_tiles))
        else:
            self.path = []

    def handle_doors_underneath(self):
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

    def play_sound(self, sound, adjust_volume=True):
        # Plays a required sound
        # If enemy is far from enemy sound will be quieter
        volume = 1
        if adjust_volume:
            volume -= sqrt(self.dist_squared) / 24
        if volume > 0:
            sound.set_volume(volume)
            self.channel.play(sound)

    def update(self):
        self.handle_doors_underneath()

        moved = False
        saw_player = False

        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.angle_from_player = atan2(self.delta_y, self.delta_x)
        self.dist_squared = self.delta_x**2 + self.delta_y**2
        self.sides = self.get_sides()

        if self.status == 'dead':
            if self.column < 4:
                self.anim_ticks += 1
                if self.anim_ticks == Enemy.animation_ticks:
                    self.anim_ticks = 0
                    self.column += 1

        elif self.status == 'hit':
            saw_player = True
            self.anim_ticks += 1
            if self.anim_ticks == Enemy.animation_ticks - 2:
                self.anim_ticks = 0
                self.status = 'default'

        elif self.status == 'shooting':
            saw_player = True

            self.anim_ticks += 1
            if self.anim_ticks == Enemy.animation_ticks:
                self.anim_ticks = 0

                self.column += 1
                if self.column in self.shot_columns:
                    self.play_sound(self.sounds.attack)
                    if self.ready_to_shoot():
                        self.shoot()

                elif self.column == 6:
                    if (int(self.x), int(self.y)) == (int(PLAYER.x), int(PLAYER.y)):
                        self.column = 0  # Continues shooting
                    elif random.randint(0, 1) and self.ready_to_shoot():
                        self.column = 0  # Continues shooting
                    else:
                        self.column -= 1
                        self.status = 'default'

        else:
            if can_see((PLAYER.x, PLAYER.y), self.sides[0]) or can_see((PLAYER.x, PLAYER.y), self.sides[1]):
                saw_player = True
                if not self.chasing:
                    self.chasing = True
                    self.play_sound(self.sounds.appearance)
                self.target_tile = (int(PLAYER.x), int(PLAYER.y))
            elif self.last_saw_ticks < self.memory:
                self.chasing = True
                self.target_tile = (int(PLAYER.x), int(PLAYER.y))
            else:
                alerted_enemy = self.get_nearby_alerted_enemy()
                if alerted_enemy:
                    self.chasing = True
                    self.target_tile = (int(alerted_enemy.x), int(alerted_enemy.y))
                else:
                    self.chasing = False

            if (self.x - 0.5, self.y - 0.5) == self.target_tile:
                if self.stationary_ticks >= self.patience:
                    if (self.x - 0.5, self.y - 0.5) == self.home:
                        if random.randint(0, 1):
                            self.target_tile = random.choice(self.home_room)
                        else:
                            self.viewangle = fixed_angle(self.angle_from_player + pi)
                    else:
                        self.target_tile = self.home
                elif self.chasing and self.ready_to_shoot():
                    self.start_shooting()
            else:
                if not self.path:
                    self.path = pathfinding.pathfind((self.x, self.y), self.target_tile)
                if self.path:
                    step_x, step_y = self.path[0]
                    if not self.can_step(step_x, step_y):
                        if self.chasing and random.randint(0, 1) and self.ready_to_shoot():
                            self.start_shooting()
                        else:
                            self.strafe()
                    else:
                        moved = True
                        step_x += 0.5
                        step_y += 0.5
                        self.viewangle = atan2(step_y - self.y, step_x - self.x)
                        self.x += cos(self.viewangle) * self.speed
                        self.y += sin(self.viewangle) * self.speed

                        if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                            self.x = step_x
                            self.y = step_y
                            self.path = pathfinding.pathfind((self.x, self.y), self.target_tile)

                            if self.chasing and self.ready_to_shoot():
                                self.start_shooting()
                            elif not self.path:
                                self.viewangle = fixed_angle(self.angle_from_player + pi)
            if not self.status == 'shooting':
                self.get_row_and_column(moved)

        if moved:
            self.stationary_ticks = 0
        else:
            self.stationary_ticks += 1
            if self.stationary_ticks > self.patience:
                self.stationary_ticks = self.patience
        if saw_player:
            self.last_saw_ticks = 0
        else:
            self.last_saw_ticks += 1
            if self.last_saw_ticks > self.memory:
                self.last_saw_ticks = self.memory

        self.update_for_drawing()

    def update_for_drawing(self):
        self.needs_to_be_drawn = False
        self.perp_dist = self.delta_x * PLAYER.dir_x + self.delta_y * PLAYER.dir_y
        if self.perp_dist > 0:
            if can_see((PLAYER.x, PLAYER.y), (self.x, self.y), PLAYER.viewangle, FOV) or \
                    can_see((PLAYER.x, PLAYER.y), self.sides[0], PLAYER.viewangle, FOV) or \
                    can_see((PLAYER.x, PLAYER.y), self.sides[1], PLAYER.viewangle, FOV):
                self.display_pos = \
                    (CAMERA_PLANE.half_len + tan(self.angle_from_player - PLAYER.viewangle) * CAMERA_PLANE.dist) * D_W
                self.image = self.sheet.subsurface(self.column * TEXTURE_SIZE, self.row * TEXTURE_SIZE,
                                                   TEXTURE_SIZE, TEXTURE_SIZE)
                self.needs_to_be_drawn = True


class Boss(Enemy):
    type = 'Boss'

    def __init__(self, spritesheet, pos):
        self.x, self.y = self.home = pos

        self.sheet = spritesheet
        self.row = 0
        self.column = 0

        self.path = []
        self.status = 'sleeping'
        self.chasing = False
        self.seen_player = False

        # Take attributes from ENEMY_INFO based on spritesheet
        self.channel = pygame.mixer.Channel(ENEMY_INFO[self.sheet].id)
        self.sounds = ENEMY_INFO[self.sheet].sounds
        self.max_hp = self.hp = ENEMY_INFO[self.sheet].hp
        self.speed = ENEMY_INFO[self.sheet].speed
        self.shooting_range = ENEMY_INFO[self.sheet].shooting_range
        self.accuracy = ENEMY_INFO[self.sheet].accuracy
        self.damage_multiplier = ENEMY_INFO[self.sheet].damage_multiplier
        self.pain_chance = ENEMY_INFO[self.sheet].pain_chance
        self.shot_columns = ENEMY_INFO[self.sheet].shot_columns
        self.shooting_row = ENEMY_INFO[self.sheet].shooting_row
        self.hit_row = ENEMY_INFO[self.sheet].hit_row

        self.appearance_ticks = 30  # Time duration in ticks that boss will not shoot when appearing
        self.anim_ticks = 0

    def hurt(self, damage, pain):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.chasing = False
            self.status = 'dead'
            self.anim_ticks = 0
            self.row = self.hit_row
            self.column = 0
            PLAYER.has_key = True
            MESSAGES.append(Message('Defeated Boss + Picked up a key'))
            self.play_sound(self.sounds.death)

    def update(self):
        self.handle_doors_underneath()

        self.delta_x = self.x - PLAYER.x
        self.delta_y = self.y - PLAYER.y
        self.angle_from_player = atan2(self.delta_y, self.delta_x)
        self.dist_squared = self.delta_x**2 + self.delta_y**2
        self.sides = self.get_sides()

        if self.status == 'dead':
            if self.column < 7:
                self.anim_ticks += 1
                if self.anim_ticks == Enemy.animation_ticks:
                    self.anim_ticks = 0
                    self.column += 1

        elif self.status == 'shooting':
            self.anim_ticks += 1
            if self.anim_ticks == Enemy.animation_ticks:
                self.anim_ticks = 0
                self.column += 1
                if self.column in self.shot_columns:
                    self.play_sound(self.sounds.attack)
                    if self.ready_to_shoot():
                        self.shoot()

                elif self.column == 8:
                    self.status = 'default'
                    self.anim_ticks = 0
                    self.row = 0
                    self.column = 0

        elif self.status == 'default':
            if self.appearance_ticks:
                self.appearance_ticks -= 1
            if not self.channel.get_busy():
                self.play_sound(self.sounds.step)
            if not self.path:
                self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
            step_x, step_y = self.path[0]
            if not self.can_step(step_x, step_y):
                if random.randint(0, 1):
                    self.start_shooting()
                else:
                    self.strafe()
            else:
                step_x += 0.5
                step_y += 0.5
                angle = atan2(step_y - self.y, step_x - self.x)
                self.x += cos(angle) * self.speed
                self.y += sin(angle) * self.speed

                if abs(self.x - step_x) < self.speed and abs(self.y - step_y) < self.speed:
                    self.x = step_x
                    self.y = step_y
                    self.path = pathfinding.pathfind((self.x, self.y), (PLAYER.x, PLAYER.y))
                    if not self.seen_player and can_see((self.x, self.y), (PLAYER.x, PLAYER.y)):
                        self.play_sound(self.sounds.appearance, False)
                        self.seen_player = True

                    if self.ready_to_shoot() and not self.appearance_ticks:
                        self.start_shooting()

            self.anim_ticks += 1
            if self.anim_ticks == Enemy.animation_ticks:
                self.anim_ticks = 0
                self.column += 1
                if self.column == 4:
                    self.column = 0

        self.update_for_drawing()


class BossHealthBar:
    w = 400
    h = 24
    def __init__(self):
        self.visible = False
        self.x = (D_W - BossHealthBar.w) / 2
        self.y = -64

    def start_showing(self, boss):
        self.visible = True
        self.boss = boss
        self.boss_image = self.boss.sheet.subsurface(0, 0, TEXTURE_SIZE, TEXTURE_SIZE)

    def draw(self):
        if self.visible:
            if self.boss.hp == 0:
                self.y -= 8
                if self.y == -64:
                    self.visible = False
            elif self.y < 24:
                self.y += 8

            colour = dynamic_colour(self.boss.hp, self.boss.max_hp)
            health_percentage = self.boss.hp / self.boss.max_hp

            pygame.draw.rect(DISPLAY, (0, 0, 0), (self.x - 4, self.y - 4, BossHealthBar.w + 8, BossHealthBar.h + 8))
            pygame.draw.rect(DISPLAY, colour, (self.x, self.y, BossHealthBar.w * health_percentage, BossHealthBar.h))

            DISPLAY.blit(self.boss_image, (self.x - 32, self.y + BossHealthBar.h / 2 - 32))


class Level:
    def load(self, level_nr):
        self.nr = level_nr
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
            PLAYER.setup(player_pos, player_angle)

        # Background
        with open('../levels/{}/background.txt'.format(level_nr), 'r') as f:
            colour = f.readline().replace('\n', '').split(',')
            colour = [int(i) for i in colour]
            self.ceiling_colour = tuple(colour)
            colour = f.readline().replace('\n', '').split(',')
            colour = [int(i) for i in colour]
            self.floor_colour = tuple(colour)

            self.skytexture = None
            value = int(f.readline().replace('\n', ''))
            if value > 0:
                skytextures = os.listdir('../textures/skies')
                try:
                    self.skytexture = pygame.image.load('../textures/skies/{}'.format(skytextures[value - 1])).convert()
                except pygame.error or IndexError:
                    pass
                else:
                    self.skytexture = pygame.transform.scale(self.skytexture, (D_W * 4, H_H))

        # Enemies
        global ENEMIES
        ENEMIES = []
        for row in range(len(TILEMAP)):
            for column in range(len(TILEMAP[row])):
                tile = TILE_VALUES_INFO[TILEMAP[row][column]]
                if tile.type == 'Enemy':
                    spritesheet = TILE_VALUES_INFO[TILEMAP[row][column]].texture
                    pos = (column + 0.5, row + 0.5)
                    if tile.desc == 'Normal':
                        ENEMIES.append(Enemy(spritesheet, pos))
                    elif tile.desc == 'Boss':
                        ENEMIES.append(Boss(spritesheet, pos))
                    TILEMAP[row][column] = 0  # Clears tile
        # Process some stuff after enemies have been cleared from tilemap
        for e in ENEMIES:
            if e.type == 'Normal':
                e.get_home_room()

        # Run pathfinding setup function
        pathfinding.setup(TILEMAP, TILE_VALUES_INFO)

    def start(self, level_nr):
        global TIME
        TIME = 0
        global DOORS
        DOORS = []
        global MESSAGES
        MESSAGES = []
        global EFFECTS
        EFFECTS = Effects()
        global WEAPON_MODEL
        WEAPON_MODEL = WeaponModel()
        global BOSSHEALTHBAR
        BOSSHEALTHBAR = BossHealthBar()

        self.load(level_nr)
        update_gameobjects()
        game_loop()

    def restart(self, enemy=None):
        def get_turn_radians():
            turn_speed = 0.05
            difference = fixed_angle(enemy.angle_from_player - PLAYER.viewangle)
            if difference > 0:
                return turn_speed
            else:
                return  -turn_speed

        global QUIT
        text_alpha = 0
        overlay_alpha = 0

        # If enemy, turn towards it
        while enemy:
            turn_radians = get_turn_radians()
            PLAYER.rotate(turn_radians)
            PLAYER.dir_x = cos(PLAYER.viewangle)
            PLAYER.dir_y = sin(PLAYER.viewangle)

            for e in ENEMIES:
                e.update_for_drawing()

            if overlay_alpha != 128:
                overlay_alpha += 8

            send_rays()
            draw_frame()
            draw_black_overlay(overlay_alpha)

            pygame.display.flip()
            CLOCK.tick(30)

            if abs(PLAYER.viewangle - enemy.angle_from_player) <= abs(turn_radians):
                break

        # Wait for a button press
        continued = False
        while not continued:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        QUIT = True
                        continued = True
                    elif event.key == K_SPACE:
                        continued = True

            if overlay_alpha != 128:
                overlay_alpha += 8
            text_alpha -= 15
            if text_alpha <= -255:
                text_alpha = 255

            for e in ENEMIES:
                e.update_for_drawing()
            send_rays()
            draw_frame()
            draw_black_overlay(overlay_alpha)

            you_died = render_text('YOU DIED', (255, 255, 255), abs(text_alpha))
            DISPLAY.blit(you_died, ((D_W - you_died.get_width()) / 2, (D_H - you_died.get_height()) / 2))
            pygame.display.flip()
            CLOCK.tick(30)

        # Start new level
        pygame.mouse.get_rel()
        pygame.event.clear()
        self.start(self.nr)

    def finish(self):
        PLAYER.save_weapon_loadout()

        seconds = int(TIME / 30)  # Rounds time spent down, 45.8 seconds will display 45
        minutes = 0
        while seconds >= 60:
            minutes += 1
            seconds -= 60
        dead = 0
        for e in ENEMIES:
            if e.status == 'dead':
                dead += 1

        global QUIT
        overlay_alpha = 0
        text_alpha = 0

        continued = False
        while not continued:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        QUIT = True
                        continued = True
                    elif event.key == K_SPACE:
                        continued = True

            text_alpha -= 15
            if text_alpha <= -255:
                text_alpha = 255
            if overlay_alpha != 128:
                overlay_alpha += 8

            send_rays()
            draw_frame()
            draw_black_overlay(overlay_alpha)

            level_finished = render_text('LEVEL FINISHED', (255, 255, 255))
            time_spent = render_text('TIME: {}m {}s'.format(minutes, seconds), (255, 255, 255))
            kills = render_text('KILLS: {}/{}'.format(len(ENEMIES), dead), (255, 255, 255))
            press_space_to_continue = render_text('Press SPACE to continue', (255, 255, 255), abs(text_alpha))
            DISPLAY.blit(level_finished, ((D_W - level_finished.get_width()) / 2, 256))
            DISPLAY.blit(time_spent, ((D_W - time_spent.get_width()) / 2, 320))
            DISPLAY.blit(kills, ((D_W - kills.get_width()) / 2, 384))
            DISPLAY.blit(press_space_to_continue, ((D_W - press_space_to_continue.get_width()) / 2, 448))
            pygame.display.flip()
            CLOCK.tick(30)

        self.start(self.nr + 1)


def squared_dist(from_, to):
    return (from_[0] - to[0])**2 + (from_[1] - to[1])**2


def fixed_angle(angle):
    while angle > pi:
        angle -= 2 * pi
    while angle < -pi:
        angle += 2 * pi
    return angle


def can_see(from_, to, viewangle=None, fov=None):
    # Universal function for checking if it's possible to see one point from another in tilemap
    # Returns True if end point visible, False if not visible

    start_x, start_y = from_
    end_x, end_y = to
    angle_to_end = atan2(end_y - start_y, end_x - start_x)

    if viewangle is not None and fov is not None:  # If viewangle and fov given
        angle = abs(viewangle - angle_to_end)
        if angle > pi:
            angle = 2 * pi - angle
        if angle > fov / 2:  # If end position outside viewangle
            return False

    # Check if there is something between end and start point
    collision_x, collision_y = raycast(from_, angle_to_end)
    return squared_dist(from_, (collision_x, collision_y)) > squared_dist(from_, to)


def dynamic_colour(current, maximum):
    ratio = current / maximum  # 1 is completely green, 0 completely red
    if ratio < 0.5:
        r = 255
        g = int(ratio * 2 * 255)
    else:
        ratio = 1 - ratio
        g = 255
        r = int(ratio * 2 * 255)
    return r, g, 0


def send_rays():
    global WALLS
    WALLS = []
    global OBJECTS
    OBJECTS = []
    for c, rayangle_offset in enumerate(CAMERA_PLANE.rayangle_offsets):
        # Get values from raycast()
        collision_x, collision_y, texture, column = \
            raycast((PLAYER.x, PLAYER.y), PLAYER.viewangle + rayangle_offset, True)

        # Calculate perpendicular distance (needed to avoid fisheye effect)
        delta_x = collision_x - PLAYER.x
        delta_y = collision_y - PLAYER.y
        perp_dist = delta_x * PLAYER.dir_x + delta_y * PLAYER.dir_y

        # Create Wall object
        WALLS.append(WallColumn(texture, column, perp_dist, c * WallColumn.width))


def raycast(start_pos, rayangle, extra_values=False):
    def check_collision(collision_x, collision_y, x_step, y_step):
        # x_step is the distance needed to move in x to get to the next similar type interception
        # y_step is the distance needed to move in y to get to the next similat type interception

        tile_value = TILEMAP[map_y][map_x]
        tile_type = TILE_VALUES_INFO[tile_value].type
        tile_desc = TILE_VALUES_INFO[tile_value].desc

        if tile_type == 'Object':
            if extra_values:
                for obj in OBJECTS:
                    if (int(obj.x), int(obj.y)) == (map_x, map_y):
                        break
                else:
                    OBJECTS.append(Object(map_x, map_y, tile_value))

        elif tile_type == 'Door':
            for d in DOORS:
                if (d.x, d.y) == (map_x, map_y):
                    door = d
                    break
            else:
                if tile_desc == 'Boss':
                    door = BossDoor((map_x, map_y), tile_value)
                else:
                    door = Door((map_x, map_y), tile_value)
                DOORS.append(door)

            collision_x += x_step / 2
            collision_y += y_step / 2
            if (int(collision_x), int(collision_y)) == (door.x, door.y):
                if x_step == 1 or x_step == -1:
                    surface_offset = collision_y - int(collision_y)
                else:
                    surface_offset = collision_x - int(collision_x)
                if surface_offset < door.closed_state:
                    if extra_values:
                        texture = TILE_VALUES_INFO[tile_value].texture
                        column = int(TEXTURE_SIZE * abs(surface_offset - door.closed_state))
                        return collision_x, collision_y, texture, column
                    else:
                        return collision_x, collision_y

        else:  # elif tile_type == 'Wall':
            if extra_values:
                for d in DOORS:
                    if (d.x, d.y) == (x - a, y - b):
                        texture = Door.side_texture
                        break
                else:
                    texture = TILE_VALUES_INFO[tile_value].texture
                if x_step == 1 or x_step == -1:
                    surface_offset = collision_y - int(collision_y)
                    column = int(TEXTURE_SIZE * abs(a - surface_offset))
                    column += TEXTURE_SIZE
                else:
                    surface_offset = collision_x - int(collision_x)
                    column = int(TEXTURE_SIZE * abs(b - surface_offset))
                return collision_x, collision_y, texture, column
            else:
                return collision_x, collision_y

    def interception_horizontal():
        if a:
            return x_intercept < x
        else:
            return x_intercept > x

    def interception_vertical():
        if b:
            return y_intercept < y
        else:
            return y_intercept > y

    # https://www.youtube.com/watch?v=eOCQfxRQ2pY
    #
    #      a = 0 | a = 1
    # -pi  b = 0 | b = 0  -
    #     -------|------- 0 rad
    #  pi  a = 0 | a = 1  +
    #      b = 1 | b = 1
    rayangle = fixed_angle(rayangle + 0.000001)
    tan_rayangle = tan(rayangle)
    x = int(start_pos[0])
    y = int(start_pos[1])
    dx = start_pos[0] - x + 0.000001
    dy = start_pos[1] - y + 0.000001

    if abs(rayangle) < pi / 2:
        a = 1
        tile_step_x = 1
        y_step = tan_rayangle
    else:
        a = 0
        tile_step_x = -1
        y_step = -tan_rayangle
    if rayangle > 0:
        b = 1
        tile_step_y = 1
        x_step = 1 / tan_rayangle
    else:
        b = 0
        tile_step_y = -1
        x_step = 1 / -tan_rayangle

    x_intercept = x + dx + (b - dy) / tan_rayangle
    y_intercept = y + dy + (a - dx) * tan_rayangle
    x += a
    y += b

    while True:
        while interception_horizontal():
            map_x = int(x_intercept)
            map_y = y - (1 - b)
            if TILEMAP[map_y][map_x]:
                collision = check_collision(x_intercept, y, x_step, tile_step_y)
                if collision:
                    return collision
            y += tile_step_y
            x_intercept += x_step
        while interception_vertical():
            map_x = x - (1 - a)
            map_y = int(y_intercept)
            if TILEMAP[map_y][map_x]:
                collision = check_collision(x, y_intercept, tile_step_x, y_step)
                if collision:
                    return collision
            x += tile_step_x
            y_intercept += y_step


def events():
    global PAUSED
    global SHOW_FPS
    global QUIT

    if PAUSED:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    PAUSED = False
                    update_sound_channels()
                elif event.key == K_F1:
                    SHOW_FPS = not SHOW_FPS
                elif event.key == K_RETURN:
                    QUIT = True
        pygame.mouse.get_rel()

    else:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    PAUSED = True
                    update_sound_channels()
                elif event.key == K_F1:
                    SHOW_FPS = not SHOW_FPS

                if event.key == K_e:
                    x = int(PLAYER.x + PLAYER.dir_x)
                    y = int(PLAYER.y + PLAYER.dir_y)
                    tile_value = TILEMAP[y][x]
                    tile_type = TILE_VALUES_INFO[tile_value].type
                    tile_desc = TILE_VALUES_INFO[tile_value].desc
                    if tile_type == 'Door':
                        if tile_desc != 'Static':
                            if PLAYER.has_key or tile_desc == 'Dynamic' or tile_desc == 'Boss':
                                for d in DOORS:
                                    # If found the right door and it's not in motion already
                                    if x == d.x and y == d.y:
                                        if not d.locked:
                                            d.state = 1
                                        else:
                                            MESSAGES.append(Message('This door is now locked'))
                                        break
                            else:
                                MESSAGES.append(Message('Opening this door requires a key'))
                        else:
                            MESSAGES.append(Message('Cannot open this door'))
                    elif tile_type == 'Wall' and tile_desc == 'End-trigger':
                        TILEMAP[y][x] += 1  # Change trigger block texture
                        LEVEL.finish()

                elif not WEAPON_MODEL.shooting:
                    key = pygame.key.name(event.key)
                    numbers = (str(x) for x in range(1, 10))
                    if key in numbers:
                        key = int(key)
                        if key in PLAYER.weapon_loadout and key != PLAYER.weapon_nr:
                            WEAPON_MODEL.switching = key

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not WEAPON_MODEL.switching:
                        WEAPON_MODEL.shooting = True


def update_gameobjects():
    for c, d in enumerate(DOORS):
        d.move()
        if d.type == 'Normal' and d.state == 0:  # Only deletes normal doors that are closed
            del DOORS[c]
    for e in ENEMIES:
        e.update()
    for m in MESSAGES:
        m.update()
    WEAPON_MODEL.update()


def handle_objects_under_player():
    # Checking if player is standing on an object bc raycast() will miss objects player is standing on
    # Also picks up objects if they can be picked up
    global OBJECTS
    tile_value = TILEMAP[int(PLAYER.y)][int(PLAYER.x)]
    if tile_value < 0:
        OBJECTS.append(Object(int(PLAYER.x), int(PLAYER.y), tile_value))
        if TILE_VALUES_INFO[tile_value].desc == 'Dynamic':
            colour = None
            type = 0  # 0 = item, 1 = weapon
            # First handle all now-weapon pickups
            if tile_value == -5:
                PLAYER.has_key = True
                MESSAGES.append(Message('Picked up a key'))
                colour = (255, 255, 0)
            elif tile_value == -6:
                if PLAYER.hp < PLAYER.max_hp:
                    PLAYER.hp += 10
                    if PLAYER.hp > PLAYER.max_hp:
                        PLAYER.hp = PLAYER.max_hp
                    MESSAGES.append(Message('Health +10'))
                    colour = (0, 255, 0)
            elif tile_value == -7:
                if PLAYER.hp < PLAYER.max_hp:
                    PLAYER.hp += 25
                    if PLAYER.hp > PLAYER.max_hp:
                        PLAYER.hp = PLAYER.max_hp
                    MESSAGES.append(Message('Health +25'))
                    colour = (0, 255, 0)
            # Then handle weapon pickups
            if not WEAPON_MODEL.shooting and not WEAPON_MODEL.switching:
                if tile_value == -1:
                    if not 5 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(5)
                        WEAPON_MODEL.switching = 5
                    colour = (0, 0, 255)
                    type = 1
                elif tile_value == -2:
                    if not 4 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(4)
                        WEAPON_MODEL.switching = 4
                    colour = (0, 0, 255)
                    type = 1
                elif tile_value == -3:
                    if not 3 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(3)
                        WEAPON_MODEL.switching = 3
                    colour = (0, 0, 255)
                    type = 1
                elif tile_value == -4:
                    if not 2 in PLAYER.weapon_loadout:
                        PLAYER.weapon_loadout.append(2)
                        WEAPON_MODEL.switching = 2
                    colour = (0, 0, 255)
                    type = 1
            if colour:
                EFFECTS.update(colour)
                TILEMAP[int(PLAYER.y)][int(PLAYER.x)] = 0
                if type == 0:
                    ITEM_PICKUP_SOUND.play()
                else:
                    MESSAGES.append(Message('Picked up {}'.format(WEAPONS[tile_value + len(WEAPONS)].name)))
                    WEAPON_PICKUP_SOUND.play()


def draw_background():
    if LEVEL.skytexture:
        # x_offset ranges from 0 to 1
        x_offset = (PLAYER.viewangle + pi) / (2 * pi)
        x = x_offset * LEVEL.skytexture.get_width()

        if x_offset <= 0.75:
            # Sky texture can be drawn as one image
            sky = LEVEL.skytexture.subsurface(x, 0, D_W, H_H)
            DISPLAY.blit(sky, (0, 0))
        else:
            # Sky texture needs to be drawn as two separate parts
            sky_left = LEVEL.skytexture.subsurface(x, 0, LEVEL.skytexture.get_width() - x, H_H)
            sky_right = LEVEL.skytexture.subsurface(0, 0, D_W - sky_left.get_width(), H_H)
            DISPLAY.blit(sky_left, (0, 0))
            DISPLAY.blit(sky_right, (sky_left.get_width(), 0))
    else:
        pygame.draw.rect(DISPLAY, LEVEL.ceiling_colour, ((0, 0), (D_W, H_H)))  # Ceiling
    pygame.draw.rect(DISPLAY, LEVEL.floor_colour, ((0, H_H), (D_W, H_H)))  # Floor


def draw_frame():
    draw_background()
    # Draw walls
    for w in WALLS:
        w.draw()

    # Get a list of objects that need to be drawn
    to_draw = []
    for sprite in ENEMIES + OBJECTS:
        if sprite.needs_to_be_drawn:
            to_draw.append(sprite)
    # Sort objects by perp_dist so things further away are drawn first
    to_draw.sort(key=lambda x: x.perp_dist, reverse=True)

    # Draw all objects in order
    for obj in to_draw:
        obj.draw()


def update_sound_channels():
    for channel_id in range(8):
        if PAUSED:
            pygame.mixer.Channel(channel_id).pause()
        else:
            pygame.mixer.Channel(channel_id).unpause()


def draw_pause_overlay():
    draw_black_overlay(128)
    paused = render_text('PAUSED', (255, 255, 255))
    DISPLAY.blit(paused, ((D_W - paused.get_width()) / 2, (D_H - paused.get_height()) / 2))


def draw_black_overlay(alpha):
    black_overlay = pygame.Surface((D_W, D_H))
    black_overlay.set_alpha(alpha)
    black_overlay.fill((0, 0, 0))
    DISPLAY.blit(black_overlay, (0, 0))


def render_text(text, colour, alpha=255):
    image = GAME_FONT.render(text, False, colour)
    image.set_alpha(alpha)
    return image


def game_loop():
    global TIME
    while not QUIT:
        events()
        if not PAUSED:
            TIME += 1
            PLAYER.rotate(pygame.mouse.get_rel()[0] * SENSITIVITY)
            PLAYER.handle_movement()
            update_gameobjects()
        else:
            for e in ENEMIES:
                e.update_for_drawing()

        send_rays()
        draw_frame()
        handle_objects_under_player()
        HUD.draw()

        if PAUSED:
            draw_pause_overlay()

        pygame.display.flip()
        CLOCK.tick(30)


if __name__ == '__main__':
    import os

    from math import *
    import random

    import numpy
    from sklearn.preprocessing import normalize

    import pygame
    from pygame.locals import *

    from game.settings import *
    import game.graphics as graphics
    import game.sounds as sounds
    import game.enemies as enemies
    import game.weapons as weapons
    import game.pathfinding as pathfinding

    # Make class constants
    Drawable.constant = 0.65 * D_H
    WallColumn.width = int(D_W / DRAW_RESOLUTION)
    WeaponModel.size = size = int(D_W * 0.75)

    # Pygame stuff
    pygame.mixer.pre_init(11025, -16, 1, 256)
    pygame.init()
    pygame.display.set_caption('Raycaster')
    DISPLAY = pygame.display.set_mode((D_W, D_H))
    CLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.event.set_allowed([KEYDOWN, MOUSEBUTTONDOWN])

    CAMERA_PLANE = CameraPlane(DRAW_RESOLUTION, FOV)
    GAME_FONT = pygame.font.Font('../font/LCD_Solid.ttf', 32)
    HUD = Hud()

    Door.side_texture = graphics.get_door_side_texture()
    ENEMY_INFO = enemies.get_enemy_info()
    TILE_VALUES_INFO = graphics.get_tile_values_info(TEXTURE_SIZE, ENEMY_INFO)
    WEAPONS = weapons.get()

    # Sounds
    Door.open_sound,\
    Door.close_sound,\
    ITEM_PICKUP_SOUND,\
    WEAPON_PICKUP_SOUND = sounds.get()

    QUIT = False
    PAUSED = False
    SHOW_FPS = False

    PLAYER = Player()
    LEVEL = Level()
    LEVEL.start(2)
    pygame.quit()
