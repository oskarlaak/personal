class Door:
    def __init__(self, pos):
        self.pos = pos
        self.neighbours = []

    def get_neighbours(self):
        neighbour_doors = get_neighbour_doors(self.pos)
        for door in DOORS:
            if door.pos in neighbour_doors:
                self.neighbours.append(door)


def get_neighbour_doors(pos):
    # Returns a list of doors that can be reached from given location
    def get_unvisited(pos):
        all_points = visited + unvisited
        for x in range(-1, 2):  # -1, 0, 1
            for y in range(-1, 2):  # -1, 0, 1
                pos_x, pos_y = (pos[0] + x, pos[1] + y)
                if (pos_x, pos_y) not in all_points:
                    if TILEMAP[pos_y][pos_x] <= 0:
                        unvisited.append((pos_x, pos_y))
                    elif TILE_VALUES_INFO[TILEMAP[pos_y][pos_x]][0] == ('Door', 'Dynamic'):
                        visited.append((pos_x, pos_y))
                        doors_found.append((pos_x, pos_y))

    doors_found = []

    visited = [pos]
    unvisited = []
    get_unvisited(pos)

    while unvisited:  # While there is unscanned points
        current = unvisited[0]  # Get new point
        del unvisited[0]  # Delete it from unvisited bc it's about to get visited
        visited.append(current)  # Add point to visited
        get_unvisited(current)  # Scan new points from that location

    return doors_found


def get_doors():
    doors = []
    for row in range(len(TILEMAP)):
        for column in range(len(TILEMAP[row])):
            if TILE_VALUES_INFO[TILEMAP[row][column]][0] == ('Door', 'Dynamic'):
                doors.append(Door((column, row)))
    return doors


def a_star(start, end, tilemap):
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
                point_x, point_y = path[-1]
                neighbours = []
                for x in range(-1, 2):  # -1, 0, 1
                    for y in range(-1, 2):  # -1, 0, 1
                        pos = (point_x + x, point_y + y)
                        if pos in visited and pos not in path:
                            neighbours.append(pos)
                if not neighbours:
                    # Delete that point from path and visited and find new neighbour points
                    del path[-1]
                    del visited[visited.index((point_x, point_y))]
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
        all_points = visited + unvisited
        for x in range(-1, 2):  # -1, 0, 1
            for y in range(-1, 2):  # -1, 0, 1
                pos_x, pos_y = (pos[0] + x, pos[1] + y)
                if (pos_x, pos_y) not in all_points and tilemap[pos_y][pos_x] <= 0:
                    unvisited.append((pos_x, pos_y))
                    points.append(Point((pos_x, pos_y)))

    end_value = tilemap[end[1]][end[0]]  # Remember end value
    tilemap[end[1]][end[0]] = 0  # Modify tilemap

    points = []  # List storing Point class objects

    visited = [start]  # Points that have been visited
    unvisited = []  # Unvisited points that can be visited next step
    current = start  # Stores current point pos

    while visited[-1] != end:  # Quits if end position is in visited
        get_unvisited(current)  # Get new unvisited options
        if not unvisited:  # If path cannot be created
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

    tilemap[end[1]][end[0]] = end_value  # Change back tilemap
    return get_path()


def squared_dist(from_, to):
    return (from_[0] - to[0])**2 + (from_[1] - to[1])**2


def pathfind(start, end, tilemap):
    start_doors = get_neighbour_doors(start)
    end_doors = get_neighbour_doors(end)
    if start_doors == end_doors:
        return a_star(start, end, tilemap)

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
            door = doors_path[-1]
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
        path += a_star(old, point.pos, tilemap)
        old = point.pos
    path += a_star(old, end, tilemap)

    return path


if __name__ == '__main__':
    import raycasting.main.tilevaluesinfo as tilevaluesinfo
    import raycasting.main.raycaster as raycaster
    import pygame
    from pygame.locals import *

    pygame.init()
    DISPLAY = pygame.display.set_mode((1024, 1024))
    CLOCK = pygame.time.Clock()

    TILE_VALUES_INFO = tilevaluesinfo.get(64)[0]
    TILEMAP = raycaster.load_level(2, TILE_VALUES_INFO)[2]  # <-- We only need tilemap

    DOORS = get_doors()
    for door in DOORS:
        door.get_neighbours()

    start = (34, 54)
    end = (55, 45)

    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        DISPLAY.fill((255, 255, 255))

        # Draw the actual tilemap
        for row in range(64):
            for column in range(64):
                tile_value = TILEMAP[row][column]
                if tile_value != 0:
                    texture = TILE_VALUES_INFO[tile_value][1]  # Get the texture
                    texture = texture.subsurface(0, 0, 64, 64)
                    texture = pygame.transform.scale(texture, (16, 16))
                    DISPLAY.blit(texture, (column * 16, row * 16))

        # Draw path in red
        path = pathfind(start, end, TILEMAP)
        old_x, old_y = start
        for point_x, point_y in path:
            pygame.draw.line(DISPLAY, (255, 0, 0), ((old_x+.5) * 16, (old_y+.5) * 16), ((point_x+.5) * 16, (point_y+.5) * 16))
            old_x, old_y = point_x, point_y

        pygame.display.flip()
        CLOCK.tick()

    pygame.quit()
