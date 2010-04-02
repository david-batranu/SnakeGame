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
BACKGROUND = 'img/grass.jpg'
SNAKES = 'img/snakes.png'
BUGS = 'img/bugs.png'


class Food(object):
    def __init__(self, surface, bulk=20):
        self.surface = surface
        self.bulk = bulk
        self.color = GREEN
        self.points = 0
        self.eaten = False
        self.dir_x = -1
        self.dir_y = 1
        self.animation_pos = 0
        self.animation_direction = 1
        self.animation_speed = 160 #ms
        self.time = 0
        self.rect = self.build_rect()
        self.set_points_worth()

    def build_rect(self):
        x = random.randrange(self.bulk, game.gamewidth - self.bulk)
        y = random.randrange(self.bulk, game.gameheight - self.bulk)
        return pygame.Rect(x, y, self.bulk, self.bulk)

    def set_points_worth(self):
        x_cartesian = (self.rect.x - (game.gamewidth / 2)) / 10
        y_cartesian = (self.rect.y - (game.gameheight / 2)) / 10

        def make_positive(i):
            return i if i >=0 else i * -1
        
        x = make_positive(x_cartesian)
        y = make_positive(y_cartesian)
        self.points = (x + y) / 2

    def being_eaten(self, rect):
        return self.rect.colliderect(rect)

    def has_been_eaten(self):
        self.eaten = True

    def nutritional_value(self):
        return self.points / 10

    def draw(self):
        pos = self.animation_pos * self.bulk
        self.surface.blit(game.bugs.subsurface(pos, 0, self.bulk, self.bulk), self.rect)
        curr_time = pygame.time.get_ticks()
        if self.time == 0:
            self.time = curr_time
        time_passed = curr_time - self.time
        if not time_passed > self.animation_speed:
            return
        else:
            self.time = curr_time
        if pos + self.bulk >= game.bugs.get_width():
            self.animation_direction = -1
        elif self.animation_pos == 0:
            self.animation_direction = 1
        self.animation_pos += self.animation_direction

    def move(self):
        def rect_in_players():
            for player in game.players:
                if self.rect.collidelist(player.body) != -1:
                    return True

        if bool(random.randint(0, 1)):
            self.dir_x = random.randint(-1, 1)
            self.dir_y = random.randint(-1, 1)

        self.rect.x += self.dir_x
        self.rect.y += self.dir_y

        if not game.gamearea.contains(self.rect) or rect_in_players():
            self.rect.x += self.dir_x * -1
            self.rect.y += self.dir_y * -1

