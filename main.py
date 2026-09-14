import os
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore

# ---------- Game Constants ----------
GRAVITY = 1500
JUMP_VELOCITY = -450
PIPE_SPEED = 280
PIPE_GAP = 280
PIPE_WIDTH = 90
PIPE_SPAWN_INTERVAL = 1.5
BIRD_X = 120
BIRD_SIZE = 65
GROUND_HEIGHT = 100
FPS = 60


# ---------- Menu Screen ----------
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.5, 0.8, 1)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)
        Window.bind(size=self._resize_bg)

        layout = FloatLayout()
        layout.add_widget(Label(
            text="[b]FLAPPY BIRD[/b]", markup=True, font_size='48sp',
            color=(1, 0.85, 0.1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.78}, size_hint=(1, 0.2)
        ))

        play_btn = Button(
            text="PLAY", font_size='24sp',
            size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.2, 0.8, 0.2, 1)
        )
        play_btn.bind(on_press=self.go_play)
        layout.add_widget(play_btn)

        hs_btn = Button(
            text="HIGH SCORES", font_size='20sp',
            size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.38},
            background_color=(0.2, 0.5, 0.9, 1)
        )
        hs_btn.bind(on_press=self.go_highscores)
        layout.add_widget(hs_btn)

        quit_btn = Button(
            text="QUIT", font_size='20sp',
            size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.26},
            background_color=(0.9, 0.3, 0.3, 1)
        )
        quit_btn.bind(on_press=self.quit_app)
        layout.add_widget(quit_btn)

        self.add_widget(layout)

    def _resize_bg(self, *args):
        self.bg.size = Window.size

    def go_play(self, *args):
        game = self.manager.get_screen('game')
        game.reset()
        self.manager.current = 'game'

    def go_highscores(self, *args):
        self.manager.current = 'highscores'

    def quit_app(self, *args):
        App.get_running_app().stop()


