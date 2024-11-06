import os
import random
import sys
import time

import pygame as pg


WIDTH, HEIGHT = 750, 700
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# こうかとん（プレイヤー）のクラス
class Hero:
    """ゲームキャラクター（こうかとん）に関するクラス"""
    delta = {
        pg.K_UP: (0, -50),
        pg.K_DOWN: (0, +50),
        pg.K_LEFT: (-50, 0),
        pg.K_RIGHT: (+50, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("images/Kokaton/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+50, 0): img,
        (+50, -50): pg.transform.rotozoom(img, 45, 0.9),
        (0, -50): pg.transform.rotozoom(img, 90, 0.9),
        (-50, -50): pg.transform.rotozoom(img0, -45, 0.9),
        (-50, 0): img0,
        (-50, +50): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +50): pg.transform.rotozoom(img, -90, 0.9),
        (+50, +50): pg.transform.rotozoom(img, -45, 0.9),
    }
    mvct = 0

    def __init__(self, xy: tuple[int, int]) -> None:
        self.img = __class__.imgs[(+50, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+50, 0)
        self.score = 0  # スコアの初期化

    def add_score(self, points: int) -> None:
        """スコアにポイントを追加するメソッド"""
        self.score += points

    # キーの入力で動く処理
    def update(self, screen: pg.Surface) -> None:
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        key_lst = pg.key.get_pressed()

        if __class__.mvct == 0:
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    sum_mv[0] += mv[0]
                    sum_mv[1] += mv[1]
                    if 0 != sum_mv[0] and 0 != sum_mv[1]: # 斜め移動防止用
                        sum_mv[0] = 0
                        sum_mv[1] = 0
            self.rct.move_ip(sum_mv) # 移動
            __class__.mvct = 15 # 0.25秒の待機
        elif 0 < __class__.mvct:
            __class__.mvct -= 1

        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = sum_mv
        screen.blit(self.img, self.rct)


# 敵のクラス
class Enemy(pg.sprite.Sprite):
    """
    敵に関するクラス
    """
    imgs = [pg.image.load(f"images/ufo/alien{i}.png") for i in range(1, 4)]

    def __init__(self, num: int, vx: tuple[int, int]) -> None:
        """
        敵のSurfaceの作成
        引数1 num: 画像指定用整数
        引数2 vx: Rectのcenter用タプル
        """
        super().__init__()
        self.num = num
        self.img = __class__.imgs[self.num]
        self.image = pg.transform.rotozoom(self.img, 0, 0.5)
        self.rect = self.image.get_rect()
        self.rect.center = vx
        self.vx, self.vy = 0, 0
        self.mvct = 0 # 行動後のクールタイム
        self.state = "move" # move、bomで行動管理

    def control(self) -> None:
        """
        敵に関する動作制御を行う
        """
        img_key = { # 進行方向に応じた画像
            (+50, 0): pg.transform.rotozoom(self.img, 0, 0.5), # 右
            (0, -50): pg.transform.rotozoom(self.image, 90, 1.0), # 上
            (-50, 0): pg.transform.flip(self.image, True, False), # 左
            (0, +50): pg.transform.rotozoom(self.image, -90, 1.0), # 下
        }
        move_list = [ # 移動用数値
            (0, -50), # 上
            (0, +50), # 下
            (-50, 0), # 左
            (+50, 0), # 右
        ]

        if self.mvct == 0: # クールタイムでなければ
            while True:
                sum_mv = random.choice(move_list)
                self.rect.move_ip(sum_mv[0], sum_mv[1])
                if check_bound(self.rect) != (True, True): # 盤面領域判定
                    self.rect.move_ip(-sum_mv[0], -sum_mv[1])
                    continue
                break
            self.image = img_key[sum_mv]
            self.mvct = 15
        elif self.mvct > 0: # クールタイムであれば
            self.mvct -= 1

    def update(self) -> None:
        """
        敵の情報を更新する
        """
        __class__.control(self)


# 爆弾（ボンバー）のクラス
class Bomber(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    def __init__(self, vx: tuple[int, int], hero: Hero, enemies: pg.sprite.Group, bom_effects: pg.sprite.Group) -> None:
        """
        引数1: vx:heroのrect座標
        引数2: hero: Heloのインスタンス
        引数3: enemies: 敵グループ
        引数4: bom_effects: 爆発エフェクトグループ
        """
        super().__init__()
        self.bom_img = pg.image.load("images/bom/bom.png")
        self.exp_img = pg.image.load("images/bom/explosion.png")
        self.image = pg.transform.rotozoom(self.bom_img, 0, 0.1)
        self.rect = self.image.get_rect()
        self.rect.center = vx
        self.count = 300
        self.state = "bom"
        self.hero = hero
        self.enemies = enemies
        self.bom_effects = bom_effects

    def control(self) -> None:
        """
        爆弾の動作を処理する
        """
        if self.count == 0:
            if self.state == "bom":
                self.image = pg.transform.rotozoom(self.exp_img, 180, 0.05)
                self.count = 30
                self.state = "explosion"
                self.call_effect(self.bom_effects) # 爆発エフェクト呼び出し
            else:
                # 爆発時に敵と衝突した場合スコアを増加
                collided_enemies = pg.sprite.spritecollide(self, self.enemies, True)
                if collided_enemies:
                    self.hero.add_score(100 * len(collided_enemies))
                self.kill()
        elif self.count > 0:
            self.count -= 1
            if self.state == "explosion":
                self.image = pg.transform.rotate(self.image, 90)

    def call_effect(self):
        """BomberZoneクラスを呼び出す"""

    def update(self) -> None:
        """
        爆弾の情報を更新する
        """
        self.control()


class BomberZone(pg.sprite.Sprite):
    """爆発エフェクトに関するクラス"""
    img = pg.image.load("explosion/burn.png")

    def __init__(self):
        pass


# スコア表示クラス
class Score:
    """
    スコア管理クラス
    スコアの追跡と更新を処理する
    """
    def __init__(self) -> None:
        """初期スコア変数を設定"""
        self.score = 0  # 初期スコアは0

    def add_score(self, points: int) -> None:
        """スコア加算"""
        self.score += points  # スコアを加算
        print(f"Score: {self.score}")  # 現在のスコアを表示（デバッグ用）

    def enemy_to_bom(self, boms: pg.sprite.Group, enemys: pg.sprite.Group) -> None:
        """
        敵と爆弾の接敵確認
        引数1 boms: 爆弾のグループ
        引数2 enemys: 敵のグループ
        """
        for bom in boms:
            if bom.state == "explosion":
                for enemy in enemys:
                    if bom.rect.colliderect(enemy.rect):  # 衝突判定
                        self.add_score(100)  # スコアを加算
                        enemy.kill()  # 敵を消去
                        break

    def update(self, screen: pg.Surface, font: pg.font) -> None:
        """
        スコア表示情報を更新する
        引数1 screen: 画面Surface
        引数2 font: 文字font
        """
        screen.fill((0,0,0), (10,10,150,36))
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))  # スコアを画面の左上に描画


# 制限時間初期化関数
def initialize_timer(time_limit: int) -> tuple:
    """
    タイマーの初期設定
    引数: time_limit: 制限時間（秒）
    戻り値: タイマーの開始時刻, 制限時間
    """
    start_ticks = pg.time.get_ticks()
    return start_ticks, time_limit


# 制限時間関数
def show_timer(screen: pg.Surface, font: pg.font.Font, start_ticks: int, time_limit: int) -> bool:
    """
    タイマーを表示し、時間切れから3秒後に終了
    引数:
    screen: 画面Surface
    font: 表示用フォント
    start_ticks: タイマーの開始時刻
    time_limit: 制限時間
    戻り値:
    タイマーが有効かどうか
    """
    elapsed_seconds = (pg.time.get_ticks() - start_ticks) / 1000
    time_left = time_limit - elapsed_seconds

    if time_left > 0:
        timer_text = font.render(f"Time: {int(time_left)}", True, (255, 255, 255))
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 50))
        return True  # タイマー継続
    else:
        # タイマーが終了し、3秒間timeoverを表示して終了
        if not hasattr(show_timer, "timeover_start"):
            show_timer.timeover_start = pg.time.get_ticks()

        timeover_text = font.render("timeover", True, (255, 0, 0))
        screen.blit(timeover_text, (WIDTH // 2 - timeover_text.get_width() // 2, HEIGHT // 2))

        if (pg.time.get_ticks() - show_timer.timeover_start) / 1000 > 3:
            return False  # タイマー終了

    return True


# 盤面領域判定関数
def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんやその他動的オブジェクトのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 50 or WIDTH - 50 < obj_rct.right:
        yoko = False
    if obj_rct.top < 100 or HEIGHT - 50 < obj_rct.bottom:
        tate = False
    for i in range(6):
        num = 100 * i
        if (100 + num) < obj_rct.left < (150 + num) or (100 + num) < obj_rct.right < (150 + num):
            for j in range(5):
                num = 100 * j
                if 150 + num < obj_rct.top < 200 + num or 150 + num < obj_rct.bottom < 200 + num:
                    yoko = False
                    tate = False
    return yoko, tate


# ゲームオーバー画面表示関数
def game_over(scr: pg.Surface) -> None:
    fonto = pg.font.SysFont("hg正楷書体pro", 70)
    gameover_txt = fonto.render("GAME OVER", True, (255, 0, 0))
    continue_txt = fonto.render("continue", True, (255, 255, 255))
    tend_txt = fonto.render("end", True, (255, 255, 255))
    picture = pg.image.load("images/hoshizora.png")  # 画像のパスを修正
    picture = pg.transform.scale(picture, (WIDTH, HEIGHT))  # 画面サイズにリサイズ
    scr.blit(picture, (0, 0))  # 背景として画像を描画
    scr.blit(gameover_txt, [(WIDTH / 2) - (gameover_txt.get_width() / 2), HEIGHT / 4])
    scr.blit(continue_txt, [(WIDTH / 2) - (continue_txt.get_width() / 2), HEIGHT / 2.3])
    scr.blit(tend_txt, [(WIDTH / 2) - (tend_txt.get_width() / 2), HEIGHT / 1.8])
    pg.display.update()
    time.sleep(5)


# タイトル画面表示関数
def show_title_screen(screen: pg.Surface) -> None:
    fonto = pg.font.SysFont("hg正楷書体pro", 70)
    title_txt = fonto.render("ボンバーこうかとん", True, (255, 255, 255))
    start_txt = fonto.render("START", True, (255, 255, 255))
    picture = pg.image.load("images/forest_dot1.jpg")  # 画像のパスを修正

    while True:
        screen.blit(picture, (0, 0))  # 背景として画像を描画
        screen.blit(title_txt, [(WIDTH / 2) - (title_txt.get_width() / 2), HEIGHT / 3])
        screen.blit(start_txt, [(WIDTH / 2) - (start_txt.get_width() / 2), HEIGHT / 2])
        pg.display.update()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                return


# 初期位置をランダムに決めるための関数
def random_position() -> list[tuple, tuple, tuple, tuple]:
    """
    盤面領域内の四隅の座標タプルをシャッフルしたリストを返す
    戻り値：タプルのリスト
    """
    pos = [
        (75, 125),
        (75, HEIGHT - 75),
        (WIDTH - 75, 125),
        (WIDTH - 75, HEIGHT - 75),
    ]
    return random.sample(pos, len(pos))


def main() -> None:
    """
    ゲームのメインループを制御する
    """
    pg.display.set_caption("ボンバーこうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    show_title_screen(screen) # タイトル画面表示
    bg_img = pg.image.load("images/bg_ver.1.0.png")  # 背景(完成版)

    position = random_position() # 敵味方の初期位置
    hero = Hero(position[-1])  # 主人公の初期位置
    boms = pg.sprite.Group()  # 爆弾クラスのグループ作成
    bom_effects = pg.sprite.Group() # 爆弾のエフェクトのブループ
    enemys = pg.sprite.Group()  # 敵のスプライトグループ
    for i, j in enumerate(position[:-1]):
        enemys.add(Enemy(i, j))  # 敵のインスタンス生成
    clock = pg.time.Clock()
    score = Score()  # スコアオブジェクトを作成

    pg.font.init() # フォントの初期化
    font = pg.font.Font(None, 36) # フォントを作成
    start_ticks, time_limit = initialize_timer(180) # 180秒(3分)に設定

    while show_timer(screen, font, start_ticks, time_limit):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:  # スペースキーで爆弾設置
                    boms.add(Bomber(hero.rct.center, hero, enemys, bom_effects))

        score.enemy_to_bom(boms, enemys) # 爆弾と敵の衝突判定

        screen.blit(bg_img, [0, 50])
        hero.update(screen) # 主人公(操作キャラ)クラスの更新
        enemys.update() # 敵グループの更新
        enemys.draw(screen)
        boms.update() # 爆弾グループの更新
        boms.draw(screen)
        score.update(screen, font) # スコア表示

        pg.display.update()
        clock.tick(60) # framerateを60に設定
    print("time up")
    return


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
