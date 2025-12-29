# game_screen.py
# Main game screen scene

import pygame
import pymunk

from scenes import Scene
from settings import *

class Ball:
    def __init__(self, space, x, y):
        self.radius = BALL_RADIUS
        mass = 1
        moment = pymunk.moment_for_circle(mass, 0, self.radius)
        
        # Physics Body
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.body.velocity = (300, -300)
        
        # Physics Shape
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = 1.0  # Perfect bounce
        self.shape.friction = 0.0
        
        space.add(self.body, self.shape)

    def draw(self, screen):
        pos = self.body.position
        pygame.draw.circle(screen, RED, (int(pos.x), int(pos.y)), self.radius)
        
class Paddle:
    def __init__(self, space, x, y):
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        
        # Kinematic body
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = (x, y)
        
        # 1. Define Convex Vertices
        # We create a "curved" top by calculating points along an arc
        self.vertices = []
        num_points = 8
        curve_height = 15  # How much the middle sticks up
        
        # Bottom edge points (flat)
        self.vertices.append((-self.width // 2, self.height // 2))
        
        # Top edge points (curved)
        for i in range(num_points + 1):
            rel_x = (i / num_points) - 0.5  # -0.5 to 0.5
            px = rel_x * self.width
            # Parabolic curve: y = height * (1 - 4x^2)
            py = -self.height // 2 - (curve_height * (1 - 4 * (rel_x**2)))
            self.vertices.append((px, py))
        self.vertices.append((self.width // 2, self.height // 2))

        # 2. Create the Shape
        self.shape = pymunk.Poly(self.body, self.vertices)
        self.shape.elasticity = 1.1  # Slight boost to keep ball fast
        self.shape.friction = 0.3    # Friction allows "spinning" the ball on hit
        
        space.add(self.body, self.shape)

    def update(self, target_x):
        # Update position
        self.body.position = (target_x, self.body.position.y)

    def draw(self, screen):
        # Convert Pymunk vertices to world coordinates for Pygame
        ps = [self.body.local_to_world(v) for v in self.vertices]
        # Draw the convex polygon
        pygame.draw.polygon(screen, WHITE, ps)


class GameScreen(Scene):
    def __init__(self, screen, game):
        super().__init__(screen, game)
        self.audio_analyzer = game.audio_analyzer

        # Initialize Pymunk Space
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

        # Instantiate Classes
        self.paddle = Paddle(self.space, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        self.ball = Ball(self.space, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Add static boundaries (walls)
        self._setup_walls()

        # Initialize lives
        self.lives = 3

    def reset_ball(self):
        self.ball.body.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.ball.body.velocity = (300, -300)

    def _setup_walls(self):
        walls = [
            pymunk.Segment(self.space.static_body, (0, 0), (SCREEN_WIDTH, 0), 5),      # Top
            pymunk.Segment(self.space.static_body, (0, 0), (0, SCREEN_HEIGHT), 5),     # Left
            pymunk.Segment(self.space.static_body, (SCREEN_WIDTH, 0), (SCREEN_WIDTH, SCREEN_HEIGHT), 5) # Right
        ]
        for wall in walls:
            wall.elasticity = 1.0
            self.space.add(wall)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.change_scene("title")


    def update(self, dt):
        # 1. Update Paddle position via Audio Note
        _, _, note_index = self.audio_analyzer.getNoteIndex()
        target_x = SCREEN_WIDTH * (note_index % 12) / 12

        target_x, _ = pygame.mouse.get_pos()

        self.paddle.update(target_x)

        # 2. Advance Physics
        self.space.step(1/60.0)

        # 3. Game Over check
        if self.ball.body.position.y > SCREEN_HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                self.reset_ball()
            else:
                self.game.change_scene("title")

    def draw(self):
        self.screen.fill(BLACK)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        
        # Draw lives
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(text, (10, 10))