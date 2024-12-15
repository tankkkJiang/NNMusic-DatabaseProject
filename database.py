import psycopg2
import psycopg2.extras  # 导入用于字典游标的模块
from contextlib import contextmanager
import random

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
            DROP TABLE IF EXISTS CommunityComments CASCADE
            ''',
            '''
            DROP TABLE IF EXISTS Playlists CASCADE
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
            ''',
            '''
            DROP TABLE IF EXISTS Favorites CASCADE
            '''
        ]
        try:
            for command in commands:
                cursor.execute(command)
            connection.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
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
            CREATE TABLE IF NOT EXISTS Favorites (
                user_id INT NOT NULL,
                song_id INT NOT NULL,
                PRIMARY KEY (user_id, song_id),
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS CommunityComments (
                comment_id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )
            '''
        ]
        try:
            for command in commands:
                cursor.execute(command)
            connection.commit()
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            cursor.close()

# -----------登录注册相关函数-----------------
# 验证用户信息
def validate_user(user_name, password, connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT password, user_id FROM Users WHERE user_name=%s", (user_name,))
        result = cursor.fetchone()
        if result and result[0] == password:
            return result[1]
        else:
            return None
    finally:
        cursor.close()


# 更新用户信息
def update_user_info(user_id, user_name, email, tel, year, month, day):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE Users
                SET user_name = %s,
                    email = %s,
                    tel = %s,
                    year = %s,
                    month = %s,
                    day = %s
                WHERE user_id = %s
                """,
                (user_name, email, tel, year, month, day, user_id)
            )
            connection.commit()
            print(f"用户ID {user_id} 的信息已更新。")
            return True
        except Exception as e:
            print(f"更新用户ID {user_id} 信息时出错: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()


# -----------去除信息-----------------
# 移除用户收藏的歌曲（如果需要独立的移除功能）
def remove_favorites(user_name, song_name):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            # 获取 user_id
            cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()
            if not user:
                print(f"用户 '{user_name}' 未找到。")
                return
            user_id = user[0]

            # 获取 song_id，确保歌曲名和艺术家名匹配
            cursor.execute(
                """
                SELECT Songs.song_id
                FROM Songs
                JOIN Artists ON Songs.artist_id = Artists.artist_id
                WHERE Songs.title = %s
                """,
                (song_name,)
            )
            song = cursor.fetchone()
            if not song:
                print(f"歌曲 '{song_name}' 的记录未找到。")
                return
            song_id = song[0]

            # 删除 Favorites 表中的记录
            cursor.execute(
                """
                DELETE FROM Favorites WHERE user_id = %s AND song_id = %s
                """,
                (user_id, song_id)
            )
            connection.commit()
            if cursor.rowcount > 0:
                print(f"歌曲 '{song_name}' 已从用户 '{user_name}' 的收藏中移除。")
            else:
                print(f"未找到歌曲 '{song_name}' 在用户 '{user_name}' 的收藏中。")
        except Exception as e:
            print(f"移除收藏时发生错误: {e}")
            connection.rollback()
        finally:
            cursor.close()


# -----------获取信息get-----------------
# 获取当前用户的信息
def get_user_info(user_name):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users WHERE user_name = %s", (user_name,))
        user = cursor.fetchone()
        return user


# 获取所有社区评论
def get_all_comments(connection):
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT cc.comment_id, u.user_name, cc.content, cc.timestamp
            FROM CommunityComments cc
            JOIN Users u ON cc.user_id = u.user_id
            ORDER BY cc.timestamp DESC
        ''')
        return cursor.fetchall()


# 插入新的社区评论
def insert_comment(user_id, content):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO CommunityComments (user_id, content)
                VALUES (%s, %s)
            ''', (user_id, content))
            connection.commit()


# 获取用户收藏的歌曲
def get_user_favorites(connection, user_name):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # 首先获取 user_id
        cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
        user = cursor.fetchone()

        if not user:
            print(f"用户 '{user_name}' 未找到。")
            return []

        user_id = user['user_id']

        # 使用 user_id 获取收藏的歌曲详情
        query = """
            SELECT 
                Songs.song_id, 
                Songs.title, 
                Artists.name AS artist_name, 
                Albums.title AS album_title, 
                Songs.genre, 
                Songs.language, 
                Songs.audio_url
            FROM Favorites
            JOIN Songs ON Favorites.song_id = Songs.song_id
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            LEFT JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Favorites.user_id = %s
        """
        cursor.execute(query, (user_id,))
        favorites = cursor.fetchall()
        return favorites
    except Exception as e:
        print(f"获取用户 '{user_name}' 收藏的歌曲时出错: {e}")
        return []
    finally:
        cursor.close()


# 获取所有歌曲并展示，联合查询艺术家姓名和专辑名称
def get_all_songs(conn):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                Songs.song_id, 
                Songs.title, 
                Artists.name AS artist_name, 
                Albums.title AS album_title, 
                Songs.genre, 
                Songs.language, 
                Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            LEFT JOIN Albums ON Songs.album_id = Albums.album_id
        """)
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"获取所有歌曲时出错: {e}")
        return []
    finally:
        cursor.close()