class BaseSnake(object):

    def __init__(self, surface, startpos, color, initlength=10, bulk=20):
        self.surface = surface
        self.startpos = startpos
        self.initlength = initlength
        self.length = initlength
        self.body = []
        self.x, self.y = startpos
        self.dir_x = 0
        self.dir_y = -1 * bulk
        self.crashed = False
        self.score = 0
        self.bulk = bulk
        self.color = color
        self.speed = 160 #ms
        self.time = 0
        self.cycles = 0
        self.needs_to_move = False
        self.define_body_elements()

    def define_body_elements(self):
        pos = (self.number * self.bulk) - self.bulk
        self.head_ud = pygame.Rect(0, pos, self.bulk, self.bulk)
        self.head_du = pygame.Rect(1 * self.bulk, pos, self.bulk, self.bulk)
        self.head_lr = pygame.Rect(2 * self.bulk, pos, self.bulk, self.bulk)
        self.head_rl = pygame.Rect(3 * self.bulk, pos, self.bulk, self.bulk)
        
        self.body_horiz = pygame.Rect(4 * self.bulk, pos, self.bulk, self.bulk)
        self.body_vert = pygame.Rect(5 * self.bulk, pos, self.bulk, self.bulk)

        self.flex_rddr = pygame.Rect(6 * self.bulk, pos, self.bulk, self.bulk)
        self.flex_luul = pygame.Rect(7 * self.bulk, pos, self.bulk, self.bulk)
        self.flex_ruur = pygame.Rect(8 * self.bulk, pos, self.bulk, self.bulk)
        self.flex_lddl = pygame.Rect(9 * self.bulk, pos, self.bulk, self.bulk)

        self.tail_ud = pygame.Rect(10 * self.bulk, pos, self.bulk, self.bulk)
        self.tail_du = pygame.Rect(11 * self.bulk, pos, self.bulk, self.bulk)
        self.tail_lr = pygame.Rect(12 * self.bulk, pos, self.bulk, self.bulk)
        self.tail_rl = pygame.Rect(13 * self.bulk, pos, self.bulk, self.bulk)

    def set_difficulty(self):
        if self.score > 500:
            self.speed = 30
        if self.score > 1000:
            self.speed = 20
        
    def move(self):
        self.set_difficulty()
        curr_time = pygame.time.get_ticks()
        if self.time == 0:
            self.time = curr_time
        time_passed = curr_time - self.time
        if not time_passed > self.speed:
            return
        else:
            self.cycles = time_passed / self.speed
            self.time = curr_time

        for i in range(self.cycles):
            self.x += self.dir_x
            self.y += self.dir_y
            body_elem = pygame.Rect(self.x, self.y, self.bulk, self.bulk)
            self.body.insert(0, body_elem)
            if self.length != 0 and len(self.body) > self.length:
                self.body.pop()

        self.crashed = self.check_crash()
        self.needs_to_move = False

    def draw(self):
        if not self.body:
            return
        body_length = len(self.body)
        for i in range(body_length):
            if i != 0:
                prev = self.body[i - 1]
            else:
                prev = None
            me = self.body[i]
            try:
                next = self.body[i + 1]
            except IndexError:
                next = None

            if not prev and next:
                if me.x < next.x:
                    img = game.snakes.subsurface(self.head_lr)
                elif me.x > next.x:
                    img = game.snakes.subsurface(self.head_rl)
                elif me.y < next.y:
                    img = game.snakes.subsurface(self.head_ud)
                elif me.y > next.y:
                    img = game.snakes.subsurface(self.head_du)

                self.surface.blit(img, self.body[i])


            if next and prev:
                if me.x < next.x and me.y < prev.y or \
                    me.x < prev.x and me.y < next.y:
                    img = game.snakes.subsurface(self.flex_rddr)

                elif me.x < next.x and me.y > prev.y or \
                    me.x < prev.x and me.y > next.y:
                    img = game.snakes.subsurface(self.flex_ruur)

                elif me.x > next.x and me.y > prev.y or \
                    me.x > prev.x and me.y > next.y:
                    img = game.snakes.subsurface(self.flex_luul)

                elif me.x > next.x and me.y < prev.y or \
                    me.x > prev.x and me.y < next.y:
                    img = game.snakes.subsurface(self.flex_lddl)

                elif me.x == prev.x == next.x:
                    img = game.snakes.subsurface(self.body_vert)

                elif me.y == prev.y == next.y:
                    img = game.snakes.subsurface(self.body_horiz)

                self.surface.blit(img, self.body[i])

            if not next and prev:
                if me.x > prev.x:
                    img = game.snakes.subsurface(self.tail_lr)
                elif me.x < prev.x:
                    img = game.snakes.subsurface(self.tail_rl)
                elif me.y > prev.y:
                    img = game.snakes.subsurface(self.tail_ud)
                elif me.y < prev.y:
                    img = game.snakes.subsurface(self.tail_du)
                    
                self.surface.blit(img, self.body[i])

    def check_crash(self):
        head = self.body[0]
        gamearea = game.gamearea
        if not gamearea.contains(head):
            return True
        for player in game.players:
            pbody = player.body[1:]
            if head.collidelist(pbody) != -1:
                return True
        return False

    def check_ate(self, food):
        if not len(self.body):
            return
        for f in food:
            if f.being_eaten(self.body[0]):
                self.score += f.points
                self.length += f.nutritional_value()
                f.has_been_eaten()


