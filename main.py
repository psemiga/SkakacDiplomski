import random
import pygame

from ZODB import FileStorage, DB
import transaction
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping


storage = FileStorage.FileStorage('database/BazaSkakac.fs')  
db = DB(storage)
connection = db.open() 
root = connection.root() 

if not hasattr(root, 'all_games'):
    print("Inicijalizacija 'all_games' jer nije pronađena u bazi.")
    root.all_games = PersistentList() 
    transaction.commit()

if not hasattr(root, 'users'):
    root.users = PersistentMapping() 
    transaction.commit()

if not hasattr(root, 'daily_challenges'):
    print("Inicijalizacija 'daily_challenges' jer nije pronađena u bazi.")
    root.daily_challenges = PersistentList() 
    transaction.commit()



from datetime import datetime, timedelta

izazovi = [
    {
        'challenge_id': 1,
        'description': 'Prikupi 20 zvijezda u jednoj igri',
        'reward': 20,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    },
    {
        'challenge_id': 2,
        'description': 'Pretrpi 5 sudara s raketama',
        'reward': 30,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    },
    {
        'challenge_id': 3,
        'description': 'Dođi do udaljenosti od 1000m',
        'reward': 100,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    }
]

for challenge in izazovi:
    if not any(ch['challenge_id'] == challenge['challenge_id'] for ch in root.daily_challenges):
        root.daily_challenges.append(PersistentMapping(challenge))
        print(f"Izazov dodan: {challenge['description']}")

transaction.commit()


for user_name, user_data in root.users.items():
    if 'lifetime_stars' not in user_data:
        user_data['lifetime_stars'] = 0

    if 'games_played' not in user_data:
        user_data['games_played'] = 0

    if 'crashes_lasers' not in user_data:
        user_data['crashes_lasers'] = 0

    if 'crashes_rockets' not in user_data:
        user_data['crashes_rockets'] = 0

    if 'record' not in user_data:
        user_data['record'] = 0

    if 'stars' not in user_data:
        user_data['stars'] = 0

    if 'jetpacks' not in user_data:
        user_data['jetpacks'] = PersistentList(['jetpack'])
    elif not isinstance(user_data['jetpacks'], PersistentList):
        user_data['jetpacks'] = PersistentList(user_data['jetpacks'])

    if 'active_jetpack' not in user_data:
        user_data['active_jetpack'] = 'jetpack'

    if 'characters' not in user_data:
        user_data['characters'] = PersistentList(['odijelo'])
    elif not isinstance(user_data['characters'], PersistentList):
        user_data['characters'] = PersistentList(user_data['characters'])

    if 'active_character' not in user_data:
        user_data['active_character'] = 'odijelo'

    if 'completed_challenges' not in user_data:
        user_data['completed_challenges'] = PersistentList()
    elif not isinstance(user_data['completed_challenges'], PersistentList):
        user_data['completed_challenges'] = PersistentList(user_data['completed_challenges'])

transaction.commit()

print("Svi podaci u root.all_games prilikom pokretanja igre:")
if hasattr(root, 'all_games') and root.all_games:
    for game in root.all_games:
        print(game)
else:
    print("Baza je prazna ili nema zapisa u 'all_games'!")

  

high_score = max((game['distance'] for game in root.all_games), default=0)
lifetime_stars = sum(user_data.get('lifetime_stars', 0) for user_data in root.users.values())


pygame.init()
pygame.mixer.init()

pygame.mixer.music.load('music/background.mp3')
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)

raketa_sound = pygame.mixer.Sound('music/raketa.wav')
zvijezda_sound = pygame.mixer.Sound('music/zvijezda.wav')
laser_sound = pygame.mixer.Sound('music/laser.wav')
kraj_sound = pygame.mixer.Sound('music/kraj.wav')
letenje_sound = pygame.mixer.Sound('music/letenje.mp3')

music_volume = 0.1
effects_volume = 0.7

def primijeni_glasnoce():
    pygame.mixer.music.set_volume(music_volume)

    raketa_sound.set_volume(effects_volume)
    zvijezda_sound.set_volume(effects_volume)
    laser_sound.set_volume(effects_volume * 0.8)
    kraj_sound.set_volume(effects_volume)
    letenje_sound.set_volume(effects_volume * 0.8)


primijeni_glasnoce()

letenje_channel = pygame.mixer.Channel(1)

WIDTH = 1000
HEIGHT = 600
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Skakac by Petar Semiga')
fps = 60
timer = pygame.time.Clock()
font = pygame.font.Font('freesansbold.ttf', 32)
lines = [0, WIDTH / 4, 2 * WIDTH / 4, 3 * WIDTH / 4]
game_speed = 3
pause = False
init_y = HEIGHT - 130
player_y = init_y
booster = False
counter = 0
y_velocity = 0
gravity = 0.4
new_laser = True
laser = []
distance = 0
restart_cmd = False
walk_counter = 0 
TOP_MARGIN = 50  
BOTTOM_MARGIN = 130
rocket_counter = 0
rocket_active = False
rocket_delay = 0
rocket_coords = []
background_x = 0
background_speed = 2

start_screen_image = pygame.image.load('images/start.png')
start_screen_image = pygame.transform.scale(start_screen_image, (WIDTH, HEIGHT)) 

end_screen_image = pygame.image.load('images/kraj.png')
end_screen_image = pygame.transform.scale(end_screen_image, (WIDTH, HEIGHT))  

oprez_image = pygame.image.load('images/oprez.png')
oprez_image = pygame.transform.scale(oprez_image, (80, 80))

rocket_image = pygame.image.load('images/raketa.png')
rocket_image = pygame.transform.scale(rocket_image, (70, 70))

