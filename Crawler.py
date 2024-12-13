# -*- coding: utf-8 -*-
import requests
import json
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
import time

# -----------数据库初始化-----------------
# 数据库连接设置
@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            database="postgres",
            user="admin",
            password="admin@123",
            host="192.168.37.132",
            port="7654",
            client_encoding="UTF8"
        )
        print("Database connection successful.")
        yield connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise  # 抛出异常以便处理
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")

# 删除所有数据库表
def drop_all_tables():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        commands = [
            '''
            DROP TABLE IF EXISTS PlaylistSongs CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Playlists CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Favorites CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Songs CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Albums CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Artists CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Users CASCADE
            '''
        ]
        try:
            for command in commands:
                cursor.execute(command)
            connection.commit()
            print("All tables dropped successfully.")
        except Exception as e:
            print(f"Error occurred while dropping tables: {e}")
        finally:
            cursor.close()

# 创建数据库表
def create_tables():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        commands = [
            '''
            CREATE TABLE IF NOT EXISTS Artists (
                artist_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                bio TEXT,
                country VARCHAR(100),
                gender VARCHAR(100)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Albums (
                album_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                artist_id INT,
                FOREIGN KEY (artist_id) REFERENCES Artists(artist_id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Users (
                user_id SERIAL PRIMARY KEY,
                user_name VARCHAR(30) NOT NULL UNIQUE,
                password VARCHAR(15) NOT NULL,
                email VARCHAR(30),
                tel VARCHAR(11),
                year INT,
                month INT,
                day INT
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Songs (
                song_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL UNIQUE,
                artist_id INT,
                album_id INT,
                genre VARCHAR(100),
                audio_url VARCHAR(255) NOT NULL,
                language VARCHAR(100),
                FOREIGN KEY (artist_id) REFERENCES Artists(artist_id),
                FOREIGN KEY (album_id) REFERENCES Albums(album_id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Playlists (
                playlist_id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Favorites (
                user_id INT NOT NULL,
                song_id INT NOT NULL,
                PRIMARY KEY (user_id, song_id),
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            )
            '''
        ]
        try:
            for command in commands:
                cursor.execute(command)
            connection.commit()
            print("All tables created successfully.")
        except Exception as e:
            print(f"Error occurred while creating tables: {e}")
        finally:
            cursor.close()

# 插入艺术家数据
def insert_artist(artist_id, name, bio, country, gender):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO Artists (artist_id, name, bio, country, gender)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (artist_id) DO NOTHING
            ''', (artist_id, name, bio, country, gender))
            connection.commit()
            print(f"Inserted artist: {name}")
        except Exception as e:
            print(f"Error inserting artist {name}: {e}")
        finally:
            cursor.close()

# 插入专辑数据
def insert_album(album_id, title, artist_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO Albums (album_id, title, artist_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (album_id) DO NOTHING
            ''', (album_id, title, artist_id))
            connection.commit()
            print(f"Inserted album: {title}")
        except Exception as e:
            print(f"Error inserting album {title}: {e}")
        finally:
            cursor.close()

# 插入歌曲数据
def insert_song(title, artist_id, album_id, genre, audio_url, language):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO Songs (title, artist_id, album_id, genre, audio_url, language)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (title) DO NOTHING
            ''', (title, artist_id, album_id, genre, audio_url, language))
            connection.commit()
            print(f"Inserted song: {title}")
        except Exception as e:
            print(f"Error inserting song {title}: {e}")
        finally:
            cursor.close()

# 插入用户数据
def insert_user(user_name, password, email, tel, year, month, day):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO Users (user_name, password, email, tel, year, month, day)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_name) DO NOTHING
            ''', (user_name, password, email, tel, year, month, day))
            connection.commit()
            print(f"Inserted user: {user_name}")
        except Exception as e:
            print(f"Error inserting user {user_name}: {e}")
        finally:
            cursor.close()

