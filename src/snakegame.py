import pygame
pygame.init()
import random
import os
import sys
import pickle


#colors
WHITE = 255, 255, 255
BLACK = 0, 0, 0
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255

SESSION_FILE_NAME = 'session.bf'
SCORE_FILE_NAME = 'score.bf'

class Food(object):
    def __init__(self, surface, bulk=3):
        self.surface = surface
        self.bulk = bulk
        self.x = random.randrange(self.bulk, game.gamewidth - self.bulk)
        self.y = random.randrange(self.bulk, game.gameheight - self.bulk)
        self.color = GREEN
        self.points = 0
        self.eaten = False
        self.set_points_worth()

    def set_points_worth(self):
        self.points = 10

    def being_eaten(self, x, y):
        if self.bulk not in (1, 0):
            if x < self.x or x > self.x + self.bulk:
                return False
            if y < self.y or y > self.y + self.bulk:
                return False
            return True
        else:
            return (x, y) == (self.x, self.y)

    def has_been_eaten(self):
        self.eaten = True

    def nutritional_value(self):
        if self.points > 10:
            return 20
        return 10

    def draw(self):
        if self.bulk not in (1, 0):
            pygame.draw.rect(self.surface, self.color, (self.x, self.y,
                                                        self.bulk, self.bulk))
        else:
            self.surface.set_at((self.x, self.y), self.color)


class BaseSnake(object):

    def __init__(self, surface, startpos, color, initlength=10):
        self.surface = surface
        self.startpos = startpos
        self.initlength = initlength
        self.length = initlength
        self.body = []
        self.x, self.y = startpos
        self.dir_x = 0
        self.dir_y = -1
        self.crashed = False
        self.score = 0
        self.color = color
        self.speed = 2
    def move(self):

        self.crashed = self.check_crash(self.x + self.dir_x * self.speed,
                                        self.y + self.dir_y * self.speed)

        for i in range(0, self.speed):
            self.x += self.dir_x
            self.y += self.dir_y
            self.body.insert(0, (self.x, self.y))
            if self.length != 0 and len(self.body) > self.length:
                self.body.pop()

    def draw(self):
        for coord in self.body:
            self.surface.set_at(coord, self.color)

    def check_crash(self, x, y):
        if x >= game.gamewidth or y >= game.gameheight or x <= 0 or y <= 0:
            return True

        for player in game.players:
            if (x, y) in player.body:
                return True
        return False

    def check_ate(self, food):
        for f in food:
            if f.being_eaten(self.x, self.y):
                self.score += f.points
                self.length += f.nutritional_value()
                f.has_been_eaten()


class Player(BaseSnake):
    def __init__(self, name, controls, *args):
        self.name = name
        self.lives = 3
        self.playing = True
        self.up, self.down, self.left, self.right = controls
        BaseSnake.__init__(self, *args)

    def reset(self):
        self.body = []
        self.x, self.y = self.startpos
        self.dir_x, self.dir_y = 0, -1
        self.score = 0
        self.crashed = self.playing = True
    
    def full_reset(self):
        self.reset()
        self.length = self.initlength
        self.lives = 3

    def handle_crash(self):
        self.lives -= 1
        if self.lives > 0:
            score = self.score
            self.reset()
            self.score = score
        else:
            self.playing = False

    def handle_key(self, key):
        if key == self.up:
            if self.dir_y == 1:
                return
            self.dir_x = 0
            self.dir_y = -1
        elif key == self.down:
            if self.dir_y == -1:
                return
            self.dir_x = 0
            self.dir_y = 1
        elif key == self.left:
            if self.dir_x == 1:
                return
            self.dir_x = -1
            self.dir_y = 0
        elif key == self.right:
            if self.dir_x == -1:
                return
            self.dir_x = 1
            self.dir_y = 0

