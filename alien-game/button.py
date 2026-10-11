import pygame.font


class Button:
    def __init__(self, screen, msg, centerx=None, centery=None, width=150, height=50, font_size=45):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        
        self.width, self.height = width, height
        self.button_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.SysFont(None, font_size)
        
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.centerx = self.screen_rect.centerx if centerx == None else centerx
        self.rect.centery = self.screen_rect.centery if centery == None else centery
        
        self.msg = msg
        
        self.prep_msg(msg)
    
    def prep_msg(self, msg=None):
        self.msg_image = self.font.render(msg if msg else self.msg, True, self.text_color, self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center
    
    def draw_button(self):
        self.screen.fill(self.button_color, self.rect)
        self.screen.blit(self.msg_image, self.msg_image_rect)
