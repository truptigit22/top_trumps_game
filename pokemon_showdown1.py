import pygame
import requests
import json
import random
from io import BytesIO
from pygame.locals import *

pygame.init()
pygame.mixer.init()

# === GLOBALS ===
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokémon Showdown")

font = pygame.font.SysFont("Arial", 28)
small_font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

background_color = (240, 240, 255)
button_color = (100, 149, 237)
hover_color = (65, 105, 225)
text_color = (0, 0, 0)

# Music & sounds
pygame.mixer.music.load("background_music.mp3")
win_sound = pygame.mixer.Sound("win_sound.wav.mp3")
lose_sound = pygame.mixer.Sound("lose_sound.wav.mp3")
pygame.mixer.music.play(-1)

music_enabled = True
music_volume = 1.0
difficulty = "medium"

high_scores_file = "high_scores.json"

# === HELPERS ===
def draw_text(text, x, y, font=font, color=text_color):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))

def button(text, x, y, w, h, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    is_hover = x < mouse[0] < x + w and y < mouse[1] < y + h
    pygame.draw.rect(screen, hover_color if is_hover else button_color, (x, y, w, h))
    draw_text(text, x + 20, y + 10)
    if is_hover and click[0] == 1 and action:
        pygame.time.wait(200)
        action()

def fetch_pokemon(pokemon_id, adjusted=False):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    try:
        data = requests.get(url).json()
        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        if adjusted:
            multiplier = {'easy': 0.8, 'medium': 1.0, 'hard': 1.2}[difficulty]
            stats = {k: int(v * multiplier) for k, v in stats.items()}
        sprite = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
        return {
            "name": data["name"].capitalize(),
            "stats": stats,
            "sprite": sprite
        }
    except:
        return None

def load_image(url):
    try:
        response = requests.get(url)
        return pygame.transform.scale(pygame.image.load(BytesIO(response.content)), (150, 150))
    except:
        return None

def update_high_scores(player, wins):
    try:
        with open(high_scores_file, "r") as f:
            scores = json.load(f)
    except FileNotFoundError:
        scores = {}
    scores[player] = scores.get(player, 0) + wins
    with open(high_scores_file, "w") as f:
        json.dump(scores, f)

def load_high_scores():
    try:
        with open(high_scores_file, "r") as f:
            return json.load(f)
    except:
        return {}

# === GAME SCREENS ===
def main_menu():
    running = True
    while running:
        screen.fill(background_color)
        draw_text("Pokémon Showdown", 280, 80)

        button("Start Game", 320, 160, 180, 50, start_game)
        button("Settings", 320, 230, 180, 50, settings_menu)
        button("High Scores", 320, 300, 180, 50, show_high_scores)
        button("Quit", 320, 370, 180, 50, quit_game)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        pygame.display.update()
        clock.tick(60)

def settings_menu():
    global music_enabled, music_volume, difficulty

    running = True
    while running:
        screen.fill((220, 220, 250))
        draw_text("Settings", 340, 60)

        button(f"Music: {'On' if music_enabled else 'Off'}", 300, 140, 200, 50, toggle_music)
        button(f"Volume: {int(music_volume * 100)}%", 300, 210, 200, 50, adjust_volume)
        button(f"Difficulty: {difficulty.capitalize()}", 300, 280, 200, 50, cycle_difficulty)
        button("Back", 300, 350, 200, 50, main_menu)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()

        pygame.display.update()
        clock.tick(60)

def toggle_music():
    global music_enabled
    music_enabled = not music_enabled
    if music_enabled:
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()

def adjust_volume():
    global music_volume
    music_volume = (music_volume + 0.1) % 1.1
    pygame.mixer.music.set_volume(music_volume)

def cycle_difficulty():
    global difficulty
    levels = ["easy", "medium", "hard"]
    idx = (levels.index(difficulty) + 1) % 3
    difficulty = levels[idx]

def show_high_scores():
    scores = load_high_scores()
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]

    running = True
    while running:
        screen.fill(background_color)
        draw_text("High Scores", 330, 60)

        for i, (name, score) in enumerate(sorted_scores):
            draw_text(f"{name}: {score}", 320, 130 + i * 40)

        button("Back", 320, 400, 160, 50, main_menu)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()

        pygame.display.update()
        clock.tick(60)

def start_game():
    player_name = input_dialog("Enter your name:")
    if not player_name:
        return

    # Pokémon Selection
    player_choices = [fetch_pokemon(random.randint(1, 151)) for _ in range(3)]

    running = True
    while running:
        screen.fill(background_color)
        draw_text("Choose Your Pokémon", 280, 40)
        x_positions = [100, 325, 550]

        for i, pkm in enumerate(player_choices):
            img = load_image(pkm["sprite"])
            if img:
                screen.blit(img, (x_positions[i], 100))
            draw_text(pkm["name"], x_positions[i], 260)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
            if event.type == MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, x in enumerate(x_positions):
                    if x < mx < x + 150 and 100 < my < 250:
                        stat_choice = stat_dialog(player_choices[i])
                        if stat_choice:
                            battle(player_name, player_choices[i], stat_choice)
                        return

        pygame.display.update()
        clock.tick(60)

def input_dialog(prompt):
    from tkinter import simpledialog, Tk
    root = Tk()
    root.withdraw()
    return simpledialog.askstring("Input", prompt)

def stat_dialog(pokemon):
    stats = list(pokemon["stats"].keys())
    from tkinter import simpledialog, Tk
    root = Tk()
    root.withdraw()
    return simpledialog.askstring("Choose Stat", f"Choose one: {', '.join(stats)}")

def battle(player_name, player_pokemon, stat):
    opponent = fetch_pokemon(random.randint(1, 151), adjusted=True)
    player_val = player_pokemon["stats"].get(stat, 0)
    opponent_val = opponent["stats"].get(stat, 0)

    result = ""
    if player_val > opponent_val:
        result = "You Win!"
        win_sound.play()
        update_high_scores(player_name, 1)
    elif player_val < opponent_val:
        result = "You Lose!"
        lose_sound.play()
    else:
        result = "It's a Tie!"

    # Flash screen
    for _ in range(2):
        screen.fill((0, 255, 0) if "Win" in result else (255, 0, 0))
        pygame.display.update()
        pygame.time.delay(150)
        screen.fill(background_color)
        pygame.display.update()
        pygame.time.delay(150)

    show_result_screen(result)

def show_result_screen(result):
    running = True
    while running:
        screen.fill(background_color)
        draw_text(result, 330, 200)
        button("Play Again", 300, 300, 200, 50, start_game)
        button("Main Menu", 300, 370, 200, 50, main_menu)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()

        pygame.display.update()
        clock.tick(60)

def quit_game():
    pygame.quit()
    exit()

# === START GAME ===
main_menu()
