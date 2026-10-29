"""Les tests du T2. Lancez-les avec : uv run pytest

Au début, presque tout est rouge : c'est normal. Chaque étape de l'énoncé
fait passer quelques tests au vert.
"""

import arcade
import pytest

import boids


@pytest.fixture(autouse=True)
def sans_bruit(monkeypatch):
    # Le bruit sur le cap rend les déplacements imprévisibles : on le coupe,
    # sauf dans test_bruit_sur_le_cap, qui le remet.
    monkeypatch.setattr(boids, "NOISE", 0)


# --- étape 0 : importer boids.py ne doit rien lancer -------------------------


def test_import_n_ouvre_pas_de_fenetre():
    # Si ce test échoue, c'est que du code tourne au moment de l'import :
    # la fenêtre doit être créée dans main(), appelée sous `if __name__ == ...`.
    with pytest.raises(RuntimeError):
        arcade.get_window()


# --- étape 2 : le boid avance ------------------------------------------------


def test_boid_est_un_sprite():
    b = boids.Boid(100, 200, 0)
    assert isinstance(b, arcade.Sprite)
    assert b.position == (100, 200)
    assert b.speed == boids.SPEED


def test_boid_garde_sa_vitesse():
    assert boids.Boid(100, 200, 0, speed=42).speed == 42


def test_boid_avance_vers_la_droite():
    b = boids.Boid(100, 200, 0, speed=60)
    b.update(0.5)  # une demi-seconde à 60 pixels par seconde
    assert b.center_x == pytest.approx(130)
    assert b.center_y == pytest.approx(200)


def test_boid_avance_vers_le_bas():
    # dans arcade, l'angle tourne dans le sens des aiguilles d'une montre
    b = boids.Boid(100, 200, 90, speed=60)
    b.update(0.5)
    assert b.center_x == pytest.approx(100)
    assert b.center_y == pytest.approx(170)


def test_chaque_boid_a_sa_vitesse():
    lent, rapide = boids.Boid(100, 200, 0, speed=10), boids.Boid(100, 300, 0, speed=100)
    lent.update(1)
    rapide.update(1)
    assert lent.center_x == pytest.approx(110)
    assert rapide.center_x == pytest.approx(200)


# --- étape 3 : en circuit fermé ----------------------------------------------


def test_boid_sort_a_droite_rentre_a_gauche():
    b = boids.Boid(boids.WIDTH - 10, 200, 0, speed=60)
    b.update(0.5)
    assert b.center_x == pytest.approx(20)


def test_boid_sort_en_bas_rentre_en_haut():
    b = boids.Boid(100, 10, 90, speed=60)
    b.update(0.5)
    assert b.center_y == pytest.approx(boids.HEIGHT - 20)


# --- étape 4 : plusieurs boids -----------------------------------------------


def test_random_boids():
    nuee = boids.random_boids(15)
    assert len(nuee) == 15
    for b in nuee:
        assert isinstance(b, boids.Boid)
        assert 0 <= b.center_x <= boids.WIDTH
        assert 0 <= b.center_y <= boids.HEIGHT
    assert len({b.position for b in nuee}) > 1  # pas tous au même endroit


# --- étape 5 : le clavier et le bruit ----------------------------------------


def test_turning_tourne_a_droite():
    b = boids.Boid(100, 200, 0, speed=0)
    b.turning = 1
    b.update(0.5)
    assert b.angle == pytest.approx(boids.TURN_SPEED / 2)


def test_turning_zero_garde_le_cap():
    b = boids.Boid(100, 200, 30, speed=0)
    b.update(0.5)
    assert b.angle == pytest.approx(30)


def test_bruit_sur_le_cap(monkeypatch):
    monkeypatch.setattr(boids, "NOISE", 5)
    caps = set()
    for _ in range(20):
        b = boids.Boid(100, 200, 30, speed=0)
        b.update(1 / 60)
        assert 25 <= b.angle <= 35
        caps.add(b.angle)
    assert len(caps) > 1  # le cap change, au hasard


# --- étape 6 : les obstacles -------------------------------------------------


def test_obstacle_est_un_sprite():
    o = boids.Obstacle(40, 80)
    assert isinstance(o, arcade.Sprite)
    assert not isinstance(o, boids.Boid)
    assert o.position == (40, 80)


def test_obstacle_grid():
    grille = boids.obstacle_grid(10)
    assert len(grille) == 100
    assert all(isinstance(o, boids.Obstacle) for o in grille)
    xs = sorted({o.center_x for o in grille})
    assert xs[0] == pytest.approx(boids.WIDTH / 20)
    assert xs[1] - xs[0] == pytest.approx(boids.WIDTH / 10)


# --- étape 7 : les voisins ---------------------------------------------------


def test_neighbours():
    b = boids.Boid(100, 100, 0)
    proche = boids.Obstacle(110, 100)
    loin = boids.Obstacle(300, 100)
    assert b.neighbours([b, proche, loin], radius=30) == [proche]


# --- étape 8 : la séparation -------------------------------------------------


def test_separation_sans_voisin():
    b = boids.Boid(100, 100, 0)
    assert b.separation([boids.Obstacle(300, 300)], radius=40) == (0, 0)


def test_separation_repousse():
    # un obstacle à gauche, à mi-rayon : le boid est poussé vers la droite
    b = boids.Boid(100, 100, 0)
    dx, dy = b.separation([boids.Obstacle(80, 100)], radius=40)
    assert dx == pytest.approx(5)  # 20 × (1 - 20/40) / 2
    assert dy == pytest.approx(0)


def test_separation_s_additionne():
    b = boids.Boid(100, 100, 0)
    gauche, droite = boids.Obstacle(80, 100), boids.Obstacle(120, 100)
    dx, dy = b.separation([gauche, droite], radius=40)
    assert dx == pytest.approx(0)
    assert dy == pytest.approx(0)


def test_update_evite_ses_voisins():
    obstacle = boids.Obstacle(100, 90)
    b = boids.Boid(100, 100, 0, speed=0, others=[obstacle])
    b.update(1 / 60)
    assert b.center_y > 100  # repoussé vers le haut, loin de l'obstacle
