import pygame
import sys
import random
import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
RED = (255, 80, 80)
GREEN = (80, 200, 80)
BLUE = (80, 150, 255)
YELLOW = (255, 220, 80)
ORANGE = (255, 150, 50)
BROWN = (139, 90, 43)
BEIGE = (245, 222, 179)
GOLD = (255, 215, 0)

def get_font(size):
    """获取支持中文的字体"""
    chinese_fonts = [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
    ]
    for font_path in chinese_fonts:
        try:
            return pygame.font.Font(font_path, size)
        except:
            continue
    return pygame.font.Font(None, size)

def draw_rounded_rect(screen, rect, color, radius=10, border=0):
    """绘制圆角矩形，支持边框"""
    x, y, w, h = rect
    if border == 0:
        pygame.draw.rect(screen, color, (x + radius, y, w - 2 * radius, h))
        pygame.draw.rect(screen, color, (x, y + radius, w, h - 2 * radius))
        pygame.draw.circle(screen, color, (x + radius, y + radius), radius)
        pygame.draw.circle(screen, color, (x + w - radius, y + radius), radius)
        pygame.draw.circle(screen, color, (x + radius, y + h - radius), radius)
        pygame.draw.circle(screen, color, (x + w - radius, y + h - radius), radius)
    else:
        pygame.draw.rect(screen, color, (x + radius, y, w - 2 * radius, border))
        pygame.draw.rect(screen, color, (x + radius, y + h - border, w - 2 * radius, border))
        pygame.draw.rect(screen, color, (x, y + radius, border, h - 2 * radius))
        pygame.draw.rect(screen, color, (x + w - border, y + radius, border, h - 2 * radius))
        for cx, cy in [(x + radius, y + radius), (x + w - radius, y + radius), 
                       (x + radius, y + h - radius), (x + w - radius, y + h - radius)]:
            pygame.draw.circle(screen, color, (cx, cy), radius, border)

def draw_text_centered(screen, text, font, x, y, color=BLACK):
    """绘制居中文字"""
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)

class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    SETTLEMENT = auto()
    UPGRADE = auto()
    GAME_OVER = auto()

class IngredientType(Enum):
    VEGETABLE = auto()
    MEAT = auto()
    FLOUR = auto()
    DISH = auto()

class Recipe:
    def __init__(self, name: str, ingredients: List[IngredientType], cook_time: int, price: int):
        self.name = name
        self.ingredients = ingredients
        self.cook_time = cook_time
        self.price = price
        self.unlocked = False

RECIPES = {
    "salad": Recipe("蔬菜沙拉", [IngredientType.VEGETABLE], 3, 30),
    "steak": Recipe("牛排", [IngredientType.MEAT], 5, 80),
    "pasta": Recipe("意面", [IngredientType.FLOUR, IngredientType.MEAT], 6, 60),
    "burger": Recipe("汉堡", [IngredientType.FLOUR, IngredientType.MEAT, IngredientType.VEGETABLE], 7, 100),
}

@dataclass
class Ingredient:
    type: IngredientType
    name: str
    color: Tuple[int, int, int]
    is_cooked: bool = False
    cook_progress: float = 0.0

