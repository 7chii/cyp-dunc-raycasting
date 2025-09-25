from collections import namedtuple

Point2 = namedtuple("Point2", "x y")

SIZE = (1920, 1080)
FPS = (60)

STEP = 1
WALL = (255, 255, 255)
FLOOR = (25, 25, 100)
CEILING = (25, 25, 25)
CUBICLE = (255, 255, 255)
CUBICLE_LINE = (0, 0, 255)

SPARED = (0, 0, 255)
ENEMY = (255, 0, 0)
BOSS = (0, 255, 0)   
ITEMS = (30, 255, 30)

ASCII_CHARS = " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


STEPSIZE = 0.035          
DEG_STEP = 1