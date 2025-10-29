import json
import random

def load_songs():
    try:
        with open('songs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

songs = load_songs()

def get_random_song():
    if not songs:
        return None
    return random.choice(songs)

def add_song(title, artist, year, genre, url):
    songs = load_songs()
    new_id = max([s['id'] for s in songs], default=0) + 1
    new_song = {
        "id": new_id,
        "title": title,
        "artist": artist,
        "year": year,
        "genre": genre,
        "url": url,
    }
    songs.append(new_song)
    with open('songs.json', 'w', encoding='utf-8') as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)
    print(f"已新增歌曲：{title}")

def song_info():
    title = input("歌曲名稱：")
    artist = input("歌手名稱：")
    year = input("發行年份：")
    genre = input("音樂類型：")
    url = input("歌曲連結：")
    add_song(title, artist, year, genre, url)

if __name__ == "__main__":
    while True:
        exit_prompt = input("是否要新增歌曲？(y/n)：")
        if exit_prompt.lower() != 'y':
            print("結束程式。")
            exit()
        number_of_songs = int(input("請問要新增幾首歌曲？"))
        for _ in range(number_of_songs):
            song_info()