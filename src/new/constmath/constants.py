from collections import namedtuple

Point2 = namedtuple("Point2", "x y")

SIZE = (1920, 1080)
FPS = (60)

STEP = 1

#wall color
WALL = (255, 255, 255)
#terminal color
TERMINAL =  (255, 255, 255)
#floor color
FLOOR = (25, 25, 100)
#ceeling color
CEILING = (25, 25, 25)
#cubicle color
CUBICLE = (255, 255, 255)
#cubicle line color
CUBICLE_LINE = (0, 0, 255)
#stairs
DOOR = (255, 165, 0)
#shops colors
PROSTBUY = (180, 50, 50)
CAFETERIA = (50, 180, 50)
MILBAY = (50, 50, 180)

FPS_LV = (255, 0, 0)

SPARED = (0, 0, 255)
ENEMY = (255, 0, 0)
BOSS = (0, 255, 0)   
ITEMS = (30, 255, 30)

ASCII_CHARS = " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


STEPSIZE = 0.035          
DEG_STEP = 1