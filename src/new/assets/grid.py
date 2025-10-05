import dinamic.dinamic as dinamic

GRID = ()
def start_grid():
    global GRID
    GRID = dinamic.generate_random_grid(24, 24, wall_chance=0.25)
    return GRID
     

assert all(len(GRID) == len(row) for row in GRID), "Grid should be square!"
for row in GRID:
    for val in row:
        assert isinstance(val, int), "Non integer element in grid!"