class Player(BaseSnake):
    def __init__(self, name, controls, number, *args):
        self.name = name
        self.number = number
        self.lives = 3
        self.playing = True
        self.up, self.down, self.left, self.right = controls
        BaseSnake.__init__(self, *args)

    def reset(self):
        self.body = []
        self.x, self.y = self.startpos
        self.dir_x, self.dir_y = 0, -1 * self.bulk
        self.score = 0
        self.crashed = False
        self.playing = True
    
    def full_reset(self):
        self.reset()
        self.length = self.initlength
        self.lives = 3
        self.time = 0

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
            if self.dir_y in (1, self.bulk) or self.needs_to_move:
                return
            self.dir_x = 0
            self.dir_y = -1 * self.bulk
            self.needs_to_move = True
        elif key == self.down:
            if self.dir_y in (-1, self.bulk * -1) or self.needs_to_move:
                return
            self.dir_x = 0
            self.dir_y = 1 * self.bulk
            self.needs_to_move = True
        elif key == self.left:
            if self.dir_x in (1, self.bulk) or self.needs_to_move:
                return
            self.dir_x = -1 * self.bulk
            self.dir_y = 0
            self.needs_to_move = True
        elif key == self.right:
            if self.dir_x in (-1, self.bulk * -1) or self.needs_to_move:
                return
            self.dir_x = 1 * self.bulk
            self.dir_y = 0
            self.needs_to_move = True

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
    gamearea = None
    difficulty = 'normal'
    font = pygame.font.Font('freesansbold.ttf', 18)
    background = pygame.image.load(BACKGROUND).convert()
    snakes = pygame.image.load(SNAKES).convert()
    bugs = pygame.image.load(BUGS).convert()

    def __init__(self):
        pygame.display.set_caption('SnakeGame')
        self.snakes.set_colorkey((255, 255, 255))
        self.bugs.set_colorkey((255, 255, 255))


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
            if self.difficulty == 'hard':
                f.move()

    def draw_game_area(self):
        rect = pygame.draw.rect(self.screen, WHITE, (0, 0, self.gamewidth, self.gameheight), 1)
        self.gamearea = rect

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
        self.food = []
        p1_controls = pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
        p2_controls = pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d
        player1 = Player('Player 1', p1_controls, 1, self.screen,
                         (self.gamewidth/2, self.gameheight/2), WHITE, 10)
        player2 = Player('Player 2', p2_controls, 2, self.screen,
                         (self.gamewidth/3, self.gameheight/3), RED, 10)

        self.screen.fill(BLACK)
        questiontext = [self.font.render('Press 1 for singleplayer', True, GREEN),
                        self.font.render('Press 2 for 2-player mode.', True, GREEN),
                        self.font.render('Player 1 controls: directional keys;', True, BLUE),
                        self.font.render('Player 2 controls: WSAD keys.', True, BLUE),
                        self.font.render('ESC = exit game', True, GREEN),
                        self.font.render('F1 = view high scores', True, GREEN)]

        if self.game_status_is_saved():
            text = 'Press c to continue previous game'
            questiontext.insert(-2, self.font.render(text, True, RED))
        
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
        self.select_difficulty_screen()
        self.startgame()

    def game_status_is_saved(self):
        return os.path.isfile(SESSION_FILE_NAME)
    
    def save_game_status(self):
        data = {'players': [], 'food': [], 'game': {}}
        for player in self.players:
            pdata = player.__dict__
            for key in ['surface', 'time']:
                del pdata[key]
            data['players'].append(pdata)
        
        for food in self.food:
            fdata = food.__dict__
            for key in ['surface', 'time']:
                del fdata[key]
            data['food'].append(fdata)

        data['game']['difficulty'] = game.difficulty

        session_file = open(SESSION_FILE_NAME, 'wb')
        pickle.dump(data, session_file)
    
    def load_game_status(self):
        session_file = open(SESSION_FILE_NAME, 'rb')
        data = pickle.load(session_file)
        self.players = []
        for player in data['players']:
            controls = player['up'], player['down'], player['left'], player['right']
            pobj = Player(player['name'], controls, player['number'], self.screen, player['startpos'],
                          player['color'], player['initlength'])
            for key, value in player.items():
                setattr(pobj, key, value)
            self.add_player(pobj)

        self.food = []
        for food in data['food']:
            fobj = Food(self.screen)
            for key, value in food.items():
                setattr(fobj, key, value)
            self.food.append(fobj)
        
        game.difficulty = data['game']['difficulty']

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
        pygame.display.update(textposx, textposy,
                              text.get_width(), text.get_height())
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
        for player in self.players:
            player.time = 0
            
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
            #self.screen.fill(BLACK)
            self.screen.blit(self.background, (0, 0))

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
            return self.run()

    def play_again(self):
        self.screen.fill(BLACK)
        question = self.font.render('Play again? (y/n)', True, GREEN)
        self.screen.blit(question,
                         (self.width/2 - question.get_size()[0] / 2,
                          self.height/2 - question.get_size()[1] / 2)
                        )
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
            s = '%s: %s - %s' % (i, name, score)
            text = self.font.render(s, True, GREEN)
            scoretext.append(text)
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

    def select_difficulty_screen(self):
        selecting = True
        while selecting:
            self.clock.tick(self.framerate)
            self.screen.fill(BLACK)
            text = 'Press 1 for normal difficulty or 2 for hard difficulty'
            nametext = self.font.render(text, True, GREEN)
            self.screen.blit(nametext, (self.gamewidth / 4, self.gameheight / 4))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(1)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.difficulty = 'normal'
                        selecting = False
                    elif event.key == pygame.K_2:
                        self.difficulty = 'hard'
                        selecting = False
                    elif event.key == pygame.K_ESCAPE:
                        return self.run()
            pygame.display.flip()
        if self.difficulty == 'hard':
            for player in self.players:
                player.speed = 50

game = MainApp()
game.run()

#todo:
# two player co-op mode with shared score
