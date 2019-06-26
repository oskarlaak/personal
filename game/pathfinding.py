class Door:
    def __init__(self, pos):
        self.pos = pos
        self.neighbours = []


def get_neighbour_doors(pos):
    # Returns a list of doors that can be reached from given location
    def get_unvisited(pos):
        # Right, down, left, up
        pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for pos_offset in pos_offsets:
            pos_x = pos[0] + pos_offset[0]
            pos_y = pos[1] + pos_offset[1]

            if (pos_x, pos_y) not in visited + unvisited:
                if TILEMAP[pos_y][pos_x] <= 0:
                    unvisited.append((pos_x, pos_y))
                elif TILE_VALUES_INFO[TILEMAP[pos_y][pos_x]].type == 'Door' and \
                        TILE_VALUES_INFO[TILEMAP[pos_y][pos_x]].desc != 'Static':
                    visited.append((pos_x, pos_y))
                    doors_found.append((pos_x, pos_y))

    doors_found = []

    visited = [pos]
    unvisited = []
    get_unvisited(pos)

    while unvisited:  # While there is unscanned/unvisted points
        current = unvisited[0]  # Get new point
        del unvisited[0]  # Delete it from unvisited bc it's about to get visited
        visited.append(current)  # Add point to visited
        get_unvisited(current)  # Scan new points from that location

    return sorted(doors_found)


def setup(tilemap, tile_values_info):
    # Creating 3 global variables for itself to use later
    global DOORS
    global TILEMAP
    global TILE_VALUES_INFO
    TILEMAP = tilemap[:]
    TILE_VALUES_INFO = tile_values_info

    # Scanning through tilemap and getting all the doors
    DOORS = []
    for row in range(len(TILEMAP)):
        for column in range(len(TILEMAP[row])):
            if TILE_VALUES_INFO[TILEMAP[row][column]].type == 'Door'\
                    and TILE_VALUES_INFO[TILEMAP[row][column]].desc != 'Static':
                DOORS.append(Door((column, row)))

    # Getting all door neighbours
    for parent_door in DOORS:
        child_door_positions = get_neighbour_doors(parent_door.pos)
        for d in DOORS:
            if d.pos in child_door_positions:
                child_door = d
                parent_door.neighbours.append(child_door)


def squared_dist(from_, to):
    return (from_[0] - to[0])**2 + (from_[1] - to[1])**2


def a_star(start, end):
    # Simplified version of A* search algorithm

    class Point:
        # Class to store point distances
        def __init__(self, pos):
            self.dist = squared_dist(pos, end)

    def get_path():
        # Trace back the visited tiles and get the path
        path = [end]
        while path[-1] != start:
            # Get neighbour points
            while True:
                #try:
                x, y = path[-1]
                #except IndexError:
                #    pass
                neighbours = []

                point_made = []
                # Right, down, left, up
                pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
                for pos_offset in pos_offsets:
                    pos_x = x + pos_offset[0]
                    pos_y = y + pos_offset[1]

                    if TILEMAP[pos_y][pos_x] <= 0:
                        point_made.append(True)
                    else:
                        point_made.append(False)

                    if (pos_x, pos_y) in visited and (pos_x, pos_y) not in path:
                        neighbours.append((pos_x, pos_y))

                for i in range(4):
                    if point_made[i - 1] and point_made[i]:
                        pos_x = x + pos_offsets[i - 1][0] + pos_offsets[i][0]
                        pos_y = y + pos_offsets[i - 1][1] + pos_offsets[i][1]

                        if (pos_x, pos_y) in visited and (pos_x, pos_y) not in path:
                            neighbours.append((pos_x, pos_y))

                if not neighbours:
                    # Delete that point from path and visited and find new neighbour points
                    del path[-1]
                    del visited[visited.index((x, y))]
                    continue
                else:
                    break

            # Find the closest neighbour to start
            best_dist = 9999
            for pos in neighbours:
                neighbour_dist = squared_dist(pos, start)
                if neighbour_dist < best_dist:
                    best_dist = neighbour_dist
                    winner_point = pos

            path.append(winner_point)

        del path[-1]
        return path[::-1]

    def get_unvisited(pos):
        point_made = []
        # Right, down, left, up
        pos_offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        for pos_offset in pos_offsets:
            pos_x = pos[0] + pos_offset[0]
            pos_y = pos[1] + pos_offset[1]

            if (pos_x, pos_y) not in visited + unvisited and TILEMAP[pos_y][pos_x] <= 0:
                unvisited.append((pos_x, pos_y))
                points.append(Point((pos_x, pos_y)))
                point_made.append(True)
            else:
                point_made.append(False)

        for i in range(4):
            if point_made[i - 1] and point_made[i]:
                pos_x = pos[0] + pos_offsets[i - 1][0] + pos_offsets[i][0]
                pos_y = pos[1] + pos_offsets[i - 1][1] + pos_offsets[i][1]

                if (pos_x, pos_y) not in visited + unvisited and TILEMAP[pos_y][pos_x] <= 0:
                    unvisited.append((pos_x, pos_y))
                    points.append(Point((pos_x, pos_y)))

    end_value = TILEMAP[end[1]][end[0]]  # Remember tilemap value at end pos
    TILEMAP[end[1]][end[0]] = 0  # Modify tilemap in case end location is a door

    points = []  # List storing Point class objects

    visited = [start]  # Points that have been visited
    unvisited = []  # Unvisited points that can be visited next step
    current = start  # Stores current point pos

    while True:
        get_unvisited(current)  # Get new unvisited options
        if not unvisited:  # If path cannot be created
            TILEMAP[end[1]][end[0]] = end_value  # Change back tilemap
            return []  # Return emtpy list

        # Find the best point's index
        best_dist = 9999
        for index, point in enumerate(points):
            if point.dist < best_dist:
                best_dist = point.dist
                winner_index = index

        current = unvisited[winner_index]  # Update current point
        del points[winner_index]  # Remove the same pos Point obj from points
        del unvisited[winner_index]  # Remove that point from unvisited
        visited.append(current)  # Add current to visited
        if current == end:  # Quits if end position is in visited
            break

    TILEMAP[end[1]][end[0]] = end_value  # Change back tilemap
    return get_path()


