import sys


class GameStats():
    def __init__(self, ai_settings):
        self.ai_settings = ai_settings
        self.game_active = False
        self.pausing = False
        self.load_high_score()
        self.reset_stats()
    
    def reset_stats(self):
        self.ships_left = self.ai_settings.ship_limit
        self.score = 0
        self.level = 1
    
    def load_high_score(self):
        try:
            self.high_score_file = open('data/high_score.txt', 'r+')
        except FileNotFoundError:
            self.high_score_file = open('data/high_score.txt', 'w+')
            self.high_score_file.write('0')
            self.high_score_file.close()
            self.high_score_file = open('data/high_score.txt', 'r+')
        self.high_score = int(self.high_score_file.read())
        self.high_score_file.close()
    
    def sys_exit(self):
        self.high_score_file = open('data/high_score.txt', 'w+')
        self.high_score_file.write(str(self.high_score))
        self.ai_settings.settings_file.close()
        self.high_score_file.close()
        sys.exit()
