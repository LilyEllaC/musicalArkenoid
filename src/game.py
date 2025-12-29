# game.py
# Main game class that manages scenes

import pygame
import pygame
from settings import *
from title_screen import TitleScreen
from game_screen import GameScreen
from tuning_screen import TuningScreen
from audio_analyzerLibrosa import LibrosaAudioAnalyzer

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Music Arkanoid")

        self.clock = pygame.time.Clock()
        self.running = True
                
        self.audio_analyzer = LibrosaAudioAnalyzer()
        
        self.scenes = {
            "title": TitleScreen(self.screen, self),
            "game": GameScreen(self.screen, self),
            "tuning": TuningScreen(self.screen, self)
        }
        self.current_scene = self.scenes["title"]

    def change_scene(self, scene_name):
        if scene_name in self.scenes:
            self.current_scene = self.scenes[scene_name]

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            self.audio_analyzer.update()
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.current_scene.handle_events(events)
            self.current_scene.update(dt)
            self.current_scene.draw()

            pygame.display.flip()

        pygame.quit()


# main.py
# Entry point for the game

from game import Game

if __name__ == "__main__":
    game = Game()
    game.run()