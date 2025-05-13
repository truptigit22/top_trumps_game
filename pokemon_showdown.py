import pygame
import random
import requests
import json
from io import BytesIO

# === Initialize Pygame ===
pygame.init()
pygame.mixer.init()

# === Screen Setup ===
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokémon Showdown")

# === Load Assets ===
battle_background = pygame.image.load("battle_background.png")
battle_background = pygame.transform.scale(battle_background, (SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.mixer.music.load("background_music.mp3")
win_sound = pygame.mixer.Sound("win_sound.wav.mp3")
lose_sound = pygame.mixer.Sound("lose_sound.wav.mp3")

# === Colors & Fonts ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 177, 76)
RED = (200, 0, 0)
GRAY = (220, 220, 220)

FONT = pygame.font.SysFont("arial", 24)

# === Globals ===
music_volume = 1.0
background_music_enabled = True
difficulty = "medium"

# === Difficulty Modifier ===
def apply_difficulty(stats, level):
    multiplier = {"easy": 0.8, "medium": 1.0, "hard": 1.2}.get(level, 1.0)
    return {k: int(v * multiplier) for k, v in stats.items()}

# === Fetch Pokémon Data ===
def get_pokemon_data(pokemon_id, adjust_stats=False):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    if adjust_stats:
        stats = apply_difficulty(stats, difficulty)
    return {
        "name": data["name"].capitalize(),
        "id": data["id"],
        "height": data["height"],
        "weight": data["weight"],
        "stats": stats,
        "sprite": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{data['id']}.png"
    }

# === Load Pokémon Image ===
def load_pokemon_image(url):
    try:
        img_data = requests.get(url).content
        image = pygame.image.load(BytesIO(img_data))
        return pygame.transform.scale(image, (150, 150))
    except Exception as e:
        print("Image load failed:", e)
        return None

# === Draw Text ===
def draw_text(text, x, y, color=BLACK):
    rendered = FONT.render(text, True, color)
    screen.blit(rendered, (x, y))

# === Draw Stat Bar ===
def draw_stat_bar(x, y, label, value, max_value=200):
    draw_text(label, x, y - 20)
    pygame.draw.rect(screen, GRAY, (x, y, 150, 20))
    pygame.draw.rect(screen, GREEN, (x, y, int((value / max_value) * 150), 20))

# === Display Pokémon ===
def display_pokemon(pokemon, x, y):
    image = load_pokemon_image(pokemon["sprite"])
    if image:
        screen.blit(image, (x, y))
    draw_text(pokemon["name"], x, y + 160)
    stats = pokemon["stats"]
    for i, (stat, val) in enumerate(stats.items()):
        draw_stat_bar(x, y + 190 + i * 30, stat, val)

# === Game Loop ===
def main():
    global music_volume, background_music_enabled, difficulty
    running = True
    clock = pygame.time.Clock()
    state = "menu"
    player_name = ""
    wins = 0
    losses = 0
    selected_stat = ""
    player_pokemon = None
    opponent_pokemon = None

    if background_music_enabled:
        pygame.mixer.music.play(-1)

    # Main game loop
    while running:
        screen.blit(battle_background, (0, 0))
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if state == "menu" and event.unicode.isprintable():
                    player_name += event.unicode
                if state == "menu" and event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                if state == "menu" and event.key == pygame.K_RETURN:
                    state = "select"

        # === Main Menu ===
        if state == "menu":
            draw_text("Enter Your Name:", 300, 200)
            draw_text(player_name, 300, 240)
            draw_text("Press Enter to Start", 300, 300)

        # === Pokémon Selection ===
        elif state == "select":
            pokemons = [get_pokemon_data(random.randint(1, 151)) for _ in range(3)]
            for i, pkmn in enumerate(pokemons):
                display_pokemon(pkmn, 50 + i * 250, 100)
            draw_text("Click to choose your Pokémon", 240, 500)
            pygame.display.flip()

            selected = False
            while not selected:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        selected = True
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        for i in range(3):
                            if 50 + i * 250 < mx < 200 + i * 250 and 100 < my < 250:
                                player_pokemon = pokemons[i]
                                selected = True
                                break
                clock.tick(30)
            state = "choose_stat"

        # === Stat Choice ===
        elif state == "choose_stat":
            screen.blit(battle_background, (0, 0))
            draw_text("Choose a stat to battle:", 250, 50)
            stats = list(player_pokemon["stats"].keys())
            buttons = []
            for i, stat in enumerate(stats):
                rect = pygame.Rect(300, 100 + i * 50, 200, 40)
                pygame.draw.rect(screen, RED, rect)
                draw_text(stat, 320, 110 + i * 50)
                buttons.append((rect, stat))
            pygame.display.flip()

            chosen = False
            while not chosen:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        chosen = True
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        for rect, stat in buttons:
                            if rect.collidepoint(mx, my):
                                selected_stat = stat
                                chosen = True
                                break
                clock.tick(30)
            state = "battle"

        # === Battle ===
        elif state == "battle":
            opponent_pokemon = get_pokemon_data(random.randint(1, 151), adjust_stats=True)
            screen.blit(battle_background, (0, 0))
            display_pokemon(player_pokemon, 100, 100)
            display_pokemon(opponent_pokemon, 500, 100)

            player_val = player_pokemon["stats"].get(selected_stat, 0)
            opponent_val = opponent_pokemon["stats"].get(selected_stat, 0)

            if player_val > opponent_val:
                result_text = "You Win!"
                wins += 1
                win_sound.play()
            elif player_val < opponent_val:
                result_text = "You Lose!"
                losses += 1
                lose_sound.play()
            else:
                result_text = "It's a Tie!"

            draw_text(result_text, 330, 500)
            pygame.display.flip()
            pygame.time.wait(3000)
            state = "select"

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

# === Run the Game ===
if __name__ == "__main__":
    main()
