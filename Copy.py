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
end_count = 5
num_image = 8   # количество картинок в gif
map = 1
intro_count = 3
last_count_upd = pygame.time.get_ticks()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
score = [0, 0]
round_over = False
game_over = False
round_over_cd = 3000    # время между раундами
font1 = pygame.font.Font(None, 32)
font = pygame.font.Font(None, 128)

pygame.mixer.music.load('mus/music.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword = pygame.mixer.Sound('mus/sword.mp3')
sword.set_volume(0.7)


def load_image(name):
    im = pygame.image.load(name)
    scaled_im = pygame.transform.scale(im, (SCREEN_WIDTH, SCREEN_HEIGHT))
    return scaled_im


knight_sprite = 'images/fighters/Hero Knight/Sprites/Hero Knight.png'
martial_sprite = 'images/fighters/Martial Hero/Sprites/Martial Hero.png'
knight_sheet = pygame.image.load(knight_sprite).convert_alpha()
martial_sheet = pygame.image.load(martial_sprite).convert_alpha()
# количество картинок в каждой анимации
knight_animations = [11, 8, 3, 7, 7, 3, 4, 11]
martial_animations = [4, 8, 2, 4, 4, 2, 3, 7]


def draw_health(health, x, y):
    """рисует количество жизни"""
    ratio = health/100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))


def write_text(text, font, text_col, x, y):
    text = font.render(text, True, text_col)
    screen.blit(text, (x, y))


class Animations(Enum):
    IDLE = 0
    RUN = 1
    JUMP = 2
    ATTACK_1 = 3
    ATTaCK_2 = 4
    GET_DAMAGE = 6
    DEATH = 7


class Background(pygame.sprite.Sprite):
    def __init__(self):
        """"конструктор заднего фона
        загружаем картинки в массив
        """
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for i in range(num_image):
            im = 'images/bg/bg_' + str(map) + '/' + str(i) + '.gif'
            self.images.append(load_image(im))
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pygame.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT))

    def update(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]


class Fighter():
    def __init__(self, player, x, y, sprite_sheet, animations, flip, sound,
                 data, controls):
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
        self.sc_height = data[2]   # scale
        self.flip = flip
        self.vx = 8
        self.vy = 0
        self.jumps = 0
        self.run = False
        self.attack_type = 0
        self.attack_cd = 0
        self.is_attack = False
        self.health = 10
        self.size = data[0]
        self.animation_list = self.load_images(sprite_sheet, animations)
        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.hit = False
        self.sword_sound = sound

    def load_images(self, sprite_sheet, animations):
        """"загружаем картинки, меняем размеры"""
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
            self.update_action(7)
        elif self.hit is True:
            self.update_action(6)
        elif self.is_attack is True:
            if self.attack_type == 1:
                self.update_action(3)
            elif self.attack_type == 2:
                self.update_action(4)
        elif self.jumps != 0:
            self.update_action(2)
        elif self.run is True:
            self.update_action(1)
        else:
            self.update_action(0)
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
                if self.action == 3 or self.action == 4:
                    self.is_attack = False
                    self.attack_cd = 25
                # получил урон
                if self.action == 6:
                    self.hit = False
                    self.is_attack = False
                    self.attack_cd = 25

    def update_action(self, new_action):
        """"вспомогательная функция
        чтобы не было ошибок если в
        анимациях разное число кадров
        """
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_anim = pygame.time.get_ticks()

    def move(self, target, round_over):
        """"перемещение игроков"""
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
    draw_health(fighter_1.health, 20, 20)
    draw_health(fighter_2.health, 860, 20)
    write_text('Hero Knight    ' + str(score[0]), font1, RED, 20, 60)
    write_text('Martial Hero    ' + str(score[1]), font1, RED, 860, 60)


fighter_1 = Fighter(1, 150, 500,
                    knight_sheet, knight_animations,
                    False, sword, [180, 2.3, 3, [78, 56]],
                    [pygame.K_w, pygame.K_a, pygame.K_d,
                        pygame.K_c, pygame.K_LSHIFT])
fighter_2 = Fighter(2, 1050, 500,
                    martial_sheet, martial_animations,
                    True, sword, [200, 2.5, 3.5, [80, 77]],
                    [pygame.K_KP8, pygame.K_KP4, pygame.K_KP6,
                        pygame.K_KP_ENTER, pygame.K_LEFT])
background = Background()
backgrounds = pygame.sprite.Group(background)
last_time = 0
font1 = pygame.font.Font(None, 32)
font = pygame.font.Font(None, 128)
finished = False

while not finished:
    clock.tick(FPS)
    if pygame.time.get_ticks() - last_time > 150:
        backgrounds.update()
        last_time = pygame.time.get_ticks()
    backgrounds.draw(screen)
    fighter_1.update()
    fighter_2.update()
    fighter_1.draw(screen)
    fighter_2.draw(screen)
    interface()
    if intro_count <= 0:
        fighter_1.move(fighter_2, round_over)
        fighter_2.move(fighter_1, round_over)
    else:
        write_text(str(intro_count), font, RED,
                   SCREEN_WIDTH/2 - 24, SCREEN_HEIGHT/3)
        if pygame.time.get_ticks() - last_count_upd >= 1000:
            intro_count -= 1
            last_count_upd = pygame.time.get_ticks()
    if score[0] == 2 or score[1] == 2:
        game_over = True
    if game_over is False:
        if round_over is False:
            if fighter_1.alive is False:
                score[1] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
            elif fighter_2.alive is False:
                score[0] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
        else:
            if pygame.time.get_ticks() - round_over_time >= round_over_cd:
                round_over = False
                map += 1
                if map == 4:
                    game_over = True
                intro_count = 3
                fighter_1 = Fighter(1, 150, 500,
                                    knight_sheet, knight_animations,
                                    False, sword, [180, 2.3, 3, [78, 56]],
                                    [pygame.K_w, pygame.K_a, pygame.K_d,
                                     pygame.K_c, pygame.K_LSHIFT])
                fighter_2 = Fighter(2, 1050, 500,
                                    martial_sheet, martial_animations,
                                    True, sword, [200, 2.5, 3.5, [80, 77]],
                                    [pygame.K_KP8, pygame.K_KP4, pygame.K_KP6,
                                     pygame.K_KP_ENTER, pygame.K_LEFT])
                background = Background()
                backgrounds = pygame.sprite.Group(background)
    else:
        if score[0] == 2 and end_count > 0:
            write_text('HERO KNIGHT WINS',
                       font, RED, SCREEN_WIDTH/8, SCREEN_HEIGHT/2)
        if score[1] == 2 and end_count > 0:
            write_text('MARTIAL HERO WINS',
                       font, RED, SCREEN_WIDTH/8, SCREEN_HEIGHT/2)
        if pygame.time.get_ticks() - round_over_time >= 1000:
            end_count -= 1
            round_over_time = pygame.time.get_ticks()
        if end_count == 1:
            score[0] = 0
            score[1] = 0
            map = 0
            game_over = False
            end_count = 5

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            finished = True

    pygame.display.update()

pygame.quit()