# ---------- Game Screen ----------
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bird = {'x': BIRD_X, 'y': 0, 'vy': 0}
        self.pipes = []
        self.score = 0
        self.state = 'ready'
        self.spawn_timer = 0

        self.canvas_widget = Widget()
        self.add_widget(self.canvas_widget)

        self.score_label = Label(
            text="0", font_size='48sp', color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'top': 0.98},
            size_hint=(1, 0.15),
            outline_width=2, outline_color=(0, 0, 0, 1)
        )
        self.add_widget(self.score_label)

        self.ready_label = Label(
            text="[b]TAP TO START[/b]", markup=True, font_size='30sp',
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            size_hint=(1, 0.15),
            outline_width=2, outline_color=(0, 0, 0, 1)
        )
        self.add_widget(self.ready_label)

        self.pause_btn = Button(
            text="II", font_size='20sp',
            size_hint=(None, None), size=(60, 60),
            pos_hint={'right': 0.98, 'top': 0.98},
            background_color=(0.2, 0.2, 0.2, 0.7)
        )
        self.pause_btn.bind(on_press=self.pause_game)
        self.add_widget(self.pause_btn)

        Clock.schedule_interval(self.update, 1 / FPS)

    def reset(self):
        self.bird = {'x': BIRD_X, 'y': Window.height / 2, 'vy': 0}
        self.pipes = []
        self.score = 0
        self.spawn_timer = 0
        self.state = 'ready'
        self.score_label.text = "0"
        self.ready_label.opacity = 1
        self.pause_btn.disabled = False
        self.redraw()

    def on_touch_down(self, touch):
        if self.pause_btn.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.state == 'ready':
            self.state = 'playing'
            self.ready_label.opacity = 0
            self.bird['vy'] = JUMP_VELOCITY
        elif self.state == 'playing':
            self.bird['vy'] = JUMP_VELOCITY
        return True

    def pause_game(self, *args):
        if self.state == 'playing':
            self.state = 'paused'
            self.manager.current = 'pause'

    def resume_game(self):
        self.state = 'playing'

    def update(self, dt):
        if self.state != 'playing':
            return

        self.bird['vy'] += GRAVITY * dt
        self.bird['y'] -= self.bird['vy'] * dt

        if self.bird['y'] + BIRD_SIZE > Window.height:
            self.bird['y'] = Window.height - BIRD_SIZE
            self.bird['vy'] = 0

        if self.bird['y'] < GROUND_HEIGHT:
            self.game_over()
            return

        self.spawn_timer += dt
        if self.spawn_timer >= PIPE_SPAWN_INTERVAL:
            self.spawn_timer = 0
            min_gap_y = GROUND_HEIGHT + PIPE_GAP // 2 + 40
            max_gap_y = Window.height - PIPE_GAP // 2 - 40
            gap_y = random.randint(int(min_gap_y), int(max_gap_y)) if max_gap_y > min_gap_y else int(Window.height / 2)
            self.pipes.append({'x': Window.width, 'gap_y': gap_y, 'scored': False})

        for pipe in self.pipes:
            pipe['x'] -= PIPE_SPEED * dt

        self.pipes = [p for p in self.pipes if p['x'] + PIPE_WIDTH > -20]

        bird_rect = (self.bird['x'], self.bird['y'], BIRD_SIZE, BIRD_SIZE)
        for pipe in self.pipes:
            top_rect = (pipe['x'], pipe['gap_y'] + PIPE_GAP // 2, PIPE_WIDTH, Window.height)
            bot_rect = (pipe['x'], 0, PIPE_WIDTH, max(0, pipe['gap_y'] - PIPE_GAP // 2))
            if self.rect_collide(bird_rect, top_rect) or self.rect_collide(bird_rect, bot_rect):
                self.game_over()
                return
            if not pipe['scored'] and pipe['x'] + PIPE_WIDTH < self.bird['x']:
                pipe['scored'] = True
                self.score += 1
                self.score_label.text = str(self.score)

        self.redraw()

    def rect_collide(self, a, b):
        return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and
                a[1] < b[1] + b[3] and a[1] + a[3] > b[1])

    def redraw(self):
        self.canvas_widget.canvas.clear()
        with self.canvas_widget.canvas:
            Color(0.5, 0.8, 1)
            Rectangle(pos=(0, 0), size=(Window.width, Window.height))

            for pipe in self.pipes:
                Color(0.2, 0.8, 0.2)
                top_bottom = pipe['gap_y'] + PIPE_GAP // 2
                Rectangle(pos=(pipe['x'], top_bottom),
                          size=(PIPE_WIDTH, Window.height - top_bottom))
                Color(0.1, 0.6, 0.1)
                Rectangle(pos=(pipe['x'] - 5, top_bottom),
                          size=(PIPE_WIDTH + 10, 25))
                Color(0.2, 0.8, 0.2)
                bottom_top = max(0, pipe['gap_y'] - PIPE_GAP // 2)
                Rectangle(pos=(pipe['x'], 0), size=(PIPE_WIDTH, bottom_top))
                Color(0.1, 0.6, 0.1)
                Rectangle(pos=(pipe['x'] - 5, bottom_top - 25),
                          size=(PIPE_WIDTH + 10, 25))

            Color(0.8, 0.6, 0.3)
            Rectangle(pos=(0, 0), size=(Window.width, GROUND_HEIGHT))
            Color(0.6, 0.9, 0.3)
            Rectangle(pos=(0, GROUND_HEIGHT - 15), size=(Window.width, 15))

            Color(1, 0.85, 0.1)
            Ellipse(pos=(self.bird['x'], self.bird['y']), size=(BIRD_SIZE, BIRD_SIZE))
            Color(0.95, 0.6, 0.1)
            Ellipse(pos=(self.bird['x'] + 10, self.bird['y'] + 15), size=(35, 25))
            Color(1, 1, 1)
            Ellipse(pos=(self.bird['x'] + 38, self.bird['y'] + 38), size=(16, 16))
            Color(0, 0, 0)
            Ellipse(pos=(self.bird['x'] + 44, self.bird['y'] + 42), size=(8, 8))
            Color(1, 0.5, 0)
            Ellipse(pos=(self.bird['x'] + BIRD_SIZE - 5, self.bird['y'] + 22), size=(20, 12))

    def game_over(self):
        self.state = 'dead'
        App.get_running_app().add_score(self.score)
        self.manager.current = 'gameover'


# ---------- Pause Screen ----------
class PauseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0, 0, 0.75)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)
        Window.bind(size=self._resize_bg)

        layout = FloatLayout()
        layout.add_widget(Label(
            text="PAUSED", font_size='48sp', color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.72}, size_hint=(1, 0.2)
        ))

        resume_btn = Button(
            text="RESUME", font_size='24sp', size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.2, 0.8, 0.2, 1)
        )
        resume_btn.bind(on_press=self.resume)
        layout.add_widget(resume_btn)

        menu_btn = Button(
            text="MAIN MENU", font_size='20sp', size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.38},
            background_color=(0.9, 0.3, 0.3, 1)
        )
        menu_btn.bind(on_press=self.go_menu)
        layout.add_widget(menu_btn)

        self.add_widget(layout)

    def _resize_bg(self, *args):
        self.bg.size = Window.size

    def resume(self, *args):
        self.manager.get_screen('game').resume_game()
        self.manager.current = 'game'

    def go_menu(self, *args):
        self.manager.current = 'menu'


