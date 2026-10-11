import pygame
from time import sleep
import json

import alien_invasion
from button import Button


if True:
    settings_on = False
    settings_str = ('ship speed factor',
                    'ship limit',
                    'bullet speed factor',
                    'bullet width',
                    'bullet height',
                    'bullets allowed',
                    'alien speed factor',
                    'alien drop speed',
                    'alien points',
                    'speedup scale',
                    'history high score')
    value_points = (0.1, 1, 0.05, 1, 1, 1, 0.05, 5, 5, 0.05)
    max_points = (3, 5, 2.5, 15, 30, 10, 3, 30, 150, 1.5)
    min_points = (0.3, 1, 0.5, 1, 1, 1, 0.05, 5, 20, 1.05)
    default_points = (0.7, 3, 1.15, 3, 15, 3, 0.2, 10, 50, 1.1)
    try:
        settings_file = open('data/settings.json', 'r+')
    except FileNotFoundError:
        settings_file=open('data/settings.json','w+')
        settings_file.write('[0.7, 3, 1.15, 3, 15, 3, 0.2, 10, 50, 1.1]')
    settings_data = json.load(settings_file)[:10]
    try:
        high_score_file = open('data/high_score.txt', 'r+')
    except FileNotFoundError:
        high_score_file=open('data/high_score.txt','w+')
        high_score_file.write('0')
    high_score = str(high_score_file.read())
    settings_data.append(high_score)
    high_score_file.close()
    settings_file.close()

def update_screen(screen, caption_image, caption_image_rect, start_button, exit_button,
                  settings_button, ok_button, reset_button, reset_high_score_button, settings_str_image,
                  settings_str_rect,
                  settings_value_image, settings_value_rect, add_list, remove_list, alien_image, alien_image_rect):
    global settings_on
    screen.fill((230, 230, 230))
    if not settings_on:
        screen.blit(caption_image, caption_image_rect)
        screen.blit(alien_image, alien_image_rect)
        start_button.draw_button()
        exit_button.draw_button()
        settings_button.draw_button()
    else:
        for image, rect in zip(settings_str_image, settings_str_rect):
            screen.blit(image, rect)
        for image, rect in zip(settings_value_image, settings_value_rect):
            screen.blit(image, rect)
        for button in add_list:
            button.draw_button()
        for button in remove_list:
            button.draw_button()
        ok_button.draw_button()
        reset_button.draw_button()
        reset_high_score_button.draw_button()


def prep_caption(screen, font, text='Alien Invasion'):
    caption_image = font.render(text, True, (0, 0, 0), (230, 230, 230))
    image_rect = caption_image.get_rect()
    image_rect.centerx, image_rect.y = screen.get_rect().centerx + 23, 10
    return caption_image, image_rect


def prep_settings_str(font, text_tuple, x, y, step=18):
    image_list = []
    rect_list = []
    now = 0
    for text in text_tuple:
        image = font.render(text, True, (0, 0, 0), (230, 230, 230))
        image_list.append(image)
        rect = image.get_rect()
        rect.x = x
        rect.y = y + step * now
        rect_list.append(rect)
        now += 1
    return image_list, rect_list


def check_events(start_button, exit_button, settings_button, ok_button, reset_button, reset_high_score_button, add_list,
                 remove_list, settings_value_image, settings_value_rect,):
    global settings_on, settings_data, high_score
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            raise SystemExit
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            if not settings_on:
                if start_button.rect.collidepoint(*mouse):
                    sleep(.1)
                    pygame.display.quit()
                    alien_invasion.run_game()
                if exit_button.rect.collidepoint(*mouse):
                    sleep(.1)
                    raise SystemExit
                if settings_button.rect.collidepoint(*mouse):
                    settings_on = not settings_on
            else:
                if ok_button.rect.collidepoint(*mouse):
                    settings_on = not settings_on
                if reset_button.rect.collidepoint(*mouse):
                    settings_data = list(default_points[:])
                    settings_data.append(high_score)
                    settings_file = open('data/settings.json', 'w+')
                    settings_file.write(json.dumps(settings_data[0:10]))
                    settings_file.close()
                    return prep_settings_value(pygame.font.SysFont(None, 25), settings_data, 170,
                                               10, 23)
                if reset_high_score_button.rect.collidepoint(*mouse):
                    high_score = 0
                    high_score_file = open('data/high_score.txt', 'w+')
                    high_score_file.write('0')
                    high_score_file.close()
                    settings_data[-1] = 0
                    return prep_settings_value(pygame.font.SysFont(None, 25), settings_data, 170,
                                               10, 23)
                for i in range(len(add_list)):
                    if add_list[i].rect.collidepoint(*mouse):
                        return change_settings(i, True, settings_data)
                for i in range(len(remove_list)):
                    if remove_list[i].rect.collidepoint(*mouse):
                        return change_settings(i, False, settings_data)
    mouse = pygame.mouse.get_pos()
    for button in add_list:
        change_button_color(button, mouse)
    for button in remove_list:
        change_button_color(button, mouse)
    change_button_color(start_button, mouse)
    change_button_color(exit_button, mouse)
    change_button_color(settings_button, mouse)
    change_button_color(ok_button, mouse)
    change_button_color(reset_button, mouse)
    change_button_color(reset_high_score_button, mouse)
    return settings_value_image, settings_value_rect


