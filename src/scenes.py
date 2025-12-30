# scenes.py
# Base scene class for managing different game screens

import pygame
from abc import ABC, abstractmethod

class Scene(ABC):
    def __init__(self, screen, game):
        self.screen = screen
        self.game = game

    @abstractmethod
    def handle_events(self, events):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def draw(self):
        pass

    def textToScreen(self,words, font, colour, x, y):
        text=font.render(words, True, colour)
        textRect=text.get_rect()
        textRect.center=(x, y)
        self.screen.blit(text, textRect)