# 获得详细歌曲信息
def get_song_by_id(connection, song_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, Songs.language,
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.song_id = %s
        """
        cursor.execute(query, (song_id,))
        song = cursor.fetchone()
        return song
    except Exception as e:
        print(f"Error while getting song by id {song_id}: {e}")
        return None
    finally:
        cursor.close()


# 获取所有专辑并展示，联合查询歌手姓名和歌曲数量
def get_all_albums(connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Albums.album_id, Albums.title AS album_title, Artists.name AS artist_name
            FROM Albums
            JOIN Artists ON Albums.artist_id = Artists.artist_id
        """
        cursor.execute(query)
        albums = cursor.fetchall()
        return albums
    except Exception as e:
        print(f"Error while getting albums: {e}")
        return []
    finally:
        cursor.close()


# 根据专辑查询歌曲
def get_songs_by_album(connection, album_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name,
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.album_id = %s
        """
        cursor.execute(query, (album_id,))
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"Error while getting songs for album {album_id}: {e}")
        return []
    finally:
        cursor.close()


# 根据id获取专辑名称
def get_album_name_by_id(conn, album_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT title FROM Albums WHERE album_id = %s
        """, (album_id,))
        album = cursor.fetchone()
        if album:
            return album[0]
        else:
            return ""
    except Exception as e:
        print(f"获取专辑名称时出错: {e}")
        return ""
    finally:
        cursor.close()

def get_artist_bio_by_name(conn, artist_name):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT bio FROM Artists WHERE name = %s
        """, (artist_name,))
        artist = cursor.fetchone()
        if artist:
            return artist[0]
        else:
            return ""
    except Exception as e:
        print(f"获取艺术家简介时出错: {e}")
        return ""
    finally:
        cursor.close()

# 获取所有艺术家信息
def get_all_artists(connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT artist_id, name, country, gender
            FROM Artists
        """
        cursor.execute(query)
        artists = cursor.fetchall()  # 获取所有艺术家信息
        return artists
    except Exception as e:
        print(f"Error while getting artists: {e}")
        return []
    finally:
        cursor.close()


def get_songs_by_artist(connection, artist_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, Songs.language,
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.artist_id = %s
        """
        cursor.execute(query, (artist_id,))
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"Error while getting songs by artist: {e}")
        return []
    finally:
        cursor.close()


def get_artist_info_by_artist(connection, artist_id):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = """
            SELECT Artists.name AS artist_name, bio
            FROM Artists
            WHERE Artists.artist_id = %s
        """
        cursor.execute(query, (artist_id,))
        result = cursor.fetchone()
        artist_name = result['artist_name']
        artist_bio = result['bio']
        return artist_name, artist_bio
    except Exception as e:
        print(f"Error while getting songs by artist: {e}")
        return []
    finally:
        cursor.close()


# -----------插入功能-----------------

# 插入用户数据
def insert_user(user_name, password, email, tel, year, month, day):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        """id = random.uniform(1, 1000000)"""
        try:
            # 首先检查用户名是否已存在
            cursor.execute("SELECT * FROM Users WHERE user_name = %s", (user_name,))
            if cursor.fetchone():
                print(f"User '{user_name}' already exists.")
            else:
                # 用户不存在，插入新用户
                cursor.execute(
                    """
                    INSERT INTO Users (user_name, password, email, tel, year, month, day)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_name, password, email, tel, year, month, day)
                )
                connection.commit()
                print(f"User '{user_name}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting user '{user_name}': {e}")
        finally:
            cursor.close()


