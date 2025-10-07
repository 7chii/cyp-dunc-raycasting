import dinamic.dinamic as dinamic

GRID = ()
def start_grid(saferoom):
    global GRID
    GRID = dinamic.generate_random_grid(24, 24, wall_chance=0.25, saferoom=saferoom)
    return GRID


     

assert all(len(GRID) == len(row) for row in GRID), "deve ser quadrada!"
for row in GRID:
    for val in row:
        assert isinstance(val, int), "grid com valores nao int!"