def pathfind(start, end):
    # Main pathfinding system

    # Turn start and end positions to ints
    start = (int(start[0]), int(start[1]))
    end = (int(end[0]), int(end[1]))

    start_doors = get_neighbour_doors(start)
    end_doors = get_neighbour_doors(end)
    if start_doors == end_doors or end in start_doors or start in end_doors:
        return a_star(start, end)

    # If start and end in different rooms
    # Get best starting door
    best_dist = 9999
    for start_door in start_doors:
        door_dist = squared_dist(start_door, end)
        if door_dist < best_dist:
            best_dist = door_dist
            winner_door = start_door  # Winner door pos
    for door in DOORS:
        if door.pos == winner_door:  # If found the door
            winner_door = door  # Winner door object
            break

    # Find doors path
    doors_path = [winner_door]
    visited_doors = []

    while doors_path[-1].pos not in end_doors:
        # Find best neighbour door
        while True:
            try:
                door = doors_path[-1]
            except IndexError:
                print('error at')
                print(start, end)
            neighbours = []
            for n in door.neighbours:
                if n not in visited_doors:
                    neighbours.append(n)
            if not neighbours:
                del doors_path[-1]
                visited_doors.append(door)  # Mark door as visited so it will not be visited again
                continue
            else:
                break

        # Find the closest neighbour to end
        best_dist = 9999
        for n in neighbours:
            neighbour_dist = squared_dist(n.pos, end)
            if neighbour_dist < best_dist:
                best_dist = neighbour_dist
                winner_neighbour = n

        doors_path.append(winner_neighbour)
        visited_doors.append(winner_neighbour)

    # Put together final path
    path = []
    old = start
    for point in doors_path:
        path += a_star(old, point.pos)
        old = point.pos
    path += a_star(old, end)

    return path


if __name__ == '__main__':
    # When executed directly, visualizes paths being created by algorithm
    import game.graphics as graphics
    import game.enemies as enemies
    import pygame
    from pygame.locals import *

    pygame.init()
    DISPLAY = pygame.display.set_mode((1024, 1024))
    CLOCK = pygame.time.Clock()

    level_nr = 1
    tilemap = []
    with open('../levels/{}/tilemap.txt'.format(level_nr), 'r') as f:
        for line in f:
            row = line.replace('\n', '')  # Get rid of newline (\n)
            row = row[1:-1]  # Get rid of '[' and ']'
            row = row.split(',')  # Split line into list
            row = [int(i) for i in row]  # Turn all number strings to an int
            tilemap.append(row)
    with open('../levels/{}/player.txt'.format(level_nr), 'r') as f:
        start = f.readline().split(',')
        start = (int(float(start[0])), int(float(start[1])))

    setup(tilemap, graphics.get_tile_values_info(64, enemies.get_enemy_info()))

    end_x, end_y = 0, 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        DISPLAY.fill((255, 255, 255))

        # Draw the tilemap
        for row in range(64):
            for column in range(64):
                tile_value = TILEMAP[row][column]
                if tile_value != 0:
                    texture = TILE_VALUES_INFO[tile_value].texture
                    texture = texture.subsurface(0, 0, 64, 64)
                    texture = pygame.transform.scale(texture, (16, 16))
                    DISPLAY.blit(texture, (column * 16, row * 16))

        end_x += 1
        if end_x > 63:
            end_x = 0
            end_y += 1
            if end_y > 63:
                end_y = 0
        pygame.draw.rect(DISPLAY, (0, 255, 0), (end_x*16, end_y*16, 16, 16))
        if TILEMAP[end_y][end_x] <= 0:
            path = pathfind(start, (end_x, end_y))
            old_x, old_y = start
            for point_x, point_y in path:
                pygame.draw.line(DISPLAY, (255, 0, 0),
                                 ((old_x + 0.5) * 16, (old_y + 0.5) * 16), ((point_x + 0.5) * 16, (point_y + 0.5) * 16))
                old_x, old_y = point_x, point_y

        pygame.display.flip()
        CLOCK.tick()

    pygame.quit()
