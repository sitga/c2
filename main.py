import pygame
import sys
import random
import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

pygame.init()

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

    def update(self, keys, dt: float):
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= dt

        if not self.is_boosting and self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen)

        speed = self.boost_speed if self.is_boosting else self.speed
        dx, dy = 0, 0

        if keys[pygame.K_w]:
            dy = -speed
            self.direction = "up"
        if keys[pygame.K_s]:
            dy = speed
            self.direction = "down"
        if keys[pygame.K_a]:
            dx = -speed
            self.direction = "left"
        if keys[pygame.K_d]:
            dx = speed
            self.direction = "right"

        if self.is_boosting:
            self.stamina = max(0, self.stamina - self.stamina_drain)
            if self.stamina <= 0:
                self.is_boosting = False

        self.x += dx
        self.y += dy

        # 限制玩家在屏幕范围内
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
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
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

    def handle_collision(self):
        for wall in self.walls:
            if self.player.rect.colliderect(wall):
                if self.player.direction == "up":
                    self.player.y = wall.bottom
                elif self.player.direction == "down":
                    self.player.y = wall.top - self.player.height
                elif self.player.direction == "left":
                    self.player.x = wall.right
                elif self.player.direction == "right":
                    self.player.x = wall.left - self.player.width
                else:
                    # 如果没有方向，根据重叠区域判断
                    overlap_left = (self.player.rect.right - wall.left)
                    overlap_right = (wall.right - self.player.rect.left)
                    overlap_top = (self.player.rect.bottom - wall.top)
                    overlap_bottom = (wall.bottom - self.player.rect.top)
                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap == overlap_left:
                        self.player.x = wall.left - self.player.width
                    elif min_overlap == overlap_right:
                        self.player.x = wall.right
                    elif min_overlap == overlap_top:
                        self.player.y = wall.top - self.player.height
                    else:
                        self.player.y = wall.bottom
                self.player.rect.x = int(self.player.x)
                self.player.rect.y = int(self.player.y)

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
            self.player.update(keys, dt)
            self.handle_collision()

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
        gold_text = self.font_small.render(f"金币: {self.gold}", True, GOLD)
        self.screen.blit(gold_text, (20, 20))

        target_text = self.font_tiny.render(f"目标: {self.target_gold}", True, GRAY)
        self.screen.blit(target_text, (20, 50))

        stamina_bar_width = 150
        stamina_height = 20
        stamina_ratio = self.player.stamina / self.player.max_stamina
        pygame.draw.rect(self.screen, GRAY, (20, 80, stamina_bar_width, stamina_height))
        pygame.draw.rect(self.screen, GREEN, (20, 80, int(stamina_bar_width * stamina_ratio), stamina_height))
        pygame.draw.rect(self.screen, BLACK, (20, 80, stamina_bar_width, stamina_height), 2)

        order_y = 150
        order_title = self.font_small.render("订单:", True, BLACK)
        self.screen.blit(order_title, (SCREEN_WIDTH - 200, order_y))

        for i, order in enumerate(self.orders[:5]):
            y = order_y + 35 + i * 50
            recipe = RECIPES[order.recipe_name]
            color = RED if order.remaining_time < 20 else BLACK
            text = self.font_tiny.render(f"{recipe.name} ({int(order.remaining_time)}s)", True, color)
            self.screen.blit(text, (SCREEN_WIDTH - 200, y))

            bar_width = 120
            time_ratio = max(0, order.remaining_time / order.time_limit)
            bar_color = GREEN if time_ratio > 0.5 else YELLOW if time_ratio > 0.25 else RED
            pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH - 200, y + 20, bar_width, 8))
            pygame.draw.rect(self.screen, bar_color, (SCREEN_WIDTH - 200, y + 20, int(bar_width * time_ratio), 8))

        inv_y = SCREEN_HEIGHT - 100
        inv_title = self.font_small.render("冰箱库存:", True, BLACK)
        self.screen.blit(inv_title, (20, inv_y))

        if self.fridge:
            items = [
                ("蔬菜", self.fridge.inventory.get(IngredientType.VEGETABLE, 0), GREEN),
                ("肉类", self.fridge.inventory.get(IngredientType.MEAT, 0), RED),
                ("面粉", self.fridge.inventory.get(IngredientType.FLOUR, 0), WHITE),
            ]
            for i, (name, count, color) in enumerate(items):
                x = 20 + i * 100
                rect = pygame.Rect(x, inv_y + 35, 80, 30)
                bg_color = color if self.selected_ingredient == [IngredientType.VEGETABLE, IngredientType.MEAT, IngredientType.FLOUR][i] else LIGHT_GRAY
                pygame.draw.rect(self.screen, bg_color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 2)
                text = self.font_tiny.render(f"{name}: {count}", True, BLACK)
                self.screen.blit(text, (x + 5, inv_y + 40))

        day_text = self.font_small.render(f"第 {self.day} 天", True, BLACK)
        self.screen.blit(day_text, (SCREEN_WIDTH // 2 - 50, 20))

        time_text = self.font_small.render(f"剩余: {int(self.day_timer)}s", True, BLACK)
        self.screen.blit(time_text, (SCREEN_WIDTH // 2 - 50, 50))

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
        title = self.font_large.render("米其林主厨", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render("Restaurant Tycoon", True, BLACK)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(subtitle, subtitle_rect)

        start_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 400, 200, 60)
        pygame.draw.rect(self.screen, GREEN, start_btn)
        pygame.draw.rect(self.screen, BLACK, start_btn, 3)
        start_text = self.font_medium.render("开始游戏", True, WHITE)
        start_rect = start_text.get_rect(center=start_btn.center)
        self.screen.blit(start_text, start_rect)

        help_text = self.font_tiny.render("WASD移动 | 鼠标左键交互 | 空格加速 | E键交互 | 1/2/3选择食材", True, GRAY)
        help_rect = help_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(help_text, help_rect)

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

        pause_text = self.font_large.render("暂停", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)

    def draw_settlement(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("今日结算", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        income_text = self.font_medium.render(f"今日收入: {self.day_income} 金币", True, GREEN)
        income_rect = income_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(income_text, income_rect)

        total_text = self.font_medium.render(f"总金币: {self.gold}", True, GOLD)
        total_rect = total_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
        self.screen.blit(total_text, total_rect)

        continue_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 60)
        pygame.draw.rect(self.screen, GREEN, continue_btn)
        pygame.draw.rect(self.screen, WHITE, continue_btn, 3)
        continue_text = self.font_medium.render("继续", True, WHITE)
        continue_rect = continue_text.get_rect(center=continue_btn.center)
        self.screen.blit(continue_text, continue_rect)

    def draw_upgrade(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("升级商店", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("恭喜获得米其林一星!", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        final_text = self.font_medium.render(f"最终金币: {self.gold}", True, WHITE)
        final_rect = final_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
        self.screen.blit(final_text, final_rect)

        restart_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 60)
        pygame.draw.rect(self.screen, GREEN, restart_btn)
        pygame.draw.rect(self.screen, WHITE, restart_btn, 3)
        restart_text = self.font_medium.render("重新开始", True, WHITE)
        restart_rect = restart_text.get_rect(center=restart_btn.center)
        self.screen.blit(restart_text, restart_rect)

    def handle_click(self, pos: Tuple[int, int]):
        if self.state == GameState.MAIN_MENU:
            start_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 400, 200, 60)
            if start_btn.collidepoint(pos):
                self.state = GameState.PLAYING

        elif self.state == GameState.SETTLEMENT:
            continue_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 60)
            if continue_btn.collidepoint(pos):
                self.day += 1
                self.day_income = 0
                self.day_timer = 180
                self.orders.clear()
                self.customers.clear()
                self.state = GameState.PLAYING

        elif self.state == GameState.GAME_OVER:
            restart_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 60)
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
