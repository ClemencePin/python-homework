"""T2 – Boids : le code de départ (étape 0).

D'après le TP « boids » de Thierry Parmentelat (flotpython), réécrit pour le
cours AP Python et pour arcade 3.

Lancez-le avec :  uv run boids.py
Testez-le avec :  uv run pytest
"""

import math
import random
from pathlib import Path

import arcade

WIDTH, HEIGHT = 800, 800
BACKGROUND = arcade.color.ALMOND

# Les images, cherchées à côté de ce fichier, d'où qu'on le lance.
HERE = Path(__file__).parent
ARROW = HERE / "media" / "arrow.png"
OBSTACLE = HERE / "media" / "obstacle.png"
SKY = HERE / "media" / "sky_2.jpg"  # le décor (étape 9)

SPEED = 100  # pixels par seconde (étape 2)
TURN_SPEED = 180  # degrés par seconde, tant qu'une flèche est enfoncée (étape 5)
NOISE = 3  # écart maximal du cap à chaque mise à jour, en degrés (étape 5)
N_BOIDS = 20  # (étape 4)
GRID = 10  # GRID × GRID obstacles (étape 6)
RADIUS = 30  # rayon de détection des voisins, en pixels (étapes 7 et 8)


# --- les objets du jeu -------------------------------------------------------
# Ces classes et fonctions sont vérifiées par les tests (tests/test_boids.py) :
# gardez leur nom et leurs paramètres.
#
# Chaque `raise NotImplementedError("étape …")` est un trou à remplir. S'il est
# atteint, le programme s'arrête net, avec ce message : il dit à quelle étape
# écrire ce morceau. Quand vous y arrivez, effacez la ligne et écrivez votre code.
# À l'étape 0, la fenêtre n'utilise encore aucune de ces classes : rien ne casse.


class Boid(arcade.Sprite):
    """Un oiseau : une flèche qui avance dans la direction où elle pointe."""

    def __init__(self, x, y, angle, speed=SPEED, others=None):
        super().__init__(ARROW, center_x=x, center_y=y, angle=angle)
        self.speed = speed
        self.others = others

    def update(self, delta_time=1 / 60, *args, **kwargs):
        """Appelée par arcade (via la SpriteList) à chaque mise à jour."""
        others = args[0] if args else kwargs.get("others", self.others)
        self.angle += getattr(self, "turning", 0) * TURN_SPEED * delta_time
        rad = math.radians(self.angle)


        self.angle += random.uniform(-NOISE, NOISE)

        dx, dy = 0, 0

        if others is not None:
            dx, dy = self.separation(others)

        self.center_x += self.speed * delta_time * math.cos(rad) + dx
        self.center_y -= self.speed * delta_time * math.sin(rad)
        self.center_y += dy

        self.center_x = self.center_x % WIDTH
        self.center_y = self.center_y % HEIGHT
        


        if others is not None :
            if self.neighbours(others):
                self.alpha = 50
            else:
                self.alpha = 255

    def neighbours(self, others, radius=RADIUS):
        """Les objets de `others` à moins de `radius` pixels, sauf soi-même."""
        voisins = []
        for other in others:
            if other is self:
                continue
            distance = math.dist(self.position, other.position)
            if distance < radius:
                voisins.append(other)
        return voisins

    def separation(self, others, radius=RADIUS):
        """Le déplacement (dx, dy) qui écarte le boid de ses voisins."""
        dx = 0
        dy = 0

        for other in others:
            if other is self:
                continue

            vx = self.center_x - other.center_x
            vy = self.center_y - other.center_y

            d = math.sqrt(vx**2 + vy**2)

            if 0 < d < radius:
                facteur = 0.5 * (1 - d / radius)

                dx += vx * facteur
                dy += vy * facteur

        return (dx, dy)


class Obstacle(arcade.Sprite):
    """Un obstacle immobile."""

    def __init__(self, x, y):
        super().__init__(OBSTACLE, center_x=x, center_y=y)


def random_boids(n, others=None):
    """n boids placés et orientés au hasard, qui évitent tous `others`."""
    boids = []
    for i in range(n):
        x = random.uniform(0,WIDTH)
        y = random.uniform(0,HEIGHT)
        angle = random.uniform(-180,180)
        boids.append(Boid(x,y,angle))
    return boids


def obstacle_grid(n):
    """n × n obstacles régulièrement espacés, au centre de leur carré."""
    obstacles = []
    intervalle_x = WIDTH / n
    intervalle_y = HEIGHT / n
    for i in range(n):
        for j in range(n):
            center_x = (i+0.5)*intervalle_x
            center_y = (j+0.5)*intervalle_y
            obstacles.append(Obstacle(center_x, center_y))
    return obstacles


# --- la fenêtre ---------------------------------------------------------------


class MyWindow(arcade.Window):
    def __init__(self):
        # d'abord, ce que fait toute fenêtre d'arcade : s'ouvrir, en WIDTH × HEIGHT
        # pixels, avec « Boids » pour titre (super() : on y revient en séance)
        super().__init__(WIDTH, HEIGHT, "Boids")
        self.background_color = BACKGROUND  # la couleur que self.clear() étale

        # pour l'instant, un simple Sprite : une image posée en (100, 100),
        # comptés depuis le coin en bas à gauche
        #boid = Boid(100, 100, -30)
        # une SpriteList : une liste de sprites, qu'arcade dessine d'un coup
        self.boids = arcade.SpriteList()
        for boid in random_boids(N_BOIDS) :
            self.boids.append(boid)

        self.turn = 0

        self.obstacles = arcade.SpriteList()

        for obstacle in obstacle_grid(GRID):
            self.obstacles.append(obstacle)

        self.sky = arcade.SpriteList()
        sky = arcade.Sprite(SKY, center_x=WIDTH / 2, center_y=HEIGHT / 2)

        sky.width = WIDTH
        sky.height = HEIGHT

        self.sky.append(sky)
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT :
            self.turn = -1
        elif key == arcade.key.RIGHT :
            self.turn = 1

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.turn = 0
    
    def on_update(self, delta_time):
        for boid in self.boids :
            boid.angle += self.turn * delta_time * TURN_SPEED
        others = list(self.boids) + list(self.obstacles)
        self.boids.update(delta_time, others)
        
    def on_draw(self):
        self.clear()
        self.sky.draw()
        self.boids.draw()
        self.obstacles.draw()

def main():
    MyWindow()
    arcade.run()


# Ce bloc ne s'exécute que si l'on lance ce fichier (uv run boids.py),
# pas quand un autre fichier fait `import boids` (les tests, par ex.).
if __name__ == "__main__":
    main()
