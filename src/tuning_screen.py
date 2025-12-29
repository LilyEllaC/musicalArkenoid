# tuning_screen.py
# Tuning screen scene for displaying microphone sound spectrum

import pygame
import numpy as np
import colorsys
from typing import Any, List
from scenes import Scene
from settings import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game import Game

class TuningScreen(Scene):
    def __init__(self, screen: pygame.Surface, game: "Game") -> None:
        super().__init__(screen, game)
        self.font_title = pygame.font.Font(None, FONT_SIZE_TITLE)
        self.font_button = pygame.font.Font(None, FONT_SIZE_BUTTON)

        self.title_text = self.font_title.render("Tuning Screen", True, WHITE)
        self.back_text = self.font_button.render("Press ESC to go back", True, GREEN)
        self.sensitivity = -40 

        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.back_rect = self.back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.audio_analyzer = game.audio_analyzer
        
        self.log_min = np.log2(self.audio_analyzer.note_freqs[0])
        self.log_max = np.log2(self.audio_analyzer.note_freqs[-1])      

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.change_scene("title")
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # + key
                    self.audio_analyzer.adjust_sensitivity(increase=True)                    
                elif event.key == pygame.K_MINUS:
                    self.audio_analyzer.adjust_sensitivity(increase=False)

                # Left/Right: Shift the frequency window (Horizontal Offset)
                elif event.key == pygame.K_LEFT:
                    # Decrement the starting frequency index/offset
                    self.audio_analyzer.adjustSpectrum(noteShift =-1)
                elif event.key == pygame.K_RIGHT:
                    # Increment the starting frequency index/offset
                    self.audio_analyzer.adjustSpectrum(noteShift =1)
                    

                # Up/Down: Change the frequency range width (Zoom/Scale)
                elif event.key == pygame.K_UP:
                    # Zoom in (decrease total width/number of octaves)
                    self.audio_analyzer.adjustSpectrum(rangeShift = 1)
                    
                    
                elif event.key == pygame.K_DOWN:
                    # Zoom out (increase total width/number of octaves)
                    self.audio_analyzer.adjustSpectrum(rangeShift = -1)
                    
                    

    def update(self, dt: float) -> None:
        pass  # No dynamic updates needed for tuning screen
    
    def adjust_sensitivity(self, increase=True):
        """Increase or decrease the dB threshold."""
        # Moving closer to 0 makes it harder to trigger (requires more volume)
        step = 2 
        if increase:
            self.sensitivity += step
        else:
            self.sensitivity -= step
    def draw(self) -> None:
        self.screen.fill(BLACK)
        self.screen.blit(self.title_text, self.title_rect)
        self.screen.blit(self.back_text, self.back_rect)

        sens_text = self.font_button.render(f"Sensitivity: {self.audio_analyzer.getSensitivity():.1f} (+/- to adjust)\n Arrow keys to adjust Range", True, WHITE)
        sens_rect = sens_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(sens_text, sens_rect)

        # Display strongest note
        strongest_note = self.audio_analyzer.getStrongestNote()
        note_text = self.font_button.render(f"Strongest Note: {strongest_note}", True, YELLOW)
        note_rect = note_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(note_text, note_rect)

        # Draw spectrum in log domain for frequencies
        max_height = 400
        maxMag = 0 + self.audio_analyzer.getSensitivity()
        minMag = maxMag-40
        scaling = max_height/(maxMag- minMag)        
        self.log_min = np.log2(self.audio_analyzer.note_freqs[0])
        self.log_max = np.log2(self.audio_analyzer.note_freqs[-1])      


        for freq, log_amp in self.audio_analyzer.getSpectrum():
            height = int((log_amp  - minMag)* scaling)
            height = max(min(height, max_height),0)
            
            # Color based on magnitude using HSV
            normalized = (log_amp - minMag) / (maxMag - minMag)
            normalized = max(0, min(1, normalized))  # Clamp to 0-1
            hue = 240 * (1 - normalized)  # 240=blue for low, 0=red for high
            r, g, b = colorsys.hsv_to_rgb(hue / 360, 1, 1)
            color = (int(r * 255), int(g * 255), int(b * 255))
            
            x_pos = self.mapFreqToX(freq)
            pygame.draw.rect(self.screen, color, (x_pos, SCREEN_HEIGHT - 100 - height, 2, height))  # Thin bars

        # Draw note labels
        # this is C3
        
        for octive in range(self.audio_analyzer.getNumOctives()):
            index = min(0+12*octive, len(self.audio_analyzer.note_names))
            note = self.audio_analyzer.note_names[index]
            freq = self.audio_analyzer.note_freqs[index]
            x_pos = self.mapFreqToX(freq)
            note_text = self.font_button.render(note, True, WHITE)
            note_rect = note_text.get_rect(center=(x_pos, SCREEN_HEIGHT - 70))
            self.screen.blit(note_text, note_rect)

        


    def mapFreqToX(self, freq: float) -> int:
        x_pos = int((np.log2(freq) - self.log_min) / (self.log_max - self.log_min) * SCREEN_WIDTH)
        return x_pos    

    