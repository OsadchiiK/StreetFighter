import pygame
from pygame import mixer

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
ch_map = 1
intro_count = 3
last_count_upd = pygame.time.get_ticks()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
score = [0, 0]
round_over = False
round_over_cd = 2000    # время между раундами
knight_size = 180
knight_scale_width = 2.3
knight_scale_height = 3
knight_shift = [78, 56]
knight_data = [knight_size, knight_scale_width,
               knight_scale_height, knight_shift]
martial_size = 200
martial_scale_width = 2.5
martial_scale_height = 3.5
martial_shift = [80, 77]
martial_data = [martial_size, martial_scale_width,
                martial_scale_height, martial_shift]

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


class bg(pygame.sprite.Sprite):
    def __init__(self):
        """"конструктор заднего фона
        загружаем картинки в массив
        """
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for i in range(num_image):
            im = 'images/bg/bg_' + str(ch_map) + '/' + str(i) + '.gif'
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
    def __init__(self, player, x, y, data, sprite_sheet,
                 animations, flip, sound):
        """конструктор класса Fighter
        self.update_anim - таймер для обновления анимаций
        self.flip - отражение картинки
        self.actions :
        #0-стоять, 1-бежать, 2-прыжок, 3-атака1, 4-атака2, 5-, 6-урон, 7-смерть
        self.image - выбираем нужную картинку
        self.animation.list-лист картинок[действие][номер картинки в анимации]
        """
        self.player = player
        self.map = 1
        self.rect = pygame.Rect((x, y), (80, 180))
        self.alive = True
        self.update_anim = pygame.time.get_ticks()
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
        self.sound = sound

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
        if pygame.time.get_ticks() - self.update_anim > anim_time:
            self.frame_index += 1
            self.update_anim = pygame.time.get_ticks()
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
                    self.attack_cd = 12
                # получил урон
                if self.action == 6:
                    self.hit = False
                    self.is_attack = False
                    self.attack_cd = 12

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
        GRAVITY = 2.4
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()
        self.run = False
        self.attack_type = 0
        if self.is_attack is False and self.alive is True:
            if round_over is False:
                # управление игрок1
                if self.player == 1:
                    if key[pygame.K_a]:
                        dx = -self.vx
                        self.flip = True
                        self.run = True
                    if key[pygame.K_d]:
                        dx = self.vx
                        self.flip = False
                        self.run = True
                    if key[pygame.K_w] and self.jumps <= 6:
                        self.vy = -25
                        self.jumps += 1
                    if key[pygame.K_c] and self.attack_cd == 0:
                        self.is_attack = True
                        self.attack_type = 1
                        self.attack(target)
                    if key[pygame.K_LSHIFT] and self.attack_cd == 0:
                        self.is_attack = True
                        self.attack_type = 2
                        self.attack(target)
                # управдение игрок2
                if self.player == 2:
                    if key[pygame.K_KP4]:
                        dx = -self.vx
                        self.flip = True
                        self.run = True
                    if key[pygame.K_KP6]:
                        dx = self.vx
                        self.flip = False
                        self.run = True
                    if key[pygame.K_KP8] and self.jumps <= 6:
                        self.vy = -25
                        self.jumps += 1
                    if key[pygame.K_KP_ENTER] and self.attack_cd == 0:
                        self.is_attack = True
                        self.attack_type = 1
                        self.attack(target)
                    if key[pygame.K_LEFT] and self.attack_cd == 0:
                        self.is_attack = True
                        self.attack_type = 2
                        self.attack(target)

        self.vy += GRAVITY
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
        self.sound.play()
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

    def end_round(self):
        self.map += 1


def interface():
    draw_health(fighter_1.health, 20, 20)
    draw_health(fighter_2.health, 860, 20)
    write_text('Hero Knight    ' + str(score[0]), font1, RED, 20, 60)
    write_text('Martial Hero    ' + str(score[1]), font1, RED, 860, 60)


fighter_1 = Fighter(1, 150, 500, knight_data,
                    knight_sheet, knight_animations,
                    False, sword)
fighter_2 = Fighter(2, 1050, 500, martial_data,
                    martial_sheet, martial_animations,
                    True, sword)
background = bg()
backgrounds = pygame.sprite.Group(background)
last_time = 0
font1 = pygame.font.Font(None, 32)
font = pygame.font.Font(None, 128)
finished = False
game_over = False

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
    if intro_count <= 0:
        fighter_1.move(fighter_2, round_over)
        fighter_2.move(fighter_1, round_over)
    else:
        write_text(str(intro_count), font, RED,
                   SCREEN_WIDTH/2, SCREEN_HEIGHT/3)
        if pygame.time.get_ticks() - last_count_upd >= 1000:
            intro_count -= 1
            last_count_upd = pygame.time.get_ticks()
    interface()
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
                ch_map += 1
                if ch_map == 4:
                    game_over = True
                intro_count = 3
                fighter_1 = Fighter(1, 150, 500, knight_data,
                                    knight_sheet, knight_animations,
                                    False, sword)
                fighter_2 = Fighter(2, 1050, 500, martial_data,
                                    martial_sheet, martial_animations,
                                    True, sword)
                background = bg()
                backgrounds = pygame.sprite.Group(background)
    else:
        if score[0] == 2 and end_count > 0:
            write_text('HERO KNIGHT WINS',
                       font, RED, SCREEN_WIDTH/8, SCREEN_HEIGHT/2)
            if pygame.time.get_ticks() - round_over_time >= 1000:
                end_count -= 1
                round_over_time = pygame.time.get_ticks()
            if end_count == 1:
                score[0] = 0
                score[1] = 0
                ch_map = 0
                game_over = False
                end_count = 5
        if score[1] == 2 and end_count > 0:
            write_text('MARTIAL HERO WINS',
                       font, RED, SCREEN_WIDTH/8, SCREEN_HEIGHT/2)
            if pygame.time.get_ticks() - round_over_time >= 1000:
                end_count -= 1
                round_over_time = pygame.time.get_ticks()
            if end_count == 1:
                score[0] = 0
                score[1] = 0
                ch_map = 0
                game_over = False
                end_count = 5

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            finished = True

    pygame.display.update()

pygame.quit()