class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.speed = 5
        self.boost_speed = 8
        self.stamina = 100
        self.max_stamina = 100
        self.stamina_regen = 0.5
        self.stamina_drain = 1.5
        self.is_boosting = False
        self.holding: Optional[Ingredient] = None
        self.interaction_cooldown = 0
        self.direction = "down"
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def update(self, keys, dt: float, walls: List[pygame.Rect]):
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= dt

        if not self.is_boosting and self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen)

        speed = self.boost_speed if self.is_boosting else self.speed
        dx, dy = 0, 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -speed
            self.direction = "up"
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = speed
            self.direction = "down"
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -speed
            self.direction = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = speed
            self.direction = "right"

        if self.is_boosting:
            self.stamina = max(0, self.stamina - self.stamina_drain)
            if self.stamina <= 0:
                self.is_boosting = False

        new_x = self.x + dx
        new_y = self.y + dy

        can_move_x = True
        test_rect = pygame.Rect(new_x, self.y, self.width, self.height)
        for wall in walls:
            if test_rect.colliderect(wall):
                can_move_x = False
                break
        if can_move_x:
            self.x = new_x

        can_move_y = True
        test_rect = pygame.Rect(self.x, new_y, self.width, self.height)
        for wall in walls:
            if test_rect.colliderect(wall):
                can_move_y = False
                break
        if can_move_y:
            self.y = new_y

        self.x = max(20, min(SCREEN_WIDTH - 20 - self.width, self.x))
        self.y = max(20, min(SCREEN_HEIGHT - 20 - self.height, self.y))
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, screen: pygame.Surface):
        color = ORANGE if self.is_boosting else YELLOW
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

        if self.holding:
            hold_rect = pygame.Rect(self.x + 5, self.y - 15, 10, 10)
            pygame.draw.rect(screen, self.holding.color, hold_rect)

    def toggle_boost(self):
        if self.stamina > 20:
            self.is_boosting = not self.is_boosting
        else:
            self.is_boosting = False

    def get_interact_rect(self) -> pygame.Rect:
        offset = 10
        if self.direction == "up":
            return pygame.Rect(self.x, self.y - offset - 10, self.width, 10)
        elif self.direction == "down":
            return pygame.Rect(self.x, self.y + self.height + offset, self.width, 10)
        elif self.direction == "left":
            return pygame.Rect(self.x - offset - 10, self.y, 10, self.height)
        else:
            return pygame.Rect(self.x + self.width + offset, self.y, 10, self.height)

class Appliance:
    def __init__(self, x: float, y: float, width: float, height: float, name: str, appliance_type: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = name
        self.type = appliance_type
        self.color = GRAY
        self.contents: Optional[Ingredient] = None
        self.is_cooking = False
        self.cook_timer = 0

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

        font = get_font(24)
        text = font.render(self.name, True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

        if self.contents:
            indicator = pygame.Rect(self.rect.x + 5, self.rect.y + 5, 10, 10)
            pygame.draw.rect(screen, self.contents.color, indicator)

class Stove(Appliance):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 80, 80, "炉灶", "stove")
        self.color = DARK_GRAY
        self.cook_progress = 0

    def update(self, dt: float):
        if self.is_cooking and self.contents:
            self.cook_progress += dt
            recipe = None
            for r in RECIPES.values():
                if len(r.ingredients) == 1 and r.ingredients[0] == self.contents.type:
                    recipe = r
                    break

            if recipe:
                self.contents.cook_progress = min(1.0, self.cook_progress / recipe.cook_time)
                if self.cook_progress >= recipe.cook_time:
                    self.contents.is_cooked = True
                    self.is_cooking = False

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        if self.is_cooking:
            bar_width = self.rect.width - 10
            bar_height = 8
            progress = self.contents.cook_progress if self.contents else 0
            pygame.draw.rect(screen, GRAY, (self.rect.x + 5, self.rect.bottom - 15, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (self.rect.x + 5, self.rect.bottom - 15, int(bar_width * progress), bar_height))

class Fridge(Appliance):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 100, 120, "冰箱", "fridge")
        self.color = BLUE
        self.inventory = {
            IngredientType.VEGETABLE: 20,
            IngredientType.MEAT: 15,
            IngredientType.FLOUR: 15,
        }
        self.max_capacity = 50

    def take_ingredient(self, ing_type: IngredientType) -> Optional[Ingredient]:
        if self.inventory.get(ing_type, 0) > 0:
            self.inventory[ing_type] -= 1
            names = {
                IngredientType.VEGETABLE: ("蔬菜", GREEN),
                IngredientType.MEAT: ("肉类", RED),
                IngredientType.FLOUR: ("面粉", WHITE),
            }
            name, color = names[ing_type]
            return Ingredient(ing_type, name, color)
        return None

    def restock(self, ing_type: IngredientType, amount: int, cost: int) -> bool:
        total = sum(self.inventory.values())
        if total + amount <= self.max_capacity:
            self.inventory[ing_type] = self.inventory.get(ing_type, 0) + amount
            return True
        return False

class Counter(Appliance):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 80, 60, "上菜区", "counter")
        self.color = BEIGE

