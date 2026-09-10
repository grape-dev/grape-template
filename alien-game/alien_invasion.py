import pygame
from pygame.sprite import Group

from settings import Settings
from ship import Ship
import game_functions as gf
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard


def run_game():
    ai_settings = Settings()
    pygame.init()
    screen = pygame.display.set_mode((ai_settings.screen_width, ai_settings.screen_height))
    pygame.display.set_caption(ai_settings.caption)
    
    ship = Ship(ai_settings, screen)
    stats = GameStats(ai_settings)
    sb = Scoreboard(ai_settings, screen, stats)
    bullets = Group()
    aliens = Group()
    play_button = Button(screen, 'Play', centery=screen.get_rect().centery - 30)
    exit_button = Button(screen, 'Exit', centery=screen.get_rect().centery + 30)
    pause_button = Button(screen, 'Pause', centerx=screen.get_rect().right - 70,
                          centery=sb.level_rect.bottom + 30, width=100, height=40, font_size=40)
    
    gf.set_english_mode()
    gf.create_fleet(ai_settings, screen, ship, aliens)
    
    while True:
        gf.check_events(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets, exit_button, pause_button)
        if stats.game_active:
            ship.update()
            gf.update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets)
            gf.update_aliens(ai_settings, stats, sb, screen, ship, aliens, bullets)
        gf.update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button, exit_button, pause_button)


if __name__ == '__main__':
    run_game()