okvir_image = pygame.image.load('images/okvir.png')
okvir_image = pygame.transform.scale(okvir_image, (WIDTH, 50))

background_image = pygame.image.load('images/background.png')
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

LASER_DEBLJINA = 10
LASER_KRAJ_SIZE = 34

PLAYER_WIDTH = 75
PLAYER_HEIGHT = 105

def ucitaj_sliku_lika(putanja):
    slika = pygame.image.load(putanja)
    return pygame.transform.smoothscale(slika, (PLAYER_WIDTH, PLAYER_HEIGHT))


likovi_po_karakteru = {
    "odijelo": {
        "jetpack": [
            ucitaj_sliku_lika('images/lik_odijelo1.png'),
            ucitaj_sliku_lika('images/lik_odijelo2.png'),
            ucitaj_sliku_lika('images/lik_odijelo3.png'),
            ucitaj_sliku_lika('images/lik_odijelo4.png'),
            ucitaj_sliku_lika('images/lik_odijelo5.png'),
        ],
        "jetpack2": [
            ucitaj_sliku_lika('images/lik_odijelo1_2.png'),
            ucitaj_sliku_lika('images/lik_odijelo2_2.png'),
            ucitaj_sliku_lika('images/lik_odijelo3_2.png'),
            ucitaj_sliku_lika('images/lik_odijelo4_2.png'),
            ucitaj_sliku_lika('images/lik_odijelo5_2.png'),
        ],
        "jetpack3": [
            ucitaj_sliku_lika('images/lik_odijelo1_3.png'),
            ucitaj_sliku_lika('images/lik_odijelo2_3.png'),
            ucitaj_sliku_lika('images/lik_odijelo3_3.png'),
            ucitaj_sliku_lika('images/lik_odijelo4_3.png'),
            ucitaj_sliku_lika('images/lik_odijelo5_3.png'),
        ],
    },

    "astronaut": {
        "jetpack": [
            ucitaj_sliku_lika('images/lik_astronaut1.png'),
            ucitaj_sliku_lika('images/lik_astronaut2.png'),
            ucitaj_sliku_lika('images/lik_astronaut3.png'),
            ucitaj_sliku_lika('images/lik_astronaut4.png'),
            ucitaj_sliku_lika('images/lik_astronaut5.png'),
        ],
        "jetpack2": [
            ucitaj_sliku_lika('images/lik_astronaut1_2.png'),
            ucitaj_sliku_lika('images/lik_astronaut2_2.png'),
            ucitaj_sliku_lika('images/lik_astronaut3_2.png'),
            ucitaj_sliku_lika('images/lik_astronaut4_2.png'),
            ucitaj_sliku_lika('images/lik_astronaut5_2.png'),
        ],
        "jetpack3": [
            ucitaj_sliku_lika('images/lik_astronaut1_3.png'),
            ucitaj_sliku_lika('images/lik_astronaut2_3.png'),
            ucitaj_sliku_lika('images/lik_astronaut3_3.png'),
            ucitaj_sliku_lika('images/lik_astronaut4_3.png'),
            ucitaj_sliku_lika('images/lik_astronaut5_3.png'),
        ],
    },

        "kralj": {
        "jetpack": [
            ucitaj_sliku_lika('images/lik_kralj1.png'),
            ucitaj_sliku_lika('images/lik_kralj2.png'),
            ucitaj_sliku_lika('images/lik_kralj3.png'),
            ucitaj_sliku_lika('images/lik_kralj4.png'),
            ucitaj_sliku_lika('images/lik_kralj5.png'),
        ],
        "jetpack2": [
            ucitaj_sliku_lika('images/lik_kralj1_2.png'),
            ucitaj_sliku_lika('images/lik_kralj2_2.png'),
            ucitaj_sliku_lika('images/lik_kralj3_2.png'),
            ucitaj_sliku_lika('images/lik_kralj4_2.png'),
            ucitaj_sliku_lika('images/lik_kralj5_2.png'),
        ],
        "jetpack3": [
            ucitaj_sliku_lika('images/lik_kralj1_3.png'),
            ucitaj_sliku_lika('images/lik_kralj2_3.png'),
            ucitaj_sliku_lika('images/lik_kralj3_3.png'),
            ucitaj_sliku_lika('images/lik_kralj4_3.png'),
            ucitaj_sliku_lika('images/lik_kralj5_3.png'),
        ],
    },
}

star_image = pygame.image.load('images/zvijezda.png')
star_image = pygame.transform.scale(star_image, (40, 40)) 

gameover_image = pygame.image.load('images/gameover.png')
gameover_image = pygame.transform.scale(gameover_image, (WIDTH, HEIGHT))

leaderboard_image = pygame.image.load('images/leaderboard.png')
leaderboard_image = pygame.transform.scale(leaderboard_image, (WIDTH, HEIGHT))

pauza_image = pygame.image.load('images/pauza.png')
pauza_image = pygame.transform.scale(pauza_image, (WIDTH, HEIGHT))

postavke_image = pygame.image.load('images/postavke.png')
postavke_image = pygame.transform.scale(postavke_image, (WIDTH, HEIGHT))

gumb_image = pygame.image.load('images/gumb.png')
gumb_image = pygame.transform.smoothscale(gumb_image, (220, 55))

gumb2_image = pygame.image.load('images/gumb2.png')
gumb2_image = pygame.transform.smoothscale(gumb2_image, (220, 55))

gumb3_image = pygame.image.load('images/gumb3.png')
gumb3_image = pygame.transform.smoothscale(gumb3_image, (220, 55))

rocket_sound_played = False



def generiraj_zvijezdu():
    x = random.randint(WIDTH, WIDTH + 300) 
    y = random.randint(50, HEIGHT - 150)  
    speed = random.randint(2, 5)  
    return {"rect": pygame.Rect(x, y, 40, 40), "speed": speed}