class MainApp(object):
    width = 800
    height = 600
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    bgcolor = BLACK
    running = False
    statusarea = 25
    maxfood = 1
    players = []
    food = []
    framerate = 60
    gamewidth = width
    gameheight = height - statusarea
    font = pygame.font.Font('freesansbold.ttf', 18)

    def __init__(self):
        pygame.display.set_caption('SnakeGame')
        pygame.mouse.set_visible(0)


    def add_player(self, player):
        self.players.append(player)

    def clean_food(self):
        self.food = [f for f in self.food if not f.eaten]
        if len(self.food) < self.maxfood:
            for i in range(len(self.food), self.maxfood):
                self.food.append(Food(self.screen))

    def draw_food(self):
        for f in self.food:
            f.draw()

    def draw_game_area(self):
        pygame.draw.rect(self.screen, WHITE, (0, 0, self.gamewidth, self.gameheight), 1)

    def draw_status_area(self):
        drawn_players = []
        textxpos = 0
        for player in self.players:
            lives = player.lives or 'GAME OVER'
            playerscore = "%s(%s): %sp" % (player.name, lives, player.score)
            playerstatus = self.font.render(playerscore, True, player.color)
            if drawn_players:
                textxpos += drawn_players[-1].get_size()[0] + 10
            self.screen.blit(playerstatus, (textxpos, self.gameheight + 5))
            drawn_players.append(playerstatus)

    def run(self):
        self.players = []
        p1_controls = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
        p2_controls = pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d
        player1 = Player('Player 1', p1_controls, self.screen, (self.gamewidth/2, self.gameheight/2), WHITE, 50)
        player2 = Player('Player 2', p2_controls, self.screen, (self.gamewidth/3, self.gameheight/3), RED, 50)

        self.screen.fill(BLACK)
        questiontext = [self.font.render('Press 1 for singleplayer', True, GREEN),
                        self.font.render('Press 2 for 2-player mode.', True, GREEN),
                        self.font.render('Player 1 controls: directional keys;', True, GREEN),
                        self.font.render('Player 2 controls: WSAD keys.', True, GREEN),
                        self.font.render('ESC = exit game', True, GREEN),
                        self.font.render('F1 = view high scores', True, GREEN)]

        if self.game_status_is_saved():
            text = 'Press c to continue previous game'
            questiontext.insert(-1, self.font.render(text, True, GREEN))
        
        textposx = self.width / 3
        textposy = self.height / 4
        for qi in range(0, len(questiontext)):
            question = questiontext[qi]
            self.screen.blit(question, (textposx, textposy))
            textposy += question.get_size()[1] + 5
        pygame.display.flip()

        selection_done = False
        while not selection_done:
            self.clock.tick(self.framerate)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(1)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.add_player(player1)
                        selection_done = True
                    elif event.key == pygame.K_2:
                        self.add_player(player1)
                        self.add_player(player2)
                        selection_done = True
                    elif self.game_status_is_saved() and event.key == pygame.K_c:
                        self.load_game_status()
                        return self.startgame(pause=True)
                    elif event.key == pygame.K_F1:
                        return self.score_page()
                    elif event.key == pygame.K_ESCAPE:
                        sys.exit(1)
        self.player_names_screen()
        return self.startgame()

    def game_status_is_saved(self):
        return os.path.isfile(SESSION_FILE_NAME)
    
    def save_game_status(self):
        data = {'players': [], 'food': []}
        for player in self.players:
            pdata = {'name': player.name,
                     'controls': (player.up, player.down, player.left, player.right),
                     'startpos': player.startpos,
                     'color': player.color,
                     'initlength': player.initlength,
                     'length': player.length,
                     'score': player.score,
                     'body': player.body,
                     'dir_x': player.dir_x,
                     'dir_y': player.dir_y,
                     'lives': player.lives,
                     'x': player.x,
                     'y': player.y,
                     'crashed': player.crashed,
                     'playing': player.playing,
                     }
            data['players'].append(pdata)
        
        for food in self.food:
            fdata = {'x': food.x,
                     'y': food.y,
                     'bulk': food.bulk,
                     'color': food.color,
                     'points': food.points,
                     'eaten': food.eaten,
                     }
            data['food'].append(fdata)
        
        session_file = open(SESSION_FILE_NAME, 'wb')
        pickle.dump(data, session_file)
    
    def load_game_status(self):
        session_file = open(SESSION_FILE_NAME, 'rb')
        data = pickle.load(session_file)
        for player in data['players']:
            pobj = Player(player['name'], player['controls'], self.screen, player['startpos'], player['color'], player['initlength'])
            pobj.length = player['length']
            pobj.score = player['score']
            pobj.body = player['body']
            pobj.dir_x = player['dir_x']
            pobj.dir_y = player['dir_y']
            pobj.lives = player['lives']
            pobj.x = player['x']
            pobj.y = player['y']
            pobj.crashed = player['crashed']
            pobj.playing = player['playing']
            self.add_player(pobj)

        for food in data['food']:
            fobj = Food(self.screen)
            fobj.x = food['x']
            fobj.y = food['y']
            fobj.bulk = food['bulk']
            fobj.color = food['color']
            fobj.points = food['points']
            fobj.eaten = food['eaten']
            self.food.append(fobj)

    def draw_players(self):
        for player in self.players:
            if not player.playing:
                continue
            player.draw()
            player.check_ate(self.food)
            player.move()
            if player.crashed:
                player.handle_crash()

        if not [player for player in self.players if player.playing]:
            self.running = False

    def pause(self):
        paused = True
        text = self.font.render('PAUSED - press p to resume', True, GREEN)
        textposx = (self.gamewidth / 2) - (text.get_size()[0] / 2)
        textposy = (self.gameheight / 4) - (text.get_size()[1] / 2)
        self.screen.blit(text, (textposx, textposy))
        pygame.display.update(textposx, textposy, text.get_width(), text.get_height())
        while paused:
            self.clock.tick(self.framerate)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(1)
                    self.save_game_status()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        paused = False
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        self.save_game_status()
                        paused = False
                        return self.run()
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_game_status()
                sys.exit(1)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.save_game_status()
                    return self.run()
                elif event.key == pygame.K_p:
                    self.pause()
                for player in self.players:
                    player.handle_key(event.key)

    def startgame(self, pause=False):
        self.running = True
        while self.running:
            self.handle_events()
            self.screen.fill(BLACK)

            self.draw_game_area()
            self.draw_status_area()
            self.draw_players()

            self.clean_food()
            self.draw_food()

            pygame.display.flip()
            self.clock.tick(self.framerate)
            if pause:
                self.pause()
                pause = False
        if not self.running:
            self.save_scores()
            self.play_again()

    def play_again(self):
        self.screen.fill(BLACK)
        question = self.font.render('Play again? (y/n)', True, GREEN)
        self.screen.blit(question, (self.width/2 - question.get_size()[0] / 2, self.height/2 - question.get_size()[1] / 2))
        pygame.display.flip()
        asking = True
        while asking:
            self.clock.tick(self.framerate)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    asking = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        self.reset_game_env()
                        self.startgame()
                    else:
                        asking = False

    def reset_game_env(self):
        for player in self.players:
            player.full_reset()
        self.food = []

    def score_page(self):
        self.screen.fill(BLACK)

        scores = self.load_scores()
        scoretext = []
        i = 1
        for name, score in scores:
            scoretext.append(self.font.render('%s: %s - %s' % (i, name, score), True, GREEN))
            i += 1

        textposx = self.width / 3
        textposy = self.height / 4
        for qi in range(0, len(scoretext)):
            score = scoretext[qi]
            self.screen.blit(score, (textposx, textposy))
            textposy += score.get_size()[1] + 5

        pygame.display.flip()
        showing_scores = True
        while showing_scores:
            self.clock.tick(self.framerate)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    showing_scores = False
                    sys.exit(1)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        showing_scores = False
                        return self.run()

    def load_scores(self):
        if os.path.isfile(SCORE_FILE_NAME):
            scores = pickle.load(open(SCORE_FILE_NAME, 'rb'))
        else:
            scores = []
            for i in range(0, 10):
                scores.append(('NOBODY', 0))
        return sorted(scores, cmp=lambda x, y: y[1] - x[1])

    def save_scores(self):
        scores = self.load_scores()
        for player in self.players:
            for i in range(0, len(scores)):
                if scores[i][1] >= player.score:
                    continue
                else:
                    scores.insert(i, (player.name, player.score))
                    scores.pop()
                    break
        pickle.dump(scores, open(SCORE_FILE_NAME, 'wb'))

    def player_names_screen(self):
        for i in range(0, len(self.players)):
            player = self.players[i]
            name = player.name
            entering_name = True
            while entering_name:
                self.clock.tick(self.framerate)
                self.screen.fill(BLACK)
                text = 'Player %s name:    %s_' % (i + 1, name)
                nametext = self.font.render(text, True, player.color)
                self.screen.blit(nametext, (self.gamewidth / 4, self.gameheight / 4))
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        sys.exit(1)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            entering_name = False
                        elif event.key == pygame.K_BACKSPACE:
                            name = name[:-1]
                            name = name.capitalize()
                        elif event.key == pygame.K_ESCAPE:
                            return self.run()
                        else:
                            try:
                                name = name + chr(event.key)
                                name = name.capitalize()
                            except:
                                pass
                pygame.display.flip()
            player.name = name

game = MainApp()
game.run()

#todo:
# food moves
# food can kill snake if it touches it's body and not it's mouth
# two player co-op mode with shared score