class Customer:
    def __init__(self, x: float, y: float, is_critic: bool = False):
        self.x = x
        self.y = y
        self.width = 35
        self.height = 35
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.is_critic = is_critic
        self.patience = 60 if is_critic else 120
        self.max_patience = self.patience
        self.order: Optional[str] = None
        self.state = "waiting"
        self.color = GOLD if is_critic else BLUE

    def update(self, dt: float):
        self.patience -= dt
        if self.patience <= 0:
            self.state = "left"

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

        if self.order:
            font = get_font(20)
            text = font.render(self.order[:4], True, BLACK)
            screen.blit(text, (self.rect.x, self.rect.y - 20))

        bar_width = self.width
        patience_ratio = self.patience / self.max_patience
        bar_color = GREEN if patience_ratio > 0.5 else YELLOW if patience_ratio > 0.25 else RED
        pygame.draw.rect(screen, GRAY, (self.rect.x, self.rect.y - 10, bar_width, 6))
        pygame.draw.rect(screen, bar_color, (self.rect.x, self.rect.y - 10, int(bar_width * patience_ratio), 6))

class Order:
    def __init__(self, recipe_name: str, customer: Customer, time_limit: float):
        self.recipe_name = recipe_name
        self.customer = customer
        self.time_limit = time_limit
        self.remaining_time = time_limit
        self.completed = False

    def update(self, dt: float):
        self.remaining_time -= dt

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("米其林主厨")
        self.clock = pygame.time.Clock()
        self.font_large = get_font(72)
        self.font_medium = get_font(48)
        self.font_small = get_font(36)
        self.font_tiny = get_font(24)

        self.reset_game()

    def reset_game(self):
        self.state = GameState.MAIN_MENU
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200)
        self.gold = 500
        self.target_gold = 50000
        self.day = 1
        self.orders: List[Order] = []
        self.customers: List[Customer] = []
        self.stoves: List[Stove] = []
        self.fridge: Optional[Fridge] = None
        self.counter: Optional[Counter] = None
        self.walls: List[pygame.Rect] = []
        self.selected_ingredient: Optional[IngredientType] = None
        self.day_income = 0
        self.unlocked_recipes = ["salad"]
        self.michelin_stars = 0
        self.transition_alpha = 0
        self.is_transitioning = False
        self.transition_target = None

        self.setup_kitchen()
        self.spawn_timer = 0
        self.day_timer = 180

    def setup_kitchen(self):
        self.walls = [
            pygame.Rect(0, 0, SCREEN_WIDTH, 20),
            pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20),
            pygame.Rect(0, 0, 20, SCREEN_HEIGHT),
            pygame.Rect(SCREEN_WIDTH - 20, 0, 20, SCREEN_HEIGHT),
        ]

        self.fridge = Fridge(50, 100)
        self.stoves = [
            Stove(200, 100),
            Stove(300, 100),
        ]
        self.counter = Counter(450, 100)

        self.walls.extend([
            pygame.Rect(40, 90, 120, 140),
            pygame.Rect(190, 90, 200, 100),
            pygame.Rect(440, 90, 100, 80),
        ])

    def spawn_customer(self):
        if len(self.customers) >= 5:
            return

        x = random.choice([50, SCREEN_WIDTH - 100])
        y = random.randint(300, SCREEN_HEIGHT - 100)
        is_critic = random.random() < 0.1
        customer = Customer(x, y, is_critic)

        available = [r for r in self.unlocked_recipes]
        if available:
            customer.order = random.choice(available)
            self.customers.append(customer)
            order = Order(customer.order, customer, 60 if is_critic else 90)
            self.orders.append(order)

    def check_interactions(self):
        interact_rect = self.player.get_interact_rect()

        if self.fridge and interact_rect.colliderect(self.fridge.rect):
            return "fridge"

        for stove in self.stoves:
            if interact_rect.colliderect(stove.rect):
                return ("stove", stove)

        if self.counter and interact_rect.colliderect(self.counter.rect):
            return ("counter", self.counter)

        for customer in self.customers:
            if interact_rect.colliderect(customer.rect):
                return ("customer", customer)

        return None

    def complete_order(self, order: Order, ingredient: Ingredient):
        order.completed = True
        recipe = RECIPES[order.recipe_name]

        quality = "perfect" if ingredient.cook_progress >= 0.9 else "normal" if ingredient.cook_progress >= 0.5 else "failed"

        if quality == "perfect":
            reward = int(recipe.price * 1.5)
        elif quality == "normal":
            reward = recipe.price
        else:
            reward = recipe.price // 2

        if order.customer.is_critic:
            reward *= 2

        self.gold += reward
        self.day_income += reward

        if order.customer in self.customers:
            self.customers.remove(order.customer)
        self.orders.remove(order)

    def update(self, dt: float):
        if self.state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            self.player.update(keys, dt, self.walls)

            self.spawn_timer += dt
            if self.spawn_timer >= 8:
                self.spawn_customer()
                self.spawn_timer = 0

            for stove in self.stoves:
                stove.update(dt)

            for customer in self.customers:
                customer.update(dt)

            for order in self.orders[:]:
                order.update(dt)
                if order.remaining_time <= 0 and not order.completed:
                    if order.customer in self.customers:
                        self.customers.remove(order.customer)
                    self.orders.remove(order)

            self.customers = [c for c in self.customers if c.state != "left"]

            self.day_timer -= dt
            if self.day_timer <= 0:
                self.end_day()

            if self.gold >= self.target_gold:
                self.michelin_stars = 1
                self.state = GameState.GAME_OVER

        elif self.is_transitioning:
            self.transition_alpha += 5
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.is_transitioning = False
                if self.transition_target:
                    self.state = self.transition_target
                    self.transition_target = None

    def end_day(self):
        self.state = GameState.SETTLEMENT

    def start_transition(self, target_state: GameState):
        self.is_transitioning = True
        self.transition_alpha = 0
        self.transition_target = target_state

    def draw_ui(self):
        panel_alpha = 230
        
        panel_gold = pygame.Surface((180, 70), pygame.SRCALPHA)
        draw_rounded_rect(panel_gold, (0, 0, 180, 70), (*WHITE, panel_alpha))
        self.screen.blit(panel_gold, (20, 20))
        draw_rounded_rect(self.screen, (20, 20, 180, 70), DARK_GRAY, radius=10, border=2)
        
        draw_text_centered(self.screen, f"金币: {self.gold}", self.font_small, 110, 45, GOLD)
        draw_text_centered(self.screen, f"目标: {self.target_gold}", self.font_tiny, 110, 75, GRAY)

        stamina_panel = pygame.Surface((180, 50), pygame.SRCALPHA)
        draw_rounded_rect(stamina_panel, (0, 0, 180, 50), (*WHITE, panel_alpha))
        self.screen.blit(stamina_panel, (20, 100))
        draw_rounded_rect(self.screen, (20, 100, 180, 50), DARK_GRAY, radius=10, border=2)
        
        stamina_bar_width = 140
        stamina_height = 16
        stamina_ratio = self.player.stamina / self.player.max_stamina
        stamina_x, stamina_y = 40, 125
        draw_text_centered(self.screen, "体力", self.font_tiny, 55, stamina_y - 8, BLACK)
        pygame.draw.rect(self.screen, GRAY, (stamina_x, stamina_y, stamina_bar_width, stamina_height))
        pygame.draw.rect(self.screen, GREEN, (stamina_x, stamina_y, int(stamina_bar_width * stamina_ratio), stamina_height))

        center_panel = pygame.Surface((200, 80), pygame.SRCALPHA)
        draw_rounded_rect(center_panel, (0, 0, 200, 80), (*WHITE, panel_alpha))
        center_x, center_y = SCREEN_WIDTH // 2 - 100, 20
        self.screen.blit(center_panel, (center_x, center_y))
        draw_rounded_rect(self.screen, (center_x, center_y, 200, 80), DARK_GRAY, radius=10, border=2)
        
        draw_text_centered(self.screen, f"第 {self.day} 天", self.font_small, SCREEN_WIDTH // 2, 50, BLACK)
        timer_color = RED if self.day_timer < 30 else BLACK
        draw_text_centered(self.screen, f"剩余: {int(self.day_timer)}s", self.font_small, SCREEN_WIDTH // 2, 80, timer_color)

        if self.orders:
            order_panel_height = 60 + len(self.orders[:5]) * 55
            order_panel = pygame.Surface((220, order_panel_height), pygame.SRCALPHA)
            draw_rounded_rect(order_panel, (0, 0, 220, order_panel_height), (*WHITE, panel_alpha))
            order_x, order_y = SCREEN_WIDTH - 240, 150
            self.screen.blit(order_panel, (order_x, order_y))
            draw_rounded_rect(self.screen, (order_x, order_y, 220, order_panel_height), DARK_GRAY, radius=10, border=2)
            
            draw_text_centered(self.screen, "当前订单", self.font_small, order_x + 110, order_y + 25, BLACK)

            for i, order in enumerate(self.orders[:5]):
                y = order_y + 55 + i * 55
                recipe = RECIPES[order.recipe_name]
                color = RED if order.remaining_time < 20 else BLACK
                
                draw_text_centered(self.screen, f"{recipe.name}", self.font_tiny, order_x + 110, y, color)

                bar_width = 180
                time_ratio = max(0, order.remaining_time / order.time_limit)
                bar_color = GREEN if time_ratio > 0.5 else YELLOW if time_ratio > 0.25 else RED
                pygame.draw.rect(self.screen, GRAY, (order_x + 20, y + 18, bar_width, 10))
                pygame.draw.rect(self.screen, bar_color, (order_x + 20, y + 18, int(bar_width * time_ratio), 10))

        if self.fridge:
            inv_panel = pygame.Surface((340, 80), pygame.SRCALPHA)
            draw_rounded_rect(inv_panel, (0, 0, 340, 80), (*WHITE, panel_alpha))
            inv_x, inv_y = 20, SCREEN_HEIGHT - 100
            self.screen.blit(inv_panel, (inv_x, inv_y))
            draw_rounded_rect(self.screen, (inv_x, inv_y, 340, 80), DARK_GRAY, radius=10, border=2)
            
            draw_text_centered(self.screen, "冰箱库存 (按1/2/3选择)", self.font_tiny, inv_x + 170, inv_y + 18, BLACK)

            items = [
                ("蔬菜", self.fridge.inventory.get(IngredientType.VEGETABLE, 0), GREEN, IngredientType.VEGETABLE),
                ("肉类", self.fridge.inventory.get(IngredientType.MEAT, 0), RED, IngredientType.MEAT),
                ("面粉", self.fridge.inventory.get(IngredientType.FLOUR, 0), WHITE, IngredientType.FLOUR),
            ]
            for i, (name, count, color, ing_type) in enumerate(items):
                x = inv_x + 25 + i * 105
                is_selected = self.selected_ingredient == ing_type
                bg_color = color if is_selected else LIGHT_GRAY
                
                item_rect = (x, inv_y + 38, 95, 35)
                pygame.draw.rect(self.screen, bg_color, item_rect)
                pygame.draw.rect(self.screen, ORANGE if is_selected else BLACK, item_rect, 2)
                draw_text_centered(self.screen, f"{name}: {count}", self.font_tiny, x + 47, inv_y + 55, BLACK)

    def draw(self):
        self.screen.fill(BEIGE)

        if self.state == GameState.MAIN_MENU:
            self.draw_main_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.PAUSED:
            self.draw_game()
            self.draw_pause_overlay()
        elif self.state == GameState.SETTLEMENT:
            self.draw_settlement()
        elif self.state == GameState.UPGRADE:
            self.draw_upgrade()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()

        if self.is_transitioning or self.transition_alpha > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(self.transition_alpha)
            self.screen.blit(overlay, (0, 0))

        pygame.display.flip()

    def draw_main_menu(self):
        menu_panel = pygame.Surface((600, 500), pygame.SRCALPHA)
        draw_rounded_rect(menu_panel, (0, 0, 600, 500), (*WHITE, 240))
        panel_x, panel_y = SCREEN_WIDTH // 2 - 300, 100
        self.screen.blit(menu_panel, (panel_x, panel_y))
        draw_rounded_rect(self.screen, (panel_x, panel_y, 600, 500), DARK_GRAY, radius=15, border=3)
        
        draw_text_centered(self.screen, "米其林主厨", self.font_large, SCREEN_WIDTH // 2, panel_y + 130, GOLD)
        draw_text_centered(self.screen, "Restaurant Tycoon", self.font_medium, SCREEN_WIDTH // 2, panel_y + 190, DARK_GRAY)

        start_btn = pygame.Rect(SCREEN_WIDTH // 2 - 120, panel_y + 260, 240, 70)
        pygame.draw.rect(self.screen, GREEN, start_btn)
        pygame.draw.rect(self.screen, BLACK, start_btn, 3)
        draw_text_centered(self.screen, "开始游戏", self.font_medium, start_btn.centerx, start_btn.centery, WHITE)

        help_bg = pygame.Rect(panel_x + 30, panel_y + 360, 540, 110)
        pygame.draw.rect(self.screen, LIGHT_GRAY, help_bg)
        draw_text_centered(self.screen, "操作说明", self.font_small, SCREEN_WIDTH // 2, panel_y + 385, BLACK)
        draw_text_centered(self.screen, "WASD/方向键移动 | 鼠标拿放 | 空格加速 | 1/2/3选食材", self.font_tiny, SCREEN_WIDTH // 2, panel_y + 420, DARK_GRAY)
        draw_text_centered(self.screen, "靠近设备后点击交互", self.font_tiny, SCREEN_WIDTH // 2, panel_y + 445, DARK_GRAY)
        draw_text_centered(self.screen, "重要: 请切换英文输入法并点击游戏窗口获得焦点!", self.font_tiny, SCREEN_WIDTH // 2, panel_y + 470, RED)

    def draw_game(self):
        for wall in self.walls:
            pygame.draw.rect(self.screen, BROWN, wall)

        if self.fridge:
            self.fridge.draw(self.screen)
        for stove in self.stoves:
            stove.draw(self.screen)
        if self.counter:
            self.counter.draw(self.screen)

        for customer in self.customers:
            customer.draw(self.screen)

        self.player.draw(self.screen)

        interact = self.check_interactions()
        if interact:
            hint_text = "按E交互" if interact != "fridge" else "点击拿取食材"
            hint = self.font_tiny.render(hint_text, True, BLACK)
            self.screen.blit(hint, (self.player.rect.x, self.player.rect.y - 40))

        self.draw_ui()

    def draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        panel_x, panel_y = SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100
        pause_panel = pygame.Surface((400, 200), pygame.SRCALPHA)
        draw_rounded_rect(pause_panel, (0, 0, 400, 200), (*WHITE, 240))
        self.screen.blit(pause_panel, (panel_x, panel_y))
        draw_rounded_rect(self.screen, (panel_x, panel_y, 400, 200), DARK_GRAY, radius=15, border=3)

        draw_text_centered(self.screen, "游戏暂停", self.font_large, SCREEN_WIDTH // 2, panel_y + 70, DARK_GRAY)
        draw_text_centered(self.screen, "按 ESC 继续游戏", self.font_small, SCREEN_WIDTH // 2, panel_y + 130, GRAY)

    def draw_settlement(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        panel_x, panel_y = SCREEN_WIDTH // 2 - 250, 120
        panel = pygame.Surface((500, 420), pygame.SRCALPHA)
        draw_rounded_rect(panel, (0, 0, 500, 420), (*WHITE, 245))
        self.screen.blit(panel, (panel_x, panel_y))
        draw_rounded_rect(self.screen, (panel_x, panel_y, 500, 420), DARK_GRAY, radius=15, border=3)

        draw_text_centered(self.screen, "今日结算", self.font_large, SCREEN_WIDTH // 2, panel_y + 60, GOLD)
        
        divider = pygame.Rect(panel_x + 50, panel_y + 110, 400, 2)
        pygame.draw.rect(self.screen, LIGHT_GRAY, divider)

        draw_text_centered(self.screen, f"第 {self.day} 天结束", self.font_medium, SCREEN_WIDTH // 2, panel_y + 155, BLACK)
        draw_text_centered(self.screen, f"今日收入: +{self.day_income}", self.font_medium, SCREEN_WIDTH // 2, panel_y + 210, GREEN)
        draw_text_centered(self.screen, f"总金币: {self.gold}", self.font_medium, SCREEN_WIDTH // 2, panel_y + 270, GOLD)
        
        progress = min(100, int(self.gold / self.target_gold * 100))
        draw_text_centered(self.screen, f"米其林进度: {progress}%", self.font_small, SCREEN_WIDTH // 2, panel_y + 320, ORANGE)

        continue_btn = pygame.Rect(SCREEN_WIDTH // 2 - 110, panel_y + 350, 220, 55)
        pygame.draw.rect(self.screen, GREEN, continue_btn)
        pygame.draw.rect(self.screen, DARK_GRAY, continue_btn, 2)
        draw_text_centered(self.screen, "下一天", self.font_medium, continue_btn.centerx, continue_btn.centery, WHITE)

    def draw_upgrade(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("升级商店", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        panel_x, panel_y = SCREEN_WIDTH // 2 - 280, 120
        panel = pygame.Surface((560, 420), pygame.SRCALPHA)
        draw_rounded_rect(panel, (0, 0, 560, 420), (*WHITE, 245))
        self.screen.blit(panel, (panel_x, panel_y))
        draw_rounded_rect(self.screen, (panel_x, panel_y, 560, 420), GOLD, radius=15, border=4)

        draw_text_centered(self.screen, "恭喜获得", self.font_medium, SCREEN_WIDTH // 2, panel_y + 110, BLACK)
        draw_text_centered(self.screen, "米其林一星!", self.font_large, SCREEN_WIDTH // 2, panel_y + 165, GOLD)
        
        divider = pygame.Rect(panel_x + 60, panel_y + 215, 440, 2)
        pygame.draw.rect(self.screen, GOLD, divider)

        draw_text_centered(self.screen, f"最终金币: {self.gold}", self.font_medium, SCREEN_WIDTH // 2, panel_y + 260, GOLD)
        draw_text_centered(self.screen, f"用时: {self.day} 天", self.font_medium, SCREEN_WIDTH // 2, panel_y + 305, BLACK)

        restart_btn = pygame.Rect(SCREEN_WIDTH // 2 - 120, panel_y + 345, 240, 55)
        pygame.draw.rect(self.screen, GREEN, restart_btn)
        pygame.draw.rect(self.screen, DARK_GRAY, restart_btn, 2)
        draw_text_centered(self.screen, "重新开始", self.font_medium, restart_btn.centerx, restart_btn.centery, WHITE)

    def handle_click(self, pos: Tuple[int, int]):
        if self.state == GameState.MAIN_MENU:
            start_btn = pygame.Rect(SCREEN_WIDTH // 2 - 120, 360, 240, 70)
            if start_btn.collidepoint(pos):
                self.state = GameState.PLAYING

        elif self.state == GameState.SETTLEMENT:
            continue_btn = pygame.Rect(SCREEN_WIDTH // 2 - 110, 470, 220, 55)
            if continue_btn.collidepoint(pos):
                self.day += 1
                self.day_income = 0
                self.day_timer = 180
                self.orders.clear()
                self.customers.clear()
                self.state = GameState.PLAYING

        elif self.state == GameState.GAME_OVER:
            restart_btn = pygame.Rect(SCREEN_WIDTH // 2 - 120, 465, 240, 55)
            if restart_btn.collidepoint(pos):
                self.reset_game()

        elif self.state == GameState.PLAYING:
            self.handle_game_click(pos)

    def handle_game_click(self, pos: Tuple[int, int]):
        interaction = self.check_interactions()

        if interaction == "fridge" and self.fridge:
            if not self.player.holding:
                # 从冰箱拿取食材
                if self.selected_ingredient:
                    ingredient = self.fridge.take_ingredient(self.selected_ingredient)
                    if ingredient:
                        self.player.holding = ingredient
            else:
                # 把食材放回冰箱（可选功能）
                pass

        elif isinstance(interaction, tuple):
            if interaction[0] == "stove":
                stove = interaction[1]
                if self.player.holding and not stove.contents:
                    stove.contents = self.player.holding
                    self.player.holding = None
                    stove.is_cooking = True
                    stove.cook_progress = 0
                elif stove.contents and not self.player.holding:
                    self.player.holding = stove.contents
                    stove.contents = None
                    stove.is_cooking = False
                    stove.cook_progress = 0

            elif interaction[0] == "counter":
                counter = interaction[1]
                if self.player.holding and self.player.holding.is_cooked:
                    for order in self.orders:
                        if not order.completed:
                            recipe = RECIPES.get(order.recipe_name)
                            if recipe and self.player.holding.type in recipe.ingredients:
                                self.complete_order(order, self.player.holding)
                                self.player.holding = None
                                break

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.player.toggle_boost()

                    elif event.key == pygame.K_e:
                        pass

                    elif event.key == pygame.K_ESCAPE:
                        if self.state == GameState.PLAYING:
                            self.state = GameState.PAUSED
                        elif self.state == GameState.PAUSED:
                            self.state = GameState.PLAYING

                    elif event.key == pygame.K_1:
                        self.selected_ingredient = IngredientType.VEGETABLE
                    elif event.key == pygame.K_2:
                        self.selected_ingredient = IngredientType.MEAT
                    elif event.key == pygame.K_3:
                        self.selected_ingredient = IngredientType.FLOUR

            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
