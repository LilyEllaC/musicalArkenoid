# title_screen.py
# Title screen scene

import pygame
from scenes import Scene
from settings import *

class TitleScreen(Scene):
    def __init__(self, screen, game):
        super().__init__(screen, game)
        self.font_title = pygame.font.Font(None, FONT_SIZE_TITLE)
        self.font_button = pygame.font.Font(None, FONT_SIZE_BUTTON)

        self.title_text = self.font_title.render("Music Arkanoid", True, WHITE)
        self.start_text = self.font_button.render("Press SPACE to Start", True, GREEN)
        self.tuning_text = self.font_button.render("Press T for Tuning", True, BLUE)

        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.start_rect = self.start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.tuning_rect = self.tuning_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.game.change_scene("game")
                elif event.key == pygame.K_t:
                    self.game.change_scene("tuning")

    def update(self, dt):
        pass  # No updates needed for title screen

    def draw(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.title_text, self.title_rect)
        self.screen.blit(self.start_text, self.start_rect)
        self.screen.blit(self.tuning_text, self.tuning_rect)