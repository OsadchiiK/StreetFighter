import pygame
from pygame import mixer
from enum import Enum

mixer.init()
pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
FPS = 60
NUM_GIF = 8   # количество картинок в gif
TICK = 1000
ROUND_CD = 3000
# количество картинок в каждой анимации
KNIGHT_ANIMATIONS = [11, 8, 3, 7, 7, 3, 4, 11]
MARTIAL_ANIMATIONS = [4, 8, 2, 4, 4, 2, 3, 7]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font1 = pygame.font.Font(None, 32)
font = pygame.font.Font(None, 128)

pygame.mixer.music.load('mus/music.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword = pygame.mixer.Sound('mus/sword.mp3')
sword.set_volume(0.7)

knight_sprite = 'images/fighters/Hero Knight/Sprites/Hero Knight.png'
martial_sprite = 'images/fighters/Martial Hero/Sprites/Martial Hero.png'
knight_sheet = pygame.image.load(knight_sprite).convert_alpha()
martial_sheet = pygame.image.load(martial_sprite).convert_alpha()


def draw_health(health, x, y):
    """рисует количество жизни"""
    ratio = health/100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))


def write_text(text, font, text_col, x, y):
    """рисует текст"""
    text = font.render(text, True, text_col)
    screen.blit(text, (x, y))


def load_image(name):
    """загружаем картинки заднего фона"""
    im = pygame.image.load(name)
    scaled_im = pygame.transform.scale(im, (SCREEN_WIDTH, SCREEN_HEIGHT))
    return scaled_im


class Animation(Enum):
    IDLE = 0
    RUN = 1
    JUMP = 2
    ATTACK_1 = 3
    ATTACK_2 = 4
    GET_DAMAGE = 6
    DEATH = 7


class Obj(Enum):
    fighter_1 = 1
    fighter_2 = 2
    backgrounds = 0
    background = 3


class Background(pygame.sprite.Sprite):
    def __init__(self, map, end_round_time):
        """конструктор заднего фона
        загружаем картинки в массив
        + индикаторы времени после раунда/игры/начала раунда
        """
        self.round_started = False
        self.end_time = end_round_time
        self.end_count = 5
        self.last_end_time = 0
        self.intro_count = 3
        self.last_count_upd = 0
        self.last_time = 0
        self.map = map
        self.game_over = False
        self.round_over = False
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for i in range(NUM_GIF):
            im = 'images/bg/bg_' + str(self.map) + '/' + str(i) + '.gif'
            self.images.append(load_image(im))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT))

    def update(self):
        """обновляем задний фон"""
        anim_upd = 150
        if pygame.time.get_ticks() - self.last_time > anim_upd:
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
            self.image = self.images[self.index]
            self.last_time = pygame.time.get_ticks()

    def intro(self):
        """начальный отсчет"""
        write_text(str(self.intro_count), font, RED,
                   SCREEN_WIDTH/2 - 24, SCREEN_HEIGHT/3)
        if pygame.time.get_ticks() - self.last_count_upd >= TICK:
            self.last_count_upd = pygame.time.get_ticks()
            self.intro_count -= 1
            if self.intro_count == 0:
                self.intro_count = 3
                self.round_started = True

    def end_game_count(self):
        """задержка в конце игры, выставляем начальные параметры"""
        if pygame.time.get_ticks() - self.last_end_time >= TICK:
            self.end_count -= 1
            self.last_end_time = pygame.time.get_ticks()
            if self.end_count == 1:
                objects[Obj.fighter_1.value].score = 0
                objects[Obj.fighter_2.value].score = 0
                self.map = 0
                self.game_over = False
                self.end_count = 5

    def new_round(self):
        """меняем карту"""
        self.round_over = False
        self.map += 1
        if self.map == 4:
            self.game_over = True

    def end_round(self):
        self.round_over = True
        self.end_time = pygame.time.get_ticks()

    def round_check(self):
        """условие начала нового раунда"""
        return (pygame.time.get_ticks() -
                objects[Obj.background.value].end_time) >= ROUND_CD