# 插入歌曲数据
def insert_song(title, artist_id, album_id, genre, audio_url, language):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Songs (title, artist_id, album_id, genre, audio_url, language)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (title, artist_id, album_id, genre, audio_url, language)
            )
            connection.commit()
            print(f"Song '{title}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting song '{title}': {e}")
        finally:
            cursor.close()


# 插入用户收藏的歌曲
def insert_favorites(user_name, song_name, artist_name):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            # 获取 user_id
            cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()
            if not user:
                print(f"用户 '{user_name}' 未找到。")
                return
            user_id = user[0]

            # 获取 song_id，确保歌曲名和艺术家名匹配
            cursor.execute(
                """
                SELECT Songs.song_id
                FROM Songs
                JOIN Artists ON Songs.artist_id = Artists.artist_id
                WHERE Songs.title = %s AND Artists.name = %s
                """,
                (song_name, artist_name)
            )
            song = cursor.fetchone()
            if not song:
                print(f"歌曲 '{song_name}' 由艺术家 '{artist_name}' 演唱的记录未找到。")
                return
            song_id = song[0]

            # 插入到 Favorites 表
            cursor.execute(
                """
                INSERT INTO Favorites (user_id, song_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, song_id) DO NOTHING
                """,
                (user_id, song_id)
            )
            connection.commit()
            print(f"歌曲 '{song_name}' 已添加到用户 '{user_name}' 的收藏中。")
        except Exception as e:
            print(f"将歌曲 '{song_name}' 添加到用户 '{user_name}' 的收藏时出错: {e}")
            connection.rollback()
        finally:
            cursor.close()


