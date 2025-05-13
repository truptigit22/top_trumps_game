import random
import pygame
import json
import requests
from io import BytesIO
from typing import List, Dict, Optional, Any
from pygame.locals import QUIT, MOUSEBUTTONDOWN
from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.ttk import Progressbar

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Set up display for Pygame
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokémon Showdown")

# Load media
pygame.mixer.music.load('background_music.mp3')
pygame.mixer.music.play(-1)  # Loop background music
win_sound = pygame.mixer.Sound('win_sound.wav.mp3')
lose_sound = pygame.mixer.Sound('lose_sound.wav.mp3')
battle_background = pygame.image.load("battle_background.png")
battle_background = pygame.transform.scale(battle_background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Global music variables
background_music_enabled = True
music_volume = 1.0  # Default volume (maximum volume)

# Global difficulty setting (default = Medium)
difficulty_level = 'medium'

# Function to apply difficulty multiplier to opponent stats
def apply_difficulty(stats: Dict[str, int], level: str) -> Dict[str, int]:
    multiplier = {
        'easy': 0.8,
        'medium': 1.0,
        'hard': 1.2
    }.get(level, 1.0)
    return {k: int(v * multiplier) for k, v in stats.items()}

# Function to fetch Pokémon data
def get_pokemon_data(pokemon_id: int, adjust_stats=False) -> Optional[Dict[str, Any]]:
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    response = requests.get(url)
    try:
        pokemon = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Pokémon data: {e}")
        return None
    stats = {stat["stat"]["name"]: stat["base_stat"] for stat in pokemon["stats"]}
    if adjust_stats:
        stats = apply_difficulty(stats, difficulty_level)

    return {
        "name": pokemon["name"],
        "id": pokemon["id"],
        "height": pokemon["height"],
        "weight": pokemon.get("weight"),
        "stats": stats,
        "sprite": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon['id']}.png"
    }

# Flash animation (winner highlight)
def flash_winner(screen, color=(0, 255, 0), times=3):
    for _ in range(times):
        screen.fill(color)
        pygame.display.update()
        pygame.time.delay(200)
        screen.fill((255, 255, 255))
        pygame.display.update()
        pygame.time.delay(200)

# Function to load Pokémon images
def load_pokemon_image(url: str) -> Optional[pygame.Surface]:
    try:
        response = requests.get(url)
        image = pygame.image.load(BytesIO(response.content))
        return pygame.transform.scale(image, (200, 200))  # Resize for display
    except Exception as e:
        print(f"Failed to load Pokémon image: {e}")
        return None


# Function to update high scores
def update_high_scores(player_name: str, wins: int):
    try:
        with open("high_scores.json", "r") as file:
            high_scores = json.load(file)
    except FileNotFoundError:
        high_scores = {}

    if player_name in high_scores:
        high_scores[player_name] += wins
    else:
        high_scores[player_name] = wins

    with open("high_scores.json", "w") as file:
        json.dump(high_scores, file)

