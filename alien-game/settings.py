import json


class Settings:
    def __init__(self):
        try:
            self.settings_file = open('data/settings.json', 'r+')
        except FileNotFoundError:
            self.settings_file = open('data/settings.json', 'w+')
            self.settings_file.write('[0.7, 3, 1.15, 3, 15, 3, 0.2, 10, 50, 1.1]')
        try:
            self.settings_data = json.load(self.settings_file)
        except json.JSONDecodeError:
            self.settings_file.close()
            self.settings_file = open('data/settings.json', 'w+')
            self.settings_file.write('[0.7, 3, 1.15, 3, 15, 3, 0.2, 10, 50, 1.1]')
            self.settings_data = json.load(self.settings_file)
        #self.settings_file.close()
        self.screen_width = 1200
        self.screen_height = 700
        self.bg_color = (230, 230, 230)
        self.caption = "Alien Invasion"
        
        self.ship_speed_factor = self.settings_data[0]
        self.ship_limit = self.settings_data[1]
        
        self.bullet_speed_factor = self.settings_data[2]
        self.bullet_width = self.settings_data[3]
        self.bullet_height = self.settings_data[4]
        self.bullet_color = 60, 60, 60
        self.bullets_allowed = self.settings_data[5]
        
        self.alien_speed_factor = self.settings_data[6]
        self.fleet_drop_speed = self.settings_data[7]
        self.fleet_direction = 1
        self.alien_points = self.settings_data[8]
        
        self.speedup_scale = self.settings_data[9]
        self.score_scale = 1.5
        
        self.initialize_dynamic_settings()
    
    def initialize_dynamic_settings(self):
        self.ship_speed_factor = self.settings_data[0]
        self.bullet_speed_factor = self.settings_data[2]
        self.alien_speed_factor = self.settings_data[6]
        self.alien_points = self.settings_data[8]
        
        self.fleet_direction = 1
    
    def increase_speed(self):
        self.ship_speed_factor *= self.speedup_scale
        self.bullet_speed_factor *= self.speedup_scale
        self.alien_speed_factor *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)

if __name__ == '__main__':
    settings=Settings()