stars = [generiraj_zvijezdu() for _ in range(3)] 



def show_start_screen():
    player_name = ''
    input_active = False 
    input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 20, 300, 50) 
    color_active = pygame.Color('red')
    color_inactive = pygame.Color('black')
    color = color_inactive
    font_input = pygame.font.Font(None, 48)

    while True:
        screen.blit(start_screen_image, (0, 0))
        button_width = 300
        button_height = 80
        button_x = WIDTH // 2 - button_width // 2  
        button_y = HEIGHT // 2 + 100

        start_button = nacrtaj_gumb(button_x + 40, button_y + 10, 'Započni', gumb_image)

        pygame.draw.rect(screen, 'white', input_box)
        pygame.draw.rect(screen, color, input_box, 2) 
        text_surface = font_input.render(player_name, True, 'black')
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):  
                    if player_name:
                        player_name = player_name.strip()
                        player_name = player_name.lower()
                        return player_name  
                elif input_box.collidepoint(event.pos): 
                    input_active = True
                    color = color_active
                else:
                    input_active = False
                    color = color_inactive
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_RETURN:  
                    input_active = False
                    color = color_inactive
                elif event.key == pygame.K_BACKSPACE:  
                    player_name = player_name[:-1]
                else:
                    player_name += event.unicode 

def nacrtaj_gumb(x, y, tekst, slika_gumba, boja_teksta='white', velicina_fonta=26, tekst_y_offset=0):
    rect = pygame.Rect(x, y, 220, 55)

    screen.blit(slika_gumba, (x, y))

    font_gumb = pygame.font.Font('freesansbold.ttf', velicina_fonta)
    tekst_surface = font_gumb.render(tekst, True, boja_teksta)

    tekst_rect = tekst_surface.get_rect(
        center=(rect.centerx, rect.centery + tekst_y_offset)
    )

    screen.blit(tekst_surface, tekst_rect)

    return rect

def nacrtaj_mali_gumb(x, y, tekst, slika_gumba=gumb_image, boja_teksta='white'):
    rect = pygame.Rect(x, y, 90, 45)

    mala_slika = pygame.transform.smoothscale(slika_gumba, (90, 45))
    screen.blit(mala_slika, (x, y))

    font_mali = pygame.font.Font('freesansbold.ttf', 26)
    tekst_surface = font_mali.render(tekst, True, boja_teksta)
    tekst_rect = tekst_surface.get_rect(center=rect.center)
    screen.blit(tekst_surface, tekst_rect)

    return rect

