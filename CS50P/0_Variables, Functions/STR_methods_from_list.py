SHOWS = [
    "Destet",
    "The Last of Us",
    "The Witcher",
    "The Mandalorian",
    "The Boys",
    "The Flash",
    "The Office",
    "The Walking Dead",
    "The Big Bang Theory",
    "The Simpsons",
    "The Office",
    "The Office",
]

def main():
    SHOWS_format = []
    for show in SHOWS:
        SHOWS_format.append(show.strip().title())
    print('\n'.join(SHOWS_format))

main()