class Fighter():
    def __init__(self, player, x, y, sprite_sheet, animations, flip, sound,
                 data, controls, score):
        """конструктор класса Fighter
        self.update_anim - таймер для обновления анимаций
        self.flip - отражение картинки
        self.image - выбираем нужную картинку
        self.animation.list-лист картинок[действие][номер картинки в анимации]
        """
        self.button_jump = controls[0]
        self.button_left = controls[1]
        self.button_right = controls[2]
        self.button_attack_1 = controls[3]
        self.button_attack_2 = controls[4]
        self.player = player
        self.rect = pygame.Rect((x, y), (80, 180))
        self.alive = True
        self.last_anim_tick = pygame.time.get_ticks()
        self.shift = data[3]
        self.sc_width = data[1]     # scale
        self.sc_height = data[2]    # scale
        self.flip = flip
        self.vx = 8
        self.vy = 0
        self.jumps = 0
        self.run = False
        self.attack_type = 0
        self.attack_cd = 0
        self.is_attack = False
        self.health = 100
        self.size = data[0]
        self.animation_list = self.load_images(sprite_sheet, animations)
        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.hit = False
        self.sword_sound = sound
        self.score = score

    def load_images(self, sprite_sheet, animations):
        """загружаем картинки, меняем размеры"""
        animation_list = []
        i = 0
        for animation in animations:
            curr_image_list = []
            for j in range(animation):
                curr_image = sprite_sheet.subsurface(j*self.size,
                                                     i*self.size,
                                                     self.size,
                                                     self.size)
                scaled_im = pygame.transform.scale(curr_image, (
                                                   self.size*self.sc_width,
                                                   self.size*self.sc_height))
                curr_image_list.append(scaled_im)
            i += 1
            animation_list.append(curr_image_list)
        return animation_list

    def draw(self, surface):
        """выводим картинку"""
        image = pygame.transform.flip(self.image, self.flip, False)
        surface.blit(image, (self.rect.x - self.shift[0]*self.sc_width,
                     self.rect.y - self.shift[1]*self.sc_height))

    def update(self):
        """проверяем что делает игрок
        и меняем анимацию
        """
        anim_time = 70
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(Animation.DEATH.value)
        elif self.hit is True:
            self.update_action(Animation.GET_DAMAGE.value)
        elif self.is_attack is True:
            if self.attack_type == 1:
                self.update_action(Animation.ATTACK_1.value)
            elif self.attack_type == 2:
                self.update_action(Animation.ATTACK_2.value)
        elif self.jumps != 0:
            self.update_action(Animation.JUMP.value)
        elif self.run is True:
            self.update_action(Animation.RUN.value)
        else:
            self.update_action(Animation.IDLE.value)
        # обновляем картинку
        self.image = self.animation_list[self.action][self.frame_index]
        # достаточно ли прошло времени с прошлого обновления
        if pygame.time.get_ticks() - self.last_anim_tick > anim_time:
            self.frame_index += 1
            self.last_anim_tick = pygame.time.get_ticks()
        # проверка кончились ли анимации
        if self.frame_index >= len(self.animation_list[self.action]):
            # конец анимации если игрок мертв
            if self.alive is False:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                # завершение атаки
                if (self.action == Animation.ATTACK_1.value or
                        self.action == Animation.ATTACK_2.value):
                    self.is_attack = False
                    self.attack_cd = 25
                # получил урон
                if self.action == Animation.GET_DAMAGE.value:
                    self.hit = False
                    self.is_attack = False
                    self.attack_cd = 25

    def update_action(self, new_action):
        """вспомогательная функция
        чтобы не было ошибок если в
        анимациях разное число кадров
        """
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_anim = pygame.time.get_ticks()

    def move(self, target, round_over):
        """перемещение игроков"""
        gravity = 2.4
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()
        self.run = False
        self.attack_type = 0
        if self.is_attack is False and self.alive is True:
            if round_over is False:
                if key[self.button_left]:
                    dx = -self.vx
                    self.flip = True
                    self.run = True
                if key[self.button_right]:
                    dx = self.vx
                    self.flip = False
                    self.run = True
                if key[self.button_jump] and self.jumps <= 5:
                    self.vy = -25
                    self.jumps += 1
                if key[self.button_attack_1] and self.attack_cd == 0:
                    self.is_attack = True
                    self.attack_type = 1
                    self.attack(target)
                if key[self.button_attack_2] and self.attack_cd == 0:
                    self.is_attack = True
                    self.attack_type = 2
                    self.attack(target)

        self.vy += gravity
        dy += self.vy

        if dx + self.rect.left < 0:
            dx = -self.rect.left
        if dx + self.rect.right > SCREEN_WIDTH:
            dx = SCREEN_WIDTH - self.rect.right
        if dy + self.rect.bottom > SCREEN_HEIGHT - 45:
            self.vy = 0
            dy = SCREEN_HEIGHT - 45 - self.rect.bottom
            self.jumps = 0

        self.rect.x += dx
        self.rect.y += dy

        if self.attack_cd > 0:
            self.attack_cd -= 1

    def attack(self, target):
        """регистрация урона"""
        self.is_attack = True
        self.sword_sound.play()
        if not self.flip:
            attack_rect = pygame.Rect((self.rect.centerx, self.rect.y),
                                      (2*self.rect.width, self.rect.height))
        else:
            attack_rect = pygame.Rect((-2*self.rect.width + self.rect.centerx,
                                       self.rect.y),
                                      (2*self.rect.width, self.rect.height))
        if attack_rect.colliderect(target.rect):
            target.health -= 10
            target.hit = True


def interface():
    """draw health bars"""
    draw_health(objects[Obj.fighter_1.value].health, 20, 20)
    draw_health(objects[Obj.fighter_2.value].health, 860, 20)
    write_text('Hero Knight    ' + str(objects[Obj.fighter_1.value].score),
               font1, RED, 20, 60)
    write_text('Martial Hero    ' + str(objects[Obj.fighter_2.value].score),
               font1, RED, 860, 60)


def start_round():
    """после отсчета можно играть"""
    if objects[Obj.background.value].round_started:
        objects[Obj.fighter_1.value].move(
                                    objects[Obj.fighter_2.value],
                                    objects[Obj.background.value].round_over)
        objects[Obj.fighter_2.value].move(
                                    objects[Obj.fighter_1.value],
                                    objects[Obj.background.value].round_over)
    else:
        objects[Obj.background.value].intro()


def victory():
    """надписи при победе"""
    objects[Obj.background.value].end_game_count()
    if objects[Obj.fighter_1.value].score == 2 > 0:
        write_text('HERO KNIGHT WINS',
                   font, RED, SCREEN_WIDTH/8, SCREEN_HEIGHT/2)
    if objects[Obj.fighter_2.value].score == 2 > 0:
        write_text('MARTIAL HERO WINS',
                   font, RED, SCREEN_WIDTH/8, SCREEN_HEIGHT/2)


def get_score():
    """начисляем очки"""
    if objects[Obj.fighter_1.value].alive is False:
        objects[Obj.fighter_2.value].score += 1
        objects[Obj.background.value].end_round()
    elif objects[Obj.fighter_2.value].alive is False:
        objects[Obj.fighter_1.value].score += 1
        objects[Obj.background.value].end_round()


def init_objects(score_1, score_2, map, end_round_time):
    """инициализируем файтеров и задний фон"""
    fighter_1 = Fighter(1, 150, 500,
                        knight_sheet, KNIGHT_ANIMATIONS,
                        False, sword, [180, 2.3, 3, [78, 56]],
                        [pygame.K_w, pygame.K_a, pygame.K_d,
                            pygame.K_c, pygame.K_LSHIFT],
                        score_1)
    fighter_2 = Fighter(2, 1050, 500,
                        martial_sheet, MARTIAL_ANIMATIONS,
                        True, sword, [200, 2.5, 3.5, [80, 77]],
                        [pygame.K_KP8, pygame.K_KP4, pygame.K_KP6,
                            pygame.K_KP_ENTER, pygame.K_LEFT],
                        score_2)
    background = Background(map, end_round_time)
    backgrounds = pygame.sprite.Group(background)
    return [backgrounds, fighter_1, fighter_2, background]


objects = init_objects(0, 0, 1, 0)
finished = False

while not finished:
    clock.tick(FPS)
    for obj in objects[:3]:
        obj.update()
        obj.draw(screen)
    interface()
    start_round()
    if (objects[Obj.fighter_1.value].score == 2 or
            objects[Obj.fighter_2.value].score == 2):
        objects[Obj.background.value].game_over = True
    if objects[Obj.background.value].game_over is False:
        if objects[Obj.background.value].round_over is False:
            get_score()
        else:
            if objects[Obj.background.value].round_check():
                objects[Obj.background.value].new_round()
                objects = init_objects(objects[Obj.fighter_1.value].score,
                                       objects[Obj.fighter_2.value].score,
                                       objects[Obj.background.value].map,
                                       objects[Obj.background.value].end_time)
    else:
        victory()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            finished = True

    pygame.display.update()

pygame.quit()