# ---------- Game Over Screen ----------
class GameOverScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.4, 0.1, 0.1, 1)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)
        Window.bind(size=self._resize_bg)

        layout = FloatLayout()
        layout.add_widget(Label(
            text="[b]GAME OVER[/b]", markup=True, font_size='48sp',
            color=(1, 0.9, 0.2, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.78}, size_hint=(1, 0.2)
        ))

        self.score_label = Label(
            text="Score: 0", font_size='32sp', color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.62}, size_hint=(1, 0.1)
        )
        layout.add_widget(self.score_label)

        self.best_label = Label(
            text="Best: 0", font_size='26sp', color=(1, 0.9, 0.2, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.52}, size_hint=(1, 0.1)
        )
        layout.add_widget(self.best_label)

        retry_btn = Button(
            text="PLAY AGAIN", font_size='24sp', size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.36},
            background_color=(0.2, 0.8, 0.2, 1)
        )
        retry_btn.bind(on_press=self.retry)
        layout.add_widget(retry_btn)

        menu_btn = Button(
            text="MAIN MENU", font_size='20sp', size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.23},
            background_color=(0.2, 0.5, 0.9, 1)
        )
        menu_btn.bind(on_press=self.go_menu)
        layout.add_widget(menu_btn)

        self.add_widget(layout)

    def _resize_bg(self, *args):
        self.bg.size = Window.size

    def on_enter(self):
        app = App.get_running_app()
        self.score_label.text = f"Score: {app.last_score}"
        self.best_label.text = f"Best: {app.get_best_score()}"

    def retry(self, *args):
        self.manager.get_screen('game').reset()
        self.manager.current = 'game'

    def go_menu(self, *args):
        self.manager.current = 'menu'


# ---------- High Score Screen ----------
class HighScoreScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.1, 0.2, 0.4, 1)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)
        Window.bind(size=self._resize_bg)

        layout = FloatLayout()
        layout.add_widget(Label(
            text="[b]HIGH SCORES[/b]", markup=True, font_size='40sp',
            color=(1, 0.9, 0.2, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.85}, size_hint=(1, 0.15)
        ))

        self.scores_box = BoxLayout(
            orientation='vertical', spacing=10, padding=20,
            size_hint=(0.8, 0.5),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        layout.add_widget(self.scores_box)

        back_btn = Button(
            text="BACK", font_size='22sp', size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'y': 0.05},
            background_color=(0.2, 0.5, 0.9, 1)
        )
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def _resize_bg(self, *args):
        self.bg.size = Window.size

    def on_enter(self):
        self.scores_box.clear_widgets()
        scores = App.get_running_app().get_top_scores()
        if not scores:
            self.scores_box.add_widget(Label(
                text="Koi score nahi. Khelo!",
                font_size='20sp', color=(1, 1, 1, 1)
            ))
        else:
            for i, s in enumerate(scores, 1):
                self.scores_box.add_widget(Label(
                    text=f"{i}.  {s}", font_size='24sp', color=(1, 1, 1, 1)
                ))

    def go_back(self, *args):
        self.manager.current = 'menu'


# ---------- App ----------
class FlappyBirdApp(App):
    def build(self):
        self.title = "Flappy Bird"
        store_path = os.path.join(self.user_data_dir, 'flappy_scores.json')
        self.store = JsonStore(store_path)
        self.last_score = 0

        sm = ScreenManager(transition=FadeTransition(duration=0.3))
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(PauseScreen(name='pause'))
        sm.add_widget(GameOverScreen(name='gameover'))
        sm.add_widget(HighScoreScreen(name='highscores'))
        return sm

    def add_score(self, score):
        self.last_score = score
        scores = self.store.get('scores')['list'] if self.store.exists('scores') else []
        scores.append(score)
        scores.sort(reverse=True)
        scores = scores[:10]
        self.store.put('scores', list=scores)

    def get_top_scores(self):
        if self.store.exists('scores'):
            return self.store.get('scores')['list'][:5]
        return []

    def get_best_score(self):
        if self.store.exists('scores'):
            scores = self.store.get('scores')['list']
            return max(scores) if scores else 0
        return 0


if __name__ == '__main__':
    FlappyBirdApp().run()