# 插入专辑数据
def insert_album(album_id, title, artist_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Albums (album_id, title, artist_id)
                VALUES (%s, %s, %s)
                """,
                (album_id, title, artist_id)
            )
            connection.commit()
            print(f"Album '{title}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting album '{title}': {e}")
        finally:
            cursor.close()


# 插入艺术家数据
def insert_artist(artist_id, name, bio, country, gender):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Artists (artist_id, name, bio, country, gender)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (artist_id, name, bio, country, gender)
            )
            connection.commit()
            print(f"Artist '{name}' inserted successfully.")
        except Exception as e:
            print(f"Error inserting artist '{name}': {e}")
        finally:
            cursor.close()


# -----------搜索功能-----------------
def search_albums(query, connection):
    # 返回一个由字典构成的列表，每个字典表示一个专辑。
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 使用字典游标
    try:
        # 执行模糊查询，查找专辑名称中包含查询关键词的专辑
        cursor.execute("SELECT * FROM Albums WHERE title ILIKE %s", ('%' + query + '%',))
        albums = cursor.fetchall()  # 获取所有匹配的专辑
        return albums  # 返回匹配的专辑列表
    except Exception as e:
        print(f"Error while searching albums: {e}")  # 打印错误信息
        return []  # 出现错误时返回空列表
    finally:
        cursor.close()  # 确保游标关闭


def search_artists(query, connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 使用字典游标
    try:
        # 执行模糊查询，查找艺术家名称中包含查询关键词的艺术家
        cursor.execute("SELECT * FROM Artists WHERE name ILIKE %s", ('%' + query + '%',))
        artists = cursor.fetchall()  # 获取所有匹配的艺术家
        return artists  # 返回匹配的艺术家列表
    except Exception as e:
        print(f"Error while searching artists: {e}")  # 打印错误信息
        return []  # 出现错误时返回空列表
    finally:
        cursor.close()  # 确保游标关闭


def search_songs(query, connection):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # 使用字典游标
    try:
        # 联合查询：查询歌曲信息时，连接艺术家和专辑的信息
        query_string = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, 
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url, Songs.language
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE Songs.title ILIKE %s
        """
        cursor.execute(query_string, ('%' + query + '%',))
        songs = cursor.fetchall()  # 获取所有匹配的歌曲
        return songs  # 返回匹配的歌曲列表
    except Exception as e:
        print(f"Error while searching songs: {e}")
        return []  # 出现错误时返回空列表
    finally:
        cursor.close()  # 确保游标关闭


# -----------新增获取筛选选项的函数-----------------
def get_unique_artist_countries(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT country FROM Artists WHERE country IS NOT NULL")
        countries = [row[0] for row in cursor.fetchall()]
        return countries
    except Exception as e:
        print(f"Error while getting unique artist countries: {e}")
        return []
    finally:
        cursor.close()


def get_unique_artist_genders(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT gender FROM Artists WHERE gender IS NOT NULL")
        genders = [row[0] for row in cursor.fetchall()]
        return genders
    except Exception as e:
        print(f"Error while getting unique artist genders: {e}")
        return []
    finally:
        cursor.close()


def get_unique_song_languages(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT language FROM Songs WHERE language IS NOT NULL")
        languages = [row[0] for row in cursor.fetchall()]
        return languages
    except Exception as e:
        print(f"Error while getting unique song languages: {e}")
        return []
    finally:
        cursor.close()


def get_unique_song_genres(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DISTINCT genre FROM Songs WHERE genre IS NOT NULL")
        genres = [row[0] for row in cursor.fetchall()]
        return genres
    except Exception as e:
        print(f"Error while getting unique song genres: {e}")
        return []
    finally:
        cursor.close()


# -----------新增综合搜索和筛选的函数-----------------
# 搜索艺术家，根据查询关键词和筛选条件
def search_artists_with_filters(query=None, country=None, gender=None, connection=None):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        base_query = "SELECT * FROM Artists WHERE TRUE"
        params = []
        if query:
            base_query += " AND name ILIKE %s"
            params.append(f"%{query}%")
        if country:
            base_query += " AND country = %s"
            params.append(country)
        if gender:
            base_query += " AND gender = %s"
            params.append(gender)

        cursor.execute(base_query, tuple(params))
        artists = cursor.fetchall()
        return artists
    except Exception as e:
        print(f"Error while searching artists with filters: {e}")
        return []
    finally:
        cursor.close()


# 搜索歌曲，根据查询关键词和筛选条件
def search_songs_with_filters(query=None, language=None, genre=None, connection=None):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        base_query = """
            SELECT Songs.song_id, Songs.title, Songs.artist_id, Artists.name AS artist_name, 
                   Songs.album_id, Albums.title AS album_title, Songs.genre, Songs.audio_url, Songs.language
            FROM Songs
            JOIN Artists ON Songs.artist_id = Artists.artist_id
            JOIN Albums ON Songs.album_id = Albums.album_id
            WHERE TRUE
        """
        params = []
        if query:
            base_query += " AND Songs.title ILIKE %s"
            params.append(f"%{query}%")
        if language:
            base_query += " AND Songs.language = %s"
            params.append(language)
        if genre:
            base_query += " AND Songs.genre = %s"
            params.append(genre)

        cursor.execute(base_query, tuple(params))
        songs = cursor.fetchall()
        return songs
    except Exception as e:
        print(f"Error while searching songs with filters: {e}")
        return []
    finally:
        cursor.close()




# -----------初始化-----------------
if __name__ == "__main__":
    drop_all_tables()
    create_tables()

    # 插入艺术家
    insert_artist(1, '陈奕迅', '著名歌手', '中国香港', '男')
    insert_artist(2, 'Kanye West', '美国著名说唱歌手和音乐制作人', '美国', '男')
    insert_artist(3, 'The Weeknd', '加拿大歌手和音乐制作人', '加拿大', '男')
    insert_artist(4, '陶喆', '台湾歌手、作曲家和音乐制作人', '中国台湾', '男')
    insert_artist(5, '林俊杰', '著名歌手', '新加坡', '男')
    insert_artist(6, 'Taylor Swift', '美国歌手、词曲作者', '美国', '女')
    insert_artist(7, 'Adele', '英国歌手和词曲作者', '英国', '女')
    insert_artist(8, '周杰伦', '台湾歌手、音乐人', '中国台湾', '男')
    insert_artist(9, 'Eminem', '美国说唱歌手、制作人', '美国', '男')
    insert_artist(10, 'Billie Eilish', '美国歌手、词曲作者', '美国', '女')
    insert_artist(11, 'Ariana Grande', '美国歌手、词曲作者', '美国', '女')
    insert_artist(12, 'Ed Sheeran', '英国歌手、词曲作者', '英国', '男')
    insert_artist(13, 'Bruno Mars', '美国歌手、词曲作者', '美国', '男')
    insert_artist(14, 'Shawn Mendes', '加拿大歌手、词曲作者', '加拿大', '男')
    insert_artist(15, 'Selena Gomez', '美国歌手、演员', '美国', '女')

    # 插入专辑
    # 陈奕迅的专辑
    insert_album(1, 'Chin Up!', 1)
    insert_album(2, '准备中', 1)

    # Kanye West的专辑
    insert_album(3, 'Donda', 2)
    insert_album(4, 'Vultures 2', 2)

    # The Weeknd的专辑
    insert_album(5, 'After Hours', 3)
    insert_album(6, 'Starboy', 3)

    # 陶喆的专辑
    insert_album(7, 'David Tao', 4)

    # 林俊杰的专辑
    insert_album(8, '第二天堂(江南)', 5)

    # 其他艺术家的专辑（示例）
    insert_album(10, '1989', 6)
    insert_album(11, '25', 7)
    insert_album(12, 'Mojito', 8)
    insert_album(13, 'The Marshall Mathers LP', 9)
    insert_album(14, 'When We All Fall Asleep, Where Do We Go', 10)
    insert_album(15, 'Sweetener', 11)
    insert_album(16, 'Divide', 12)
    insert_album(17, '24K Magic', 13)
    insert_album(18, 'Wonder', 14)
    insert_album(19, 'Rare', 15)

    # 插入歌曲
    # 陈奕迅 - Chin Up! 专辑的歌曲
    insert_song('尘大师 Lightly', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 尘大师 Lightly.mp3', '国语')
    insert_song('焦焦焦 Hold On A Sec', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 焦焦焦 Hold On A Sec.mp3', '国语')
    insert_song('空城记 Something Missing', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 空城记 Something Missing.mp3',
                '国语')
    insert_song('盲婚哑嫁 The Code', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 盲婚哑嫁 The Code.mp3', '国语')
    insert_song('人啊人 Homo Sapiens', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 人啊人 Homo Sapiens.mp3', '国语')
    insert_song('社交恐惧癌 Don’t Mind Me', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 社交恐惧癌 Don’t Mind Me.mp3',
                '国语')
    insert_song('是但求其爱 The Search', 1, 1, 'Pop', r'陈奕迅/Chin Up!/陈奕迅 - 是但求其爱 The Search.mp3', '国语')
    insert_song('致明日的舞 A Dance For Tomorrow', 1, 1, 'Pop',
                r'陈奕迅/Chin Up!/陈奕迅 - 致明日的舞 A Dance For Tomorrow.mp3', '国语')

    # 陈奕迅 - 准备中 专辑的歌曲
    insert_song('黑洞', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 黑洞.mp3', '国语')
    insert_song('老细我撇先', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 老细我撇先.mp3', '国语')
    insert_song('梦的可能', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 梦的可能.mp3', '国语')
    insert_song('起点‧终站', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 起点‧终站.mp3', '国语')
    insert_song('人生马拉松', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 人生马拉松.mp3', '国语')
    insert_song('万圣节的一个传说', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 万圣节的一个传说.mp3', '国语')
    insert_song('无条件', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 无条件.mp3', '国语')
    insert_song('喜欢一个人', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 喜欢一个人.mp3', '国语')
    insert_song('心烧', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 心烧.mp3', '国语')
    insert_song('一个灵魂的独白', 1, 2, 'Pop', r'陈奕迅/准备中/陈奕迅 - 一个灵魂的独白.mp3', '国语')

    # Kanye West - Donda 专辑的歌曲
    insert_song('Tell The Vision', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Tell The Vision.mp3', 'English')
    insert_song('Remote Control', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Remote Control.mp3', 'English')
    insert_song('Pure Souls', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Pure Souls.mp3', 'English')
    insert_song('Praise God', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Praise God.mp3', 'English')
    insert_song('Ok Ok', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Ok Ok.mp3', 'English')
    insert_song('Ok Ok pt 2', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Ok Ok pt 2.mp3', 'English')
    insert_song('Off The Grid', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Off The Grid.mp3', 'English')
    insert_song('No Child Left Behind', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - No Child Left Behind.mp3',
                'English')
    insert_song('New Again', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - New Again.mp3', 'English')
    insert_song('Moon', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Moon.mp3', 'English')
    insert_song('Lord I Need You', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Lord I Need You.mp3', 'English')
    insert_song('Keep My Spirit Alive', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Keep My Spirit Alive.mp3',
                'English')
    insert_song('Junya', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Junya.mp3', 'English')
    insert_song('Junya pt 2', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Junya pt 2.mp3', 'English')
    insert_song('Jonah', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Jonah.mp3', 'English')
    insert_song('Jesus Lord', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Jesus Lord.mp3', 'English')
    insert_song('Jail', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Jail.mp3', 'English')
    insert_song('Jail pt 2', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Jail pt 2.mp3', 'English')
    insert_song('Hurricane', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Hurricane.mp3', 'English')
    insert_song('Heaven and Hell', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Heaven and Hell.mp3', 'English')
    insert_song('God Breathed', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - God Breathed.mp3', 'English')
    insert_song('Donda', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Donda.mp3', 'English')
    insert_song('Donda Chant', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Donda Chant.mp3', 'English')
    insert_song('Come to Life', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Come to Life.mp3', 'English')
    insert_song('Believe What I Say', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - Believe What I Say.mp3',
                'English')
    insert_song('24', 2, 3, 'Hip-Hop', r'Kanye West/Donda/Kanye West - 24.mp3', 'English')

    # Kanye West - Vultures 2 专辑的歌曲
    insert_song('530', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - 530.mp3', 'English')
    insert_song('BOMB', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - BOMB.mp3', 'English')
    insert_song('DEAD', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - DEAD.mp3', 'English')
    insert_song('FIELD TRIP', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - FIELD TRIP.mp3', 'English')
    insert_song('FOREVER ROLLING', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - FOREVER ROLLING.mp3',
                'English')
    insert_song('FOREVER', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - FOREVER.mp3', 'English')
    insert_song('FRIED', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - FRIED.mp3', 'English')
    insert_song('HUSBAND', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - HUSBAND.mp3', 'English')
    insert_song('ISABELLA', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - ISABELLA.mp3', 'English')
    insert_song('LIFESTYLE', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - LIFESTYLE.mp3', 'English')
    insert_song('MY SOUL', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - MY SOUL.mp3', 'English')
    insert_song('PROMOTION', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - PROMOTION.mp3', 'English')
    insert_song('RIVER', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - RIVER.mp3', 'English')
    insert_song('SKY CITY', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - SKY CITY.mp3', 'English')
    insert_song('SLIDE', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - SLIDE.mp3', 'English')
    insert_song('TIME MOVING SLOW', 2, 4, 'Hip-Hop', r'Kanye West/Vultures 2/Kanye West - TIME MOVING SLOW.mp3',
                'English')

    # The Weeknd - After Hours 专辑的歌曲
    insert_song('After Hours', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - After Hours.mp3', 'English')
    insert_song('Alone Again', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Alone Again.mp3', 'English')
    insert_song('Blinding Lights', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Blinding Lights.mp3', 'English')
    insert_song('Escape From LA', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Escape From LA.mp3', 'English')
    insert_song('Faith', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Faith.mp3', 'English')
    insert_song('Hardest To Love', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Hardest To Love.mp3', 'English')
    insert_song('Heartless', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Heartless.mp3', 'English')
    insert_song('In Your Eyes', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - In Your Eyes.mp3', 'English')
    insert_song('Repeat After Me (Interlude)', 3, 5, 'R&B',
                r'The Weeknd/After Hours/The Weeknd - Repeat After Me (Interlude).mp3', 'English')
    insert_song('Save Your Tears', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Save Your Tears.mp3', 'English')
    insert_song('Scared To Live', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Scared To Live.mp3', 'English')
    insert_song('Snowchild', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Snowchild.mp3', 'English')
    insert_song('Too Late', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Too Late.mp3', 'English')
    insert_song('Until I Bleed Out', 3, 5, 'R&B', r'The Weeknd/After Hours/The Weeknd - Until I Bleed Out.mp3',
                'English')

    # The Weeknd - Starboy 专辑的歌曲
    insert_song('A Lonely Night', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - A Lonely Night.mp3', 'English')
    insert_song('All I Know', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - All I Know.mp3', 'English')
    insert_song('Attention', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Attention.mp3', 'English')
    insert_song('Die For You', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Die For You.mp3', 'English')
    insert_song('False Alarm', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - False Alarm.mp3', 'English')
    insert_song('I Feel It Coming', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - I Feel It Coming.mp3', 'English')
    insert_song('Love To Lay', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Love To Lay.mp3', 'English')
    insert_song('Nothing Without You', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Nothing Without You.mp3',
                'English')
    insert_song('Ordinary Life', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Ordinary Life.mp3', 'English')
    insert_song('Party Monster', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Party Monster.mp3', 'English')
    insert_song('Reminder', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Reminder.mp3', 'English')
    insert_song('Rockin’', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Rockin’.mp3', 'English')
    insert_song('Secrets', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Secrets.mp3', 'English')
    insert_song('Six Feet Under', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Six Feet Under.mp3', 'English')
    insert_song('Starboy', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Starboy.mp3', 'English')
    insert_song('Stargirl Interlude', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - Stargirl Interlude.mp3', 'English')
    insert_song('True Colors', 3, 6, 'R&B', r'The Weeknd/Starboy/The Weeknd - True Colors.mp3', 'English')

    # 陶喆 - David Tao 专辑的歌曲
    insert_song('Airport Arrival', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - Airport Arrival.mp3', '国语')
    insert_song('Airport Take Off', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - Airport Take Off.mp3', '国语')
    insert_song('Answering Machine', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - Answering Machine.mp3', '国语')
    insert_song('Take 6 Minus 3', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - Take 6 Minus 3.mp3', '国语')
    insert_song('爱，很简单', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 爱，很简单.mp3', '国语')
    insert_song('机场的10_30', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 飞机场的10_30.mp3', '国语')
    insert_song('流沙', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 流沙.mp3', '国语')
    insert_song('沙滩 (钢琴版)', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 沙滩 (钢琴版).mp3', '国语')
    insert_song('沙滩', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 沙滩.mp3', '国语')
    insert_song('十七岁', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 十七岁.mp3', '国语')
    insert_song('是是非非', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 是是非非.mp3', '国语')
    insert_song('王八蛋', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 王八蛋.mp3', '国语')
    insert_song('望春风', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 望春风.mp3', '国语')
    insert_song('心乱飞', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 心乱飞.mp3', '国语')
    insert_song('再见以前先说再见', 4, 7, 'R&B', r'陶喆/David Tao/陶喆 - 再见以前先说再见.mp3', '国语')

    # 林俊杰 - 第二天堂(江南) 专辑的歌曲
    insert_song('Endless Road', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - Endless Road.mp3', '国语')
    insert_song('第二天堂', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 第二天堂.mp3', '国语')
    insert_song('豆浆油条', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 豆浆油条.mp3', '国语')
    insert_song('害怕', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 害怕.mp3', '国语')
    insert_song('江南', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 江南.mp3', '国语')
    insert_song('精灵', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 精灵.mp3', '国语')
    insert_song('距离', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 距离.mp3', '国语')
    insert_song('美人鱼', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 美人鱼.mp3', '国语')
    insert_song('起床了', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 起床了.mp3', '国语')
    insert_song('森林浴', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 森林浴.mp3', '国语')
    insert_song('天使心', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 天使心.mp3', '国语')
    insert_song('未完成', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 未完成.mp3', '国语')
    insert_song('相信无限', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 相信无限.mp3', '国语')
    insert_song('一开始', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 一开始.mp3', '国语')
    insert_song('子弹列车', 5, 8, 'R&B', r'林俊杰/第二天堂(江南)/林俊杰 - 子弹列车.mp3', '国语')

    # Taylor Swift - 1989 专辑的歌曲
    insert_song('Shake It Off', 10, 6, 'Pop', r'Taylor Swift/1989/Taylor Swift - Shake It Off.mp3', 'English')

    # Adele - 25 专辑的歌曲
    insert_song('Hello', 11, 7, 'Pop', r'Adele/25/Adele - Hello.mp3', 'English')

    # Jay Chou - Mojito 专辑的歌曲
    insert_song('Mojito', 12, 8, 'Pop', r'Jay Chou/Mojito/Jay Chou - Mojito.mp3', 'Mandarin')

    # Eminem - The Marshall Mathers LP 专辑的歌曲
    insert_song('The Real Slim Shady', 13, 9, 'Hip-Hop',
                r'Eminem/The Marshall Mathers LP/Eminem - The Real Slim Shady.mp3', 'English')

    # Billie Eilish - When We All Fall Asleep, Where Do We Go 专辑的歌曲
    insert_song('Bad Guy', 14, 10, 'Pop',
                r'Billie Eilish/When We All Fall Asleep, Where Do We Go/Billie Eilish - Bad Guy.mp3', 'English')

    # Ariana Grande - Sweetener 专辑的歌曲
    insert_song('No Tears Left to Cry', 15, 11, 'Pop',
                r'Ariana Grande/Sweetener/Ariana Grande - No Tears Left to Cry.mp3', 'English')

    # Ed Sheeran - Divide 专辑的歌曲
    insert_song('Shape of You', 16, 12, 'Pop', r'Ed Sheeran/Divide/Ed Sheeran - Shape of You.mp3', 'English')

    # Bruno Mars - 24K Magic 专辑的歌曲
    insert_song('24K Magic', 17, 13, 'Pop', r'Bruno Mars/24K Magic/Bruno Mars - 24K Magic.mp3', 'English')

    # Shawn Mendes - Wonder 专辑的歌曲
    insert_song('Wonder', 18, 14, 'Pop', r'Shawn Mendes/Wonder/Shawn Mendes - Wonder.mp3', 'English')

    # Selena Gomez - Rare 专辑的歌曲
    insert_song('Lose You to Love Me', 19, 15, 'Pop', r'Selena Gomez/Rare/Selena Gomez - Lose You to Love Me.mp3',
                'English')

    # 添加用户
    insert_user('Tank', 'Tank2028085771', 'jzl@250.com', '1008611', '2003', '2', '30')
    insert_user('x+x', 'x+x', 'x+x@163.com', '1008611', '2003', '2', '30')
    insert_user('Bean_cock', 'Gong', 'Roman@163.com', '1008611', '2005', '2', '30')
    insert_user('Bonjour', 'Bonjour', 'Bonjour@163.com', '1008611', '2003', '2', '30')