# Main Game Class
class PokemonGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon Showdown")
        self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        
        self.player_name = ""
        self.wins = 0
        self.losses = 0
        self.ties = 0

        # Start the game
        self.start_game()

    def start_game(self):
        # Clear the screen
        self.clear_screen()

        # Create buttons and labels on the game screen
        Label(self.root, text="Enter your name:", font=('Arial', 14)).pack(pady=10)
        self.name_entry = Entry(self.root, font=('Arial', 14))
        self.name_entry.pack(pady=10)
        
        Button(self.root, text="Start Game", font=('Arial', 14), command=self.play_game).pack(pady=20)

        # Settings Button on the Main Screen
        Button(self.root, text="Settings", font=('Arial', 14), command=self.open_settings).pack(pady=10)

        # Leaderboard Button
        Button(self.root, text="High Scores", font=('Arial', 14), command=self.show_high_scores).pack(pady=10)

    def open_settings(self):
        # Create the settings window
        settings_window = Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        # Toggle Music Button
        self.toggle_music_button = Button(settings_window, text="Toggle Music", font=('Arial', 14), command=self.toggle_music)
        self.toggle_music_button.pack(pady=10)

        # Volume Controls
        self.volume_label = Label(settings_window, text=f"Volume: {int(music_volume * 100)}%", font=('Arial', 14))
        self.volume_label.pack(pady=10)
        
        Button(settings_window, text="Increase Volume", font=('Arial', 14), command=self.increase_volume).pack(pady=5)
        Button(settings_window, text="Decrease Volume", font=('Arial', 14), command=self.decrease_volume).pack(pady=5)

        # Close Button for Settings
        Button(settings_window, text="Close", font=('Arial', 14), command=settings_window.destroy).pack(pady=20)

    def toggle_music(self):
        global background_music_enabled
        background_music_enabled = not background_music_enabled
        if background_music_enabled:
            pygame.mixer.music.play(-1, 0.0)  # Start music if enabled
            self.toggle_music_button.config(text="Stop Music")  # Update button text
        else:
            pygame.mixer.music.stop()  # Stop music if disabled
            self.toggle_music_button.config(text="Play Music")  # Update button text

    def increase_volume(self):
        global music_volume
        if music_volume < 1.0:
            music_volume += 0.1
            pygame.mixer.music.set_volume(music_volume)
            self.volume_label.config(text=f"Volume: {int(music_volume * 100)}%")  # Update volume label

    def decrease_volume(self):
        global music_volume
        if music_volume > 0.0:
            music_volume -= 0.1
            pygame.mixer.music.set_volume(music_volume)
            self.volume_label.config(text=f"Volume: {int(music_volume * 100)}%")  # Update volume label

    # Function to show high scores
    def show_high_scores(self):
        try:
          with open("high_scores.json", "r") as f:
            scores = json.load(f)
            top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
            message = "\n".join([f"{name}: {score}" for name, score in top_scores])
            messagebox.showinfo("High Scores", message)
        except FileNotFoundError:
            messagebox.showinfo("High Scores", "No high scores yet!")

    def play_game(self):
        # Clear the screen for the game
        self.clear_screen()

        available_pokemon = [get_pokemon_data(random.randint(1, 151)) for _ in range(3)]
        self.display_pokemon(available_pokemon)

        # Buttons for Pokémon selection
        Button(self.root, text=f"Select {available_pokemon[0]['name']}", command=lambda: self.choose_pokemon(available_pokemon[0])).pack(pady=10)
        Button(self.root, text=f"Select {available_pokemon[1]['name']}", command=lambda: self.choose_pokemon(available_pokemon[1])).pack(pady=10)
        Button(self.root, text=f"Select {available_pokemon[2]['name']}", command=lambda: self.choose_pokemon(available_pokemon[2])).pack(pady=10)

    def display_pokemon(self, available_pokemon: List[Dict[str, Any]]):
        screen.fill(WHITE)
        x_positions = [100, 300, 500]  # Positions for Pokémon images

        for i, pokemon in enumerate(available_pokemon):
            if pokemon:
                image = load_pokemon_image(pokemon["sprite"])
                if image:
                    screen.blit(image, (x_positions[i], 200))  # Display Pokémon images
                    font = pygame.font.Font(None, 36)
                    text = font.render(pokemon["name"], True, BLACK)
                    screen.blit(text, (x_positions[i], 400))

        pygame.display.update()  # Update the display

    def choose_pokemon(self, selected_pokemon):
        messagebox.showinfo("Pokemon Selected", f"You selected {selected_pokemon['name']}!")
        self.choose_stat(selected_pokemon)

    def choose_stat(self, player_pokemon):
        # Ask player to choose a stat
        stats = list(player_pokemon["stats"].keys()) + ["id", "height", "weight"]
        stat_choice = simpledialog.askstring("Choose Stat", f"Choose a stat:\n{', '.join(stats)}")

        if stat_choice:
            self.show_opponent(player_pokemon, stat_choice.lower())

    def show_stat_bar(frame, stat_name, value):
        Label(frame, text=stat_name, font=('Arial', 10)).pack()
        bar = Progressbar(frame, orient=HORIZONTAL, length=120, mode='determinate')
        bar['value'] = value
        bar['maximum'] = 200  # Adjust max if needed
        bar.pack(pady=2)


    def show_opponent(self, player_pokemon, stat_choice):
        opponent_pokemon = get_pokemon_data(random.randint(1, 151))
        messagebox.showinfo("Opponent", f"Opponent's Pokémon: {opponent_pokemon['name']}")

        player_value = player_pokemon["stats"].get(stat_choice, 0)
        opponent_value = opponent_pokemon["stats"].get(stat_choice, 0)

        result = ""
        if player_value > opponent_value:
            result = "You win!"
            self.wins += 1
            win_sound.play()
        elif player_value < opponent_value:
            result = "You lose!"
            self.losses += 1
            lose_sound.play()
        else:
            result = "It's a tie!"
            self.ties += 1

        # Stop music before showing result
        if background_music_enabled:
            pygame.mixer.music.stop()  # Stop the background music during result display
        
        # Show the result (win/lose/tie)
        messagebox.showinfo("Result", result)

        # Restart music after result
        if background_music_enabled:
            pygame.mixer.music.play(-1, 0.0)  # Start playing the background music again

        update_high_scores(self.player_name, self.wins)

        # Ask if the player wants to play again
        play_again = messagebox.askyesno("Play Again?", "Do you want to play again?")
        if play_again:
            self.play_game()
        else:
            self.show_summary()

    def show_summary(self):
        # Stop music when player doesn't want to play again
        if background_music_enabled:
            pygame.mixer.music.stop()  # Stop the music when game ends

        self.clear_screen()
        summary_text = f"Game Over\nWins: {self.wins}\nLosses: {self.losses}\nTies: {self.ties}"
        Label(self.root, text=summary_text, font=('Arial', 14)).pack(pady=20)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()


# Start the Tkinter GUI
def main():
    root = Tk()
    game = PokemonGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