def change_settings(i, add: bool, settings_data):
    if add:
        if settings_data[i] < max_points[i]:
            settings_data[i] += value_points[i]
            settings_data[i] = round(settings_data[i], 2)
    if not add:
        if settings_data[i] > min_points[i]:
            settings_data[i] -= value_points[i]
            settings_data[i] = round(settings_data[i], 2)
    settings_file = open('data/settings.json', 'w+')
    settings_file.write(json.dumps(settings_data[:9]))
    settings_file.close()
    return prep_settings_value(pygame.font.SysFont(None, 25), settings_data, 170,
                               10, 23)


def change_button_color(button:Button, mouse):
    if button.rect.collidepoint(*mouse):
        button.button_color = (70, 70, 70)
        button.prep_msg()
    else:
        button.button_color = (100, 100, 100)
        button.prep_msg()


def prep_settings_value(font, text_list, x, y, step):
    image_list = []
    rect_list = []
    now = 0
    for text in text_list:
        image = font.render(str(text), True, (0, 0, 0), (230, 230, 230))
        image_list.append(image)
        rect = image.get_rect()
        rect.x = x
        rect.y = y + step * now
        rect_list.append(rect)
        now += 1
    return image_list, rect_list


def prep_settings_button(screen, number, x, y, step):
    add_list = []
    remove_list = []
    for i in range(number):
        add_button = Button(screen, '+', x, y + i * step, 20, 20, 20)
        remove_button = Button(screen, '-', x + 30, y + i * step, 20, 20, 20)
        add_list.append(add_button)
        remove_list.append(remove_button)
    return add_list, remove_list


def main():
    global settings_on, settings_str, settings_data
    
    pygame.init()
    screen = pygame.display.set_mode((300, 300), flags=pygame.NOFRAME)
    pygame.display.set_caption('Alien Invasion')
    font = pygame.font.SysFont(None, 50)
    caption_image, caption_image_rect = prep_caption(screen, font)
    alien_image = pygame.image.load('resources/alien.bmp')
    alien_image = pygame.transform.scale(alien_image, (35, 35))
    alien_image_rect = alien_image.get_rect()
    alien_image_rect.x, alien_image_rect.y = 10, 9
    
    update_mouse_event = pygame.USEREVENT + 1
    create_smart_mouse_event = pygame.USEREVENT + 2
    pygame.time.set_timer(update_mouse_event, 50)
    pygame.time.set_timer(create_smart_mouse_event, 200)
    
    start_button = Button(screen, 'Start', centery=90, width=100, height=50, font_size=50)
    settings_button = Button(screen, 'Settings', centery=160, width=160, height=50, font_size=50)
    exit_button = Button(screen, 'Exit', centery=230, width=80, height=50, font_size=50)
    reset_button = Button(screen, 'Reset settings', centerx=120, centery=280, width=170, height=30, font_size=30)
    ok_button = Button(screen, 'OK', centerx=260, centery=280, width=50, height=30, font_size=30)
    reset_high_score_button = Button(screen, 'reset', centerx=260, centery=250, width=50, height=20, font_size=20)
    
    settings_str_image, settings_str_rect = prep_settings_str(pygame.font.SysFont(None, 25), settings_str, 10, 10, 23)
    settings_value_image, settings_value_rect = prep_settings_value(pygame.font.SysFont(None, 25), settings_data, 170,
                                                                    10, 23)
    add_list, remove_list = prep_settings_button(screen, 10, 245, 18, 23)
    
    while True:
        settings_value_image, settings_value_rect = check_events(start_button, exit_button, settings_button, ok_button,
                                                                 reset_button, reset_high_score_button,
                                                                 add_list, remove_list, settings_value_image,
                                                                 settings_value_rect)
        update_screen(screen, caption_image, caption_image_rect, start_button,
                      exit_button, settings_button, ok_button, reset_button, reset_high_score_button,
                      settings_str_image,
                      settings_str_rect, settings_value_image, settings_value_rect, add_list, remove_list, alien_image,
                      alien_image_rect)
        pygame.display.flip()


if __name__ == '__main__':
    main()