# -----------爬虫功能-----------------
# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://music.163.com/',
}

# 获取指定歌手的歌曲信息
def get_artist_songs(artist_id):
    """
    发送请求获取指定歌手的歌曲信息
    参数:
    artist_id (str): 歌手的 ID
    返回:
    list or None: 成功则返回歌曲列表，否则返回 None
    """
    url = 'https://music.163.com/api/artist/albums/'  # 获取歌手专辑的 API
    params = {
        'id': artist_id,
        'offset': 0,
        'total': True,
        'limit': 100  # 每页获取100张专辑
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        albums_data = response.json()
        albums = albums_data.get('hotAlbums', [])  # 获取热门专辑
        songs = []
        for album in albums:
            album_id = album['id']
            songs += get_album_songs(album_id)
            time.sleep(1)  # 避免请求过于频繁
        return songs
    except requests.exceptions.RequestException as e:
        print('请求出错:', e)
        return None

# 获取专辑中的歌曲
def get_album_songs(album_id):
    url = 'https://music.163.com/api/album/' + str(album_id)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        album_data = response.json()
        songs = album_data.get('songs', [])
        print(f"Fetched {len(songs)} songs from album ID {album_id}")
        return songs
    except requests.exceptions.RequestException as e:
        print(f"Error fetching songs from album {album_id}: {e}")
        return []

# 获取歌曲的播放链接
def get_song_url(song_id):
    """
    获取歌曲的播放链接
    参数:
    song_id (int): 歌曲的 ID
    返回:
    str: 歌曲的下载 URL
    """
    url = f'https://music.163.com/song/media/outer/url?id={song_id}.mp3'
    return url

# 下载歌曲
def download_song(song_name, song_url, save_dir):
    """
    下载指定歌曲并保存到指定目录
    参数:
    song_name (str): 歌曲名称
    song_url (str): 歌曲的下载 URL
    save_dir (str): 保存歌曲的目录
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    safe_song_name = "".join(c for c in song_name if c.isalnum() or c in " _-")
    save_path = os.path.join(save_dir, f'{safe_song_name}.mp3')
    if os.path.exists(save_path):
        print(f'{song_name} 已存在，跳过下载！')
        return
    try:
        response = requests.get(song_url, headers=headers, timeout=30)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f'{song_name} 下载完成！')
    except requests.exceptions.RequestException as e:
        print(f'{song_name} 下载失败！错误: {e}')

# -----------主程序逻辑-----------------
def main():
    # 初始化数据库
    drop_all_tables()
    create_tables()

    # 插入示例数据（如果需要）
    # 注意：如果您已经有了数据，可以跳过这一步
    # 这里假设您已经有了插入数据的逻辑

    # 爬取网易云音乐数据并存入数据库
    # 示例：爬取陈奕迅的歌曲
    # 首先获取陈奕迅的 artist_id，假设为 7
    artist_id = '2116'  # 请根据实际情况修改
    songs = get_artist_songs(artist_id)
    if songs:
        print(f"总共获取到 {len(songs)} 首歌曲。")
        save_dir = '下载的歌曲'  # 保存目录
        for song in songs:
            song_name = song.get('name')
            song_id = song.get('id')
            album = song.get('album', {})
            album_id = album.get('id')
            album_title = album.get('name')
            genre = song.get('album', {}).get('genre', 'Unknown')  # 需要根据实际数据结构调整
            language = song.get('album', {}).get('language', 'Unknown')  # 需要根据实际数据结构调整

            # 获取播放链接
            song_url = get_song_url(song_id)

            # 下载歌曲
            download_song(song_name, song_url, save_dir)

            # 插入专辑数据
            insert_album(album_id, album_title, artist_id)

            # 插入歌曲数据
            insert_song(song_name, artist_id, album_id, genre, song_url, language)

            time.sleep(1)  # 避免请求过于频繁
    else:
        print('获取歌曲信息失败！')

if __name__ == "__main__":
    main()
