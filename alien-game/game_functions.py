import sys
import pygame
from bullet import Bullet
from alien import Alien
from time import sleep
try:
    from pynput.keyboard import Controller, Key
except:
    pass

def check_events(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets, exit_button, pause_button):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stats.sys_exit()
        elif event.type == pygame.KEYDOWN:
            check_keydown_events(event, ship, ai_settings, screen, stats, sb, play_button, aliens, bullets)
        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ship)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            check_exit_button(stats, mouse_x, mouse_y, exit_button)
            check_play_button(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets, mouse_x, mouse_y)
            check_pause_button(stats, mouse_x, mouse_y, pause_button)


def check_keydown_events(event, ship, ai_settings, screen, stats, sb, play_button, aliens, bullets):
    if event.key == pygame.K_p:
        start_game(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets)
    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
        ship.moving_right = True
    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
        ship.moving_left = True
    if event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
        fire_bullet(ai_settings, screen, ship, bullets)
    if event.key == pygame.K_ESCAPE:
        stats.sys_exit()
    if event.key == pygame.K_PAUSE:
        if stats.game_active:
            stats.game_active = False
            stats.pausing = True
        else:
            stats.game_active = True
            stats.pausing = False


def check_keyup_events(event, ship):
    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
        ship.moving_right = False
    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
        ship.moving_left = False


def check_exit_button(stats, mouse_x, mouse_y, exit_button):
    if exit_button.rect.collidepoint(mouse_x, mouse_y) and (not stats.game_active):
        stats.sys_exit()


def check_pause_button(stats, mouse_x, mouse_y, pause_button):
    if pause_button.rect.collidepoint(mouse_x, mouse_y) and stats.game_active:
        stats.game_active = False
        stats.pausing = True


def check_play_button(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets, mouse_x, mouse_y):
    if play_button.rect.collidepoint(mouse_x, mouse_y) and not stats.game_active and not stats.pausing:
        start_game(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets)
    if stats.pausing:
        stats.game_active = True
        stats.pausing = False


def start_game(ai_settings, screen, stats, sb, play_button, ship, aliens, bullets):
    ai_settings.initialize_dynamic_settings()
    stats.reset_stats()
    stats.game_active = True
    
    sb.prep_score()
    sb.prep_high_score()
    sb.prep_level()
    sb.prep_ships()
    
    aliens.empty()
    bullets.empty()
    
    create_fleet(ai_settings, screen, ship, aliens)
    ship.center_ship()
    sb.show_score()


def set_english_mode():
    """
    此函数针对输入法，游戏开始以后，输入法会隐藏，且保持在中文模式。
    中文模式下无法进行按键操作，所以需要按shift切换为英文模式。
    下面keyboard.type(...)可能会有类型错误，不用管它
    """
    try:
        keyboard = Controller()
        keyboard.type([Key.shift_l])
        del keyboard
    except:
        pass


def update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button, exit_button, pause_button):
    screen.fill(ai_settings.bg_color)
    for bullet in bullets.sprites():
        bullet.draw_bullet()
    ship.blitme()
    aliens.draw(screen)
    sb.show_score()
    if stats.pausing:
        play_button.prep_msg('Continue')
    else:
        play_button.prep_msg('Play')
    if not stats.game_active:
        play_button.draw_button()
        exit_button.draw_button()
    else:
        pause_button.draw_button()
    pygame.display.flip()


def update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets):
    bullets.update()
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullets.remove(bullet)
    check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets)


def check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets):
    collisions = pygame.sprite.groupcollide(bullets, aliens, True, True)
    if collisions:
        for aliens in collisions.values():
            stats.score += ai_settings.alien_points * len(aliens)
            sb.prep_score()
        check_high_score(stats, sb)
    if len(aliens) == 0:
        bullets.empty()
        ai_settings.increase_speed()
        stats.level += 1
        sb.prep_level()
        create_fleet(ai_settings, screen, ship, aliens)


def check_high_score(stats, sb):
    if stats.score > stats.high_score:
        stats.high_score = stats.score
        sb.prep_high_score()


def fire_bullet(ai_settings, screen, ship, bullets):
    if len(bullets) < ai_settings.bullets_allowed:
        new_bullet = Bullet(ai_settings, screen, ship)
        bullets.add(new_bullet)


def get_numbers_aliens_x(ai_settings, alien_width):
    available_space_x = ai_settings.screen_width - 4 * alien_width
    number_aliens_x = int(available_space_x / (2 * alien_width))
    return number_aliens_x


def get_number_rows(ai_settings, ship_height, alien_height):
    available_space_y = (ai_settings.screen_height - (3 * alien_height) - ship_height)
    number_rows = int(available_space_y / (2 * alien_height))
    return number_rows


def create_alien(ai_settings, screen, aliens, alien_number, row_number):
    alien = Alien(ai_settings, screen)
    alien_width = alien.rect.width
    alien.x = alien_width + 2 * alien_width * alien_number
    alien.rect.x = alien.x
    alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
    aliens.add(alien)


def create_fleet(ai_settings, screen, ship, aliens):
    alien = Alien(ai_settings, screen)
    alien_width = alien.rect.width
    number_aliens_x = get_numbers_aliens_x(ai_settings, alien_width)
    number_rows = get_number_rows(ai_settings, ship.rect.height, alien.rect.height)
    
    for row_number in range(number_rows):
        for alien_number in range(number_aliens_x):
            create_alien(ai_settings, screen, aliens, alien_number, row_number)


def update_aliens(ai_settings, stats, sb, screen, ship, aliens, bullets):
    check_fleet_edges(ai_settings, aliens)
    aliens.update()
    if pygame.sprite.spritecollideany(ship, aliens):
        ship_hit(ai_settings, stats, sb, screen, ship, aliens, bullets)
    check_aliens_bottom(ai_settings, stats, sb, screen, ship, aliens, bullets)


def check_fleet_edges(ai_settings, aliens):
    for alien in aliens.sprites():
        if alien.check_edges():
            change_fleet_direction(ai_settings, aliens)
            break


def change_fleet_direction(ai_settings, aliens):
    for alien in aliens.sprites():
        alien.rect.y += ai_settings.fleet_drop_speed
    ai_settings.fleet_direction *= -1


def ship_hit(ai_settings, stats, sb, screen, ship, aliens, bullets):
    if stats.ships_left > 0:
        stats.ships_left -= 1
        sb.prep_ships()
        aliens.empty()
        bullets.empty()
        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()
        sleep(0.5)
    else:
        stats.game_active = False


def check_aliens_bottom(ai_settings, stats, sb, screen, ship, aliens, bullets):
    screen_rect = screen.get_rect()
    for alien in aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            ship_hit(ai_settings, stats, sb, screen, ship, aliens, bullets)
            break


def reset_high_score():
    file = open('data/high_score.txt', 'w+')
    file.write('0')
    file.close()