def show_settings_screen():
    global music_volume, effects_volume

    while True:
        screen.blit(postavke_image, (0, 0))

        font_text = pygame.font.Font('freesansbold.ttf', 30)

        music_text = font_text.render(f"Glazba: {int(music_volume * 100)}%", True, 'white')
        music_rect = music_text.get_rect(center=(WIDTH // 2, 190))
        screen.blit(music_text, music_rect)

        effects_text = font_text.render(f"Efekti: {int(effects_volume * 100)}%", True, 'white')
        effects_rect = effects_text.get_rect(center=(WIDTH // 2, 290))
        screen.blit(effects_text, effects_rect)

        music_minus = nacrtaj_mali_gumb(WIDTH // 2 - 190, 170, "-", gumb2_image)
        music_plus = nacrtaj_mali_gumb(WIDTH // 2 + 100, 170, "+", gumb_image)

        effects_minus = nacrtaj_mali_gumb(WIDTH // 2 - 190, 270, "-", gumb2_image)
        effects_plus = nacrtaj_mali_gumb(WIDTH // 2 + 100, 270, "+", gumb_image)

        back_button = nacrtaj_gumb(WIDTH // 2 - 110, HEIGHT - 100, "Natrag", gumb2_image)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if music_minus.collidepoint(event.pos):
                    music_volume = max(0.0, music_volume - 0.1)
                    primijeni_glasnoce()

                if music_plus.collidepoint(event.pos):
                    music_volume = min(1.0, music_volume + 0.1)
                    primijeni_glasnoce()

                if effects_minus.collidepoint(event.pos):
                    effects_volume = max(0.0, effects_volume - 0.1)
                    primijeni_glasnoce()

                if effects_plus.collidepoint(event.pos):
                    effects_volume = min(1.0, effects_volume + 0.1)
                    primijeni_glasnoce()

                if back_button.collidepoint(event.pos):
                    return
                

def show_pause_menu(player_name):
    global pause, booster

    pause = True
    booster = False
    letenje_channel.stop()

    while True:
        screen.blit(pauza_image, (0, 0))

        continue_button = nacrtaj_gumb(WIDTH // 2 - 110, 220, "Nastavi", gumb_image)
        settings_button = nacrtaj_gumb(WIDTH // 2 - 110, 295, "Postavke", gumb_image)
        challenges_button = nacrtaj_gumb(WIDTH // 2 - 110, 370, "Izazovi", gumb_image)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause = False
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint(event.pos):
                    pause = False
                    return

                if settings_button.collidepoint(event.pos):
                    show_settings_screen()

                if challenges_button.collidepoint(event.pos):
                    show_challenges(player_name)

def nacrtaj_cijenu_sa_zvijezdom(button_rect, cijena):
    font_button = pygame.font.Font('freesansbold.ttf', 22)

    mala_zvijezda = pygame.transform.smoothscale(star_image, (20, 20))

    kupi_surface = font_button.render("Kupi", True, 'white')
    cijena_surface = font_button.render(str(cijena), True, 'white')

    razmak = 7

    ukupna_sirina = (
        kupi_surface.get_width()
        + razmak
        + cijena_surface.get_width()
        + 4
        + mala_zvijezda.get_width()
    )

    start_x = button_rect.centerx - ukupna_sirina // 2
    center_y = button_rect.centery

    kupi_y = center_y - kupi_surface.get_height() // 2
    cijena_y = center_y - cijena_surface.get_height() // 2
    zvijezda_y = center_y - mala_zvijezda.get_height() // 2

    screen.blit(kupi_surface, (start_x, kupi_y))

    cijena_x = start_x + kupi_surface.get_width() + razmak
    screen.blit(cijena_surface, (cijena_x, cijena_y))

    zvijezda_x = cijena_x + cijena_surface.get_width() + 4
    screen.blit(mala_zvijezda, (zvijezda_x, zvijezda_y))

def show_end_screen(player_name, zadnji_rezultat):
    while True:
        screen.blit(gameover_image, (0, 0))

        settings_corner_button = nacrtaj_gumb(
            20,
            20,
            'Postavke',
            gumb_image,
            'white',
            22
        )

        font_end = pygame.font.Font(None, 40)
        font_result = pygame.font.Font(None, 44)

        result_text = font_result.render(f"Zadnji rezultat: {zadnji_rezultat} m", True, 'white')
        result_rect = result_text.get_rect(center=(WIDTH // 2, 180))
        screen.blit(result_text, result_rect)
        font_stats = pygame.font.Font(None, 32)
        user_data = root.users[player_name]

        stats = [
            f"Broj odigranih igara: {user_data['games_played']}",
            f"Najveća udaljenost: {user_data['record']} m",
            f"Ukupno zvijezda: {user_data['lifetime_stars']}",
            f"Sudari s laserima: {user_data['crashes_lasers']}",
            f"Sudari s raketama: {user_data['crashes_rockets']}",
        ]

        stats_start_y = 220

        for i, stat in enumerate(stats):
            text_surface = font_stats.render(stat, True, 'white')
            text_rect = text_surface.get_rect(center=(WIDTH // 2, stats_start_y + i * 35))
            screen.blit(text_surface, text_rect)

        button_width = 220
        button_height = 55
        button_spacing_x = 20
        button_spacing_y = 20

        row1_y = HEIGHT - 150
        row2_y = row1_y + button_height + button_spacing_y

        start_x_4 = (WIDTH - (4 * button_width + 3 * button_spacing_x)) // 2
        start_x_2 = (WIDTH - (2 * button_width + button_spacing_x)) // 2

        retry_button = nacrtaj_gumb(
            start_x_4,
            row1_y,
            'Ponovno',
            gumb_image,
            'white',
            24
        )

        shop_button = nacrtaj_gumb(
            start_x_4 + button_width + button_spacing_x,
            row1_y,
            'Trgovina',
            gumb_image,
            'white',
            24
        )

        leaderboard_button = nacrtaj_gumb(
            start_x_4 + 2 * (button_width + button_spacing_x),
            row1_y,
            'Rezultati',
            gumb_image,
            'white',
            24
        )

        challenges_button = nacrtaj_gumb(
            start_x_4 + 3 * (button_width + button_spacing_x),
            row1_y,
            'Izazovi',
            gumb_image,
            'white',
            24
        )

        reset_button = nacrtaj_gumb(
            start_x_2,
            row2_y,
            'Reset baze',
            gumb2_image,
            'white',
            24
        )

        exit_button = nacrtaj_gumb(
            start_x_2 + button_width + button_spacing_x,
            row2_y,
            'Izlaz',
            gumb2_image,
            'white',
            24
        )
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if settings_corner_button.collidepoint(event.pos):
                    show_settings_screen()
                if retry_button.collidepoint(event.pos):
                    return True

                if exit_button.collidepoint(event.pos):
                    transaction.commit()
                    connection.close()
                    db.close()
                    pygame.quit()
                    exit()

                if reset_button.collidepoint(event.pos):
                    root.all_games.clear()
                    root.users.clear()
                    transaction.commit()
                    connection.close()
                    db.close()
                    pygame.quit()
                    exit()

                if shop_button.collidepoint(event.pos):
                    show_shop(player_name)

                if leaderboard_button.collidepoint(event.pos):
                    show_leaderboard_screen()

                if challenges_button.collidepoint(event.pos):
                    show_challenges(player_name)

def show_leaderboard_screen():
    while True:
        screen.blit(leaderboard_image, (0, 0))

        font_title = pygame.font.Font(None, 44)
        font_board = pygame.font.Font(None, 32)

        title1 = font_title.render("Najveći rezultati", True, 'white')
        screen.blit(title1, (WIDTH // 4 - 160, 170))

        sorted_games = sorted(root.all_games, key=lambda x: x['distance'], reverse=True)

        y_offset = 225
        for i, game in enumerate(sorted_games[:5]):
            text = f"{i + 1}. {game['player']}: {game['distance']} m"
            entry = font_board.render(text, True, 'white')
            screen.blit(entry, (WIDTH // 4 - 160, y_offset))
            y_offset += 45

        title2 = font_title.render("Najviše zvijezda", True, 'white')
        screen.blit(title2, (3 * WIDTH // 4 - 160, 170))

        sorted_users = sorted(
            root.users.items(),
            key=lambda x: x[1].get('lifetime_stars', 0),
            reverse=True
        )

        y_offset = 225
        for i, (name, data) in enumerate(sorted_users[:5]):
            lifetime_stars = data.get('lifetime_stars', 0)
            text = f"{i + 1}. {name}: {lifetime_stars} zvijezda"
            entry = font_board.render(text, True, 'white')
            screen.blit(entry, (3 * WIDTH // 4 - 160, y_offset))
            y_offset += 45

        back_button = nacrtaj_gumb(WIDTH // 2 - 110, HEIGHT - 90, 'Natrag', gumb2_image)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return



def show_shop(player_name):
    while True:
        screen.fill((0, 0, 0))  
        shop_image = pygame.image.load('images/shop.png') 
        shop_image = pygame.transform.scale(shop_image, (WIDTH, HEIGHT))
        screen.blit(shop_image, (0, 0))

        font_shop = pygame.font.Font(None, 36)
        user_data = root.users[player_name]

        screen.blit(font_shop.render(f"Zvijezde: {user_data['stars']}", True, 'white'), (50, 20))

        back_button = nacrtaj_gumb(WIDTH - 240, 15, 'Natrag', gumb2_image)

        item_width = 115
        item_height = 115
        button_width = 150
        button_height = 36
        column_spacing = 300

        start_x = 100

        jetpack_y = 190
        jetpack_button_y = 315

        lik_y = 365
        lik_name_y = 495
        lik_price_y = 528

        jetpack_buttons = []
        jetpack_images = [
            {"name": "jetpack", "image": "jetpack_basic.png", "price": 0},
            {"name": "jetpack2", "image": "jetpack_gold.png", "price": 3},
            {"name": "jetpack3", "image": "jetpack_diamond.png", "price": 100},
        ]

        x_offset = start_x

        for jetpack in jetpack_images:
            jetpack_img_path = f'images/{jetpack["image"]}'
            jetpack_img = pygame.image.load(jetpack_img_path)
            jetpack_img = pygame.transform.smoothscale(jetpack_img, (item_width, item_height))

            screen.blit(jetpack_img, (x_offset + 25, jetpack_y))

            if jetpack["name"] == user_data.get('active_jetpack', 'jetpack'):
                button_color = 'yellow'
                button_text = "Odabran"
            elif jetpack["name"] in user_data['jetpacks']:
                button_color = 'green'
                button_text = "Odaberi"
            else:
                button_color = 'white'
                button_text = f"Kupi"

            if jetpack["name"] == user_data.get('active_jetpack', 'jetpack'):
                button_image = gumb3_image
            else:
                button_image = gumb_image

            button_rect = pygame.Rect(x_offset + 7, jetpack_button_y, button_width, button_height)

            screen.blit(
                pygame.transform.smoothscale(button_image, (button_width, button_height)),
                (button_rect.x, button_rect.y)
            )

            if jetpack["name"] not in user_data['jetpacks']:
                nacrtaj_cijenu_sa_zvijezdom(button_rect, jetpack["price"])
            else:
                font_button = pygame.font.Font('freesansbold.ttf', 22)
                text_surface = font_button.render(button_text, True, 'white')
                text_rect = text_surface.get_rect(center=button_rect.center)
                screen.blit(text_surface, text_rect)


            jetpack_buttons.append({
                "rect": button_rect,
                "name": jetpack["name"],
                "price": jetpack["price"]
            })

            x_offset += column_spacing

        character_buttons = []

        likovi_images = [
            {"id": "odijelo", "name": "Odijelo", "image": "lik_odijelo.png", "price": 0},
            {"id": "astronaut", "name": "Astronaut", "image": "lik_astronaut.png", "price": 80},
            {"id": "kralj", "name": "Kralj", "image": "lik_kralj.png", "price": 100},
        ]

        x_offset = start_x

        for lik in likovi_images:
            lik_img_path = f'images/{lik["image"]}'
            lik_img = pygame.image.load(lik_img_path)
            lik_img = pygame.transform.smoothscale(lik_img, (item_width, item_height))

            screen.blit(lik_img, (x_offset + 25, lik_y))

            label_text = font_shop.render(lik["name"], True, 'white')
            label_rect = label_text.get_rect(center=(x_offset + 82, lik_name_y))
            screen.blit(label_text, label_rect)

            if lik["id"] == user_data.get('active_character', 'odijelo'):
                character_button_text = "Odabran"
                character_button_image = gumb3_image
            elif lik["id"] in user_data['characters']:
                character_button_text = "Odaberi"
                character_button_image = gumb_image
            else:
                character_button_text = "Kupi"
                character_button_image = gumb_image

            character_button_rect = pygame.Rect(x_offset + 7, lik_price_y, button_width, button_height)

            screen.blit(
                pygame.transform.smoothscale(character_button_image, (button_width, button_height)),
                (character_button_rect.x, character_button_rect.y)
            )

            if lik["id"] not in user_data['characters']:
                nacrtaj_cijenu_sa_zvijezdom(character_button_rect, lik["price"])
            else:
                font_button = pygame.font.Font('freesansbold.ttf', 22)
                text_surface = font_button.render(character_button_text, True, 'white')
                text_rect = text_surface.get_rect(center=character_button_rect.center)
                screen.blit(text_surface, text_rect)

            character_buttons.append({
                "rect": character_button_rect,
                "id": lik["id"],
                "price": lik["price"]
            })

            x_offset += column_spacing

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    collected_stars = root.users[player_name]['stars'] 
                    transaction.commit()
                    print(f"DEBUG: Spremanje zvijezda za {player_name} prilikom povratka iz trgovine: {collected_stars}")
                    return

                for button in jetpack_buttons:
                    if button["rect"].collidepoint(event.pos):
                        jetpack_name = button["name"]

                        if jetpack_name in user_data['jetpacks']:
                            user_data['active_jetpack'] = jetpack_name
                            transaction.commit()
                            print(f"Odabrali ste {jetpack_name}!")

                        elif user_data['stars'] >= button["price"]:
                            user_data['stars'] -= button["price"]
                            user_data['jetpacks'].append(jetpack_name)
                            user_data['active_jetpack'] = jetpack_name
                            transaction.commit()
                            print(f"DEBUG: {player_name} kupio {jetpack_name}. Preostalo: {user_data['stars']} zvijezda.")

                        else:
                            print(f"Nemate dovoljno zvijezda za {jetpack_name}.")

                        break

                for button in character_buttons:
                    if button["rect"].collidepoint(event.pos):
                        character_id = button["id"]

                        if character_id in user_data['characters']:
                            user_data['active_character'] = character_id
                            transaction.commit()
                            print(f"Odabrali ste lika {character_id}!")

                        elif user_data['stars'] >= button["price"]:
                            user_data['stars'] -= button["price"]
                            user_data['characters'].append(character_id)
                            user_data['active_character'] = character_id
                            transaction.commit()
                            print(f"DEBUG: {player_name} kupio lika {character_id}. Preostalo: {user_data['stars']} zvijezda.")

                        else:
                            print(f"Nemate dovoljno zvijezda za lika {character_id}.")

                        break


def show_user_stats(player_name):
    user_data = root.users[player_name]

    stats_background = pygame.image.load('images/statistika.png')
    stats_background = pygame.transform.scale(stats_background, (WIDTH, HEIGHT))

    while True:
        screen.blit(stats_background, (0, 0))
        font_stats = pygame.font.Font(None, 36)

        stats = [
            f"Broj odigranih igara: {user_data['games_played']}",
            f"Najveća udaljenost: {user_data['record']} m",
            f"Ukupno zvijezda: {user_data['lifetime_stars']}",
            f"Sudari s laserima: {user_data['crashes_lasers']}",
            f"Sudari s raketama: {user_data['crashes_rockets']}",
        ]

        y_offset = 150
        for stat in stats:
            text_surface = font_stats.render(stat, True, 'white')
            screen.blit(text_surface, (WIDTH // 2 - 250, y_offset))
            y_offset += 50

        back_button = nacrtaj_gumb(WIDTH // 2 - 110, HEIGHT - 85, 'Natrag', gumb2_image)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):  
                    return


def show_challenges(player_name):
    while True:
        challenges_image = pygame.image.load('images/izazovi.png')
        challenges_image = pygame.transform.scale(challenges_image, (WIDTH, HEIGHT))
        screen.blit(challenges_image, (0, 0))

        font_challenges = pygame.font.Font('freesansbold.ttf', 22)
        font_small = pygame.font.Font('freesansbold.ttf', 21)

        user_data = root.users[player_name]

        if 'completed_challenges' not in user_data:
            user_data['completed_challenges'] = PersistentList()
            transaction.commit()

        completed = user_data['completed_challenges']

        active_challenges = []

        for challenge in root.daily_challenges:
            if challenge['challenge_id'] not in completed:
                active_challenges.append(challenge)

        if len(active_challenges) == 0:
            text = font_challenges.render("Nema aktivnih izazova. Sve si riješio!", True, 'white')
            text_rect = text.get_rect(center=(WIDTH // 2, 280))
            screen.blit(text, text_rect)
        else:
            y_offset = 165
            mala_zvijezda = pygame.transform.smoothscale(star_image, (24, 24))

            for challenge in active_challenges:
                challenge_id = challenge['challenge_id']

                if challenge_id == 1:
                    progress = min(stars_this_game, 20)
                    target = 20

                elif challenge_id == 2:
                    progress = min(user_data.get('crashes_rockets', 0), 5)
                    target = 5

                elif challenge_id == 3:
                    progress = min(int(distance), 1000)
                    target = 1000

                else:
                    progress = 0
                    target = 1

                opis_tekst = f"{challenge['description']}: {progress}/{target}"
                opis = font_challenges.render(opis_tekst, True, 'white')
                screen.blit(opis, (105, y_offset))

                nagrada_text = font_small.render(f"Nagrada: {challenge['reward']}", True, 'white')
                screen.blit(nagrada_text, (105, y_offset + 35))

                screen.blit(
                    mala_zvijezda,
                    (105 + nagrada_text.get_width() + 8, y_offset + 32)
                )

                y_offset += 95

        back_button = nacrtaj_gumb(WIDTH // 2 - 110, HEIGHT - 90, 'Natrag', gumb2_image)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return


def generiraj_sliku(line_list, lase):
    global background_x

    if not pause:
        background_x -= background_speed

    if background_x <= -WIDTH:
        background_x = 0

    screen.blit(background_image, (background_x, 0))
    screen.blit(background_image, (background_x + WIDTH, 0))

    for star in stars:
        screen.blit(star_image, (star["rect"].x, star["rect"].y))

    for i in range(len(line_list)):
        pygame.draw.line(screen, 'black', (line_list[i], 0), (line_list[i], 50), 3) 
        pygame.draw.line(screen, 'black', (line_list[i], HEIGHT - 50), (line_list[i], HEIGHT), 3)

        if not pause:
            line_list[i] -= game_speed

        if line_list[i] < 0:
            line_list[i] = WIDTH

    if not pause:
        lase[0][0] -= game_speed*3
        lase[1][0] -= game_speed*3

    screen.blit(okvir_image, (0, 0))  
    screen.blit(okvir_image, (0, HEIGHT - 50)) 

    outer_radius = 16
    inner_radius = 10
    border_width = 2

    if lase[0][1] == lase[1][1]:
        x1 = int(lase[0][0])
        x2 = int(lase[1][0])
        y = int(lase[0][1])

        laser_width = max(1, x2 - x1)

        laser_line = pygame.Rect(
            x1,
            y - LASER_DEBLJINA // 2,
            laser_width,
            LASER_DEBLJINA
        )

        pygame.draw.rect(screen, (255, 40, 20), laser_line)

        pygame.draw.rect(
            screen,
            (255, 230, 180),
            (x1, y - 2, laser_width, 4)
        )

        pygame.draw.circle(screen, (255, 80, 20), (x1, y), outer_radius)
        pygame.draw.circle(screen, (255, 230, 120), (x1, y), inner_radius)
        pygame.draw.circle(screen, (30, 30, 30), (x1, y), outer_radius, border_width)

        pygame.draw.circle(screen, (255, 80, 20), (x2, y), outer_radius)
        pygame.draw.circle(screen, (255, 230, 120), (x2, y), inner_radius)
        pygame.draw.circle(screen, (30, 30, 30), (x2, y), outer_radius, border_width)

    else:
        x = int(lase[0][0])
        y1 = int(lase[0][1])
        y2 = int(lase[1][1])

        laser_height = max(1, y2 - y1)

        laser_line = pygame.Rect(
            x - LASER_DEBLJINA // 2,
            y1,
            LASER_DEBLJINA,
            laser_height
        )

        pygame.draw.rect(screen, (255, 40, 20), laser_line)

        pygame.draw.rect(
            screen,
            (255, 230, 180),
            (x - 2, y1, 4, laser_height)
        )

        pygame.draw.circle(screen, (255, 80, 20), (x, y1), outer_radius)
        pygame.draw.circle(screen, (255, 230, 120), (x, y1), inner_radius)
        pygame.draw.circle(screen, (30, 30, 30), (x, y1), outer_radius, border_width)

        pygame.draw.circle(screen, (255, 80, 20), (x, y2), outer_radius)
        pygame.draw.circle(screen, (255, 230, 120), (x, y2), inner_radius)
        pygame.draw.circle(screen, (30, 30, 30), (x, y2), outer_radius, border_width)

    screen.blit(font.render(f'Distance: {int(distance)} m', True, 'white'), (10, 10))
    stars_display = root.users[player_name]['stars'] 
    screen.blit(font.render(f'Zvijezde: {stars_display}', True, 'white'), (10, 50))

    top_plat = pygame.Rect(0, 0, WIDTH, 50)
    bot_plat = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)

    return line_list, top_plat, bot_plat, lase, laser_line



def generiraj_igraca():
    global walk_counter

    user_data = root.users[player_name]

    active_character = user_data.get('active_character', 'odijelo')
    active_jetpack = user_data.get('active_jetpack', 'jetpack')

    if active_character not in likovi_po_karakteru:
        active_character = 'odijelo'

    if active_jetpack not in likovi_po_karakteru[active_character]:
        active_jetpack = 'jetpack'

    slike_lika = likovi_po_karakteru[active_character][active_jetpack]

    hod_1 = slike_lika[0]
    hod_2 = slike_lika[1]
    hod_3 = slike_lika[2]
    pada = slike_lika[3]
    leti_boost = slike_lika[4]

    if booster:
        screen.blit(leti_boost, (100, player_y))

    elif player_y >= HEIGHT - 130:
        if walk_counter < 20:
            screen.blit(hod_1, (100, player_y))
        elif 20 <= walk_counter < 40:
            screen.blit(hod_2, (100, player_y))
        elif 40 <= walk_counter < 60:
            screen.blit(hod_3, (100, player_y))
        elif 60 <= walk_counter < 80:
            screen.blit(hod_2, (100, player_y))

        walk_counter += 1

        if walk_counter >= 80:
            walk_counter = 0

    else:
        screen.blit(pada, (100, player_y))

    return pygame.Rect((120, player_y + 10), (25, 60))



def provjeri_sudar():
    global stars, collected_stars
    coll = [False, False]
    rstrt = False
    if player.colliderect(bot_plat):
        coll[0] = True
    elif player.colliderect(top_plat):
        coll[1] = True
    if laser_line.colliderect(player):
        root.users[player_name]['crashes_lasers'] += 1 
        transaction.commit()
        rstrt = True
    if rocket_active:
        if rocket.colliderect(player):
            root.users[player_name]['crashes_rockets'] += 1 
            transaction.commit()
            print(f"DEBUG: Sudar s raketom! Ukupno: {root.users[player_name]['crashes_rockets']}")
            rstrt = True
    return coll, rstrt



def generiraj_laser():
    laser_type = random.randint(0, 1)
    offset = random.randint(10, 300)
    if laser_type == 0:
        laser_width = random.randint(100, 300)
        laser_y = random.randint(100, HEIGHT - 100)
        new_lase = [[WIDTH + offset, laser_y], [WIDTH + offset + laser_width, laser_y]]
    else:
        laser_height = random.randint(100, 300)
        laser_y = random.randint(100, HEIGHT - 400)
        new_lase = [[WIDTH + offset, laser_y], [WIDTH + offset, laser_y + laser_height]]
    return new_lase



def generiraj_raketu(coords, mode):
    if mode == 0:  
        rock = screen.blit(oprez_image, (coords[0] - 80, coords[1] - 40))
        if not pause:
            if coords[1] > player_y + 10:
                coords[1] -= 3
            else:
                coords[1] += 3
    else: 
        rock = screen.blit(rocket_image, (coords[0], coords[1] - 10))
        if not pause:
            coords[0] -= 10 + game_speed
    return coords, rock



player_name = show_start_screen()
if '' in root.users:
    del root.users['']
    transaction.commit()
player_name = player_name.strip()        
player_name = player_name.lower()     
print(f"DEBUG: Korisnici u bazi: {list(root.users.keys())}")
print(f"DEBUG: Prijavljeni korisnik: '{player_name}' (duljina = {len(player_name)})")

if player_name not in root.users:
    root.users[player_name] = PersistentMapping({
    'record': 0,
    'lifetime_stars': 0,
    'games': PersistentList(),
    'stars': 0,
    'jetpacks': PersistentList(['jetpack']),
    'active_jetpack': 'jetpack',
    'characters': PersistentList(['odijelo']),
    'active_character': 'odijelo',
    'games_played': 0,
    'crashes_lasers': 0,
    'crashes_rockets': 0,
    'completed_challenges': PersistentList()
})
    transaction.commit()

user_data = root.users[player_name]  
print("DEBUG: Svi korisnici u bazi:", list(root.users.keys()))
collected_stars = user_data['stars'] 
print(f"Prilikom pokretanja igre za {player_name}, pronađeno {collected_stars} zvijezda.")
print(f"DEBUG: Za korisnika '{player_name}' dohvaćeno {collected_stars} zvijezda iz baze.")
stars_this_game = 0




run = True
while run:
    timer.tick(fps)
    if counter < 40:
        counter += 1
    else:
        counter = 0
    if new_laser:
        laser = generiraj_laser()
        laser_sound.play()
        new_laser = False
    lines, top_plat, bot_plat, laser, laser_line = generiraj_sliku(lines, laser)
    

    if not rocket_active:
        rocket_counter += 1
    if rocket_counter > 180:
        rocket_counter = 0
        rocket_active = True
        rocket_delay = 0
        rocket_sound_played = False
        rocket_coords = [WIDTH, HEIGHT / 2]
    if rocket_active:
        if rocket_delay < 90: 
            if not pause:
                rocket_delay += 1
            rocket_coords, rocket = generiraj_raketu(rocket_coords, 0)  
        else:
            if not rocket_sound_played:
                raketa_sound.play()
                rocket_sound_played = True 
            rocket_coords, rocket = generiraj_raketu(rocket_coords, 1)  
        if rocket_coords[0] < -50:  
            rocket_active = False

    player = generiraj_igraca()

    for star in stars[:]:
        if player.colliderect(star["rect"]): 
            zvijezda_sound.play() 
            stars.remove(star)  
            root.users[player_name]['stars'] += 1 
            root.users[player_name]['lifetime_stars'] += 1
            stars_this_game += 1
            collected_stars = root.users[player_name]['stars']
            transaction.commit()
            print(f"DEBUG: {player_name} lifetime_stars: {root.users[player_name]['lifetime_stars']}")
            stars.append(generiraj_zvijezdu())


    colliding, restart_cmd = provjeri_sudar()

    for challenge in root.daily_challenges:
        if challenge['challenge_id'] not in root.users[player_name]['completed_challenges']:

            challenge_done = False

            if challenge['challenge_id'] == 1 and stars_this_game >= 20:
                challenge_done = True

            elif challenge['challenge_id'] == 2 and root.users[player_name]['crashes_rockets'] >= 5:
                challenge_done = True

            elif challenge['challenge_id'] == 3 and distance >= 1000:
                challenge_done = True

            if challenge_done:
                root.users[player_name]['stars'] += challenge['reward']
                root.users[player_name]['completed_challenges'].append(challenge['challenge_id'])
                collected_stars = root.users[player_name]['stars']

                print(
                    f"Izazov '{challenge['description']}' ispunjen! "
                    f"Dobivaš {challenge['reward']} zvijezda."
                )

    transaction.commit()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            transaction.commit()
            connection.close()
            db.close()
            pygame.quit()
            exit() 
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                show_pause_menu(player_name)

            if event.key == pygame.K_SPACE and not booster and not pause:
                booster = True

                if not letenje_channel.get_busy():
                    letenje_channel.play(letenje_sound, loops=-1)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                booster = False
                letenje_channel.stop()

    if booster:
        if player_y > TOP_MARGIN:
            player_y -= 5
    else:
        if player_y < HEIGHT - BOTTOM_MARGIN:
            player_y += 5

    if not pause:
        distance += game_speed
        if booster:
            y_velocity -= gravity
        else:
            y_velocity += gravity
        if (colliding[0] and y_velocity > 0) or (colliding[1] and y_velocity < 0):
            y_velocity = 0
        player_y += y_velocity
        if player_y < TOP_MARGIN:
            player_y = TOP_MARGIN
            y_velocity = 0

        if player_y > HEIGHT - BOTTOM_MARGIN:
            player_y = HEIGHT - BOTTOM_MARGIN
            y_velocity = 0

    if distance < 20000:
        game_speed = 1 + (distance // 500) / 10
    else:
        game_speed = 11

    if laser[0][0] < 0 and laser[1][0] < 0:
        new_laser = True

    if distance > root.users[player_name]['record']:
        root.users[player_name]['record'] = int(distance)

    if restart_cmd:
        letenje_channel.stop()
        booster = False
        kraj_sound.play()
        root.users[player_name]['games_played'] += 1
        user_data = root.users[player_name] 
        collected_stars = user_data['stars'] 
        transaction.commit()
        print(f"Ažurirane zvijezde za igrača {player_name}: {collected_stars}")

        root.all_games.append({
            'player': player_name,
            'distance': int(distance),
            'stars': collected_stars
                })
        transaction.commit()  
        print(f"Dodan zapis za igrača {player_name}: {distance}m, {collected_stars} zvijezde.")


        if not show_end_screen(player_name, int(distance)):
            break

        distance = 0
        stars_this_game = 0
        rocket_active = False
        rocket_counter = 0
        pause = False
        player_y = init_y
        y_velocity = 0
        restart_cmd = False
        new_laser = True
        laser = generiraj_laser()
        stars = [generiraj_zvijezdu() for _ in range(3)]

    if distance > high_score:
        high_score = int(distance)
    
    for star in stars[:]:  
        star["rect"].x -= star["speed"]  
        if star["rect"].x < -20:  
            stars.remove(star) 
            stars.append(generiraj_zvijezdu())  

    pygame.display.flip()





