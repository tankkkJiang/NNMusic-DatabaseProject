<<<<<<< HEAD
# NNMusic 音乐播放软件

## 简介

这是一个基于 openGauss 数据库和 Flask 后端的音乐播放软件，支持用户注册、登录、浏览和播放音乐，管理收藏以及编辑个人资料。

## 功能

- **用户注册与登录**：创建新账号并登录系统。
- **音乐播放**：浏览和播放歌曲。
- **收藏管理**：收藏喜欢的歌曲，方便访问。
- **个人资料管理**：查看和编辑个人信息。
- **搜索与筛选**：根据关键词、艺术家、专辑、语言和风格进行搜索和筛选。

## 技术栈

- **后端**：Python, Flask, psycopg2
- **数据库**：openGauss on openEuler
- **前端**：HTML, CSS, JavaScript

## 数据库设计

采用 openGauss 数据库，主要包含以下表：

- **Artists**：存储艺术家信息。
- **Albums**：存储专辑信息，关联艺术家。
- **Users**：存储用户信息。
- **Songs**：存储歌曲信息，关联艺术家和专辑。
- **Playlists**：存储用户创建的播放列表。
- **Favorites**：存储用户收藏的歌曲。

数据库初始化和操作函数位于 `database.py`，包括表的创建、数据插入、用户验证、信息更新及各种查询功能。

## 后端介绍

后端使用 Flask 框架，通过 `app.py` 实现：

- **路由管理**：处理用户注册、登录、主页访问、个人资料查看与编辑、歌曲和专辑浏览等请求。
- **用户会话管理**：使用 Flask 会话管理用户登录状态。
- **数据交互**：通过 `database.py` 提供的函数与 openGauss 数据库交互，实现数据的增删改查。
- **错误处理**：统一处理异常，确保系统稳定运行。

## 数据库功能概要

数据库操作封装在 `database.py` 中，主要包括以下功能：

### 获取数据（get_函数）

- **get_all_songs(conn)**：获取所有歌曲信息，包含艺术家和专辑名称。
- **get_song_by_id(connection, song_id)**：根据歌曲ID获取详细信息。
- **get_all_albums(connection)**：获取所有专辑及其艺术家信息。
- **get_songs_by_album(connection, album_id)**：根据专辑ID获取所属歌曲。
- **get_all_artists(connection)**：获取所有艺术家信息。
- **get_songs_by_artist(connection, artist_id)**：根据艺术家ID获取其所有歌曲。
- **get_artist_info_by_artist(connection, artist_id)**：获取艺术家名称和简介。
- **get_user_info(user_name)**：获取指定用户的详细信息。
- **get_user_favorites(connection, user_name)**：获取用户收藏的所有歌曲。
- **get_unique_artist_countries(connection)**、**get_unique_artist_genders(connection)**、**get_unique_song_languages(connection)**、**get_unique_song_genres(connection)**：获取艺术家和歌曲的唯一筛选选项。

### 插入数据（insert_函数）

- **insert_user(user_name, password, email, tel, year, month, day)**：插入新用户数据。
- **insert_artist(artist_id, name, bio, country, gender)**：插入新艺术家数据。
- **insert_album(album_id, title, artist_id)**：插入新专辑数据。
- **insert_song(title, artist_id, album_id, genre, audio_url, language)**：插入新歌曲数据。
- **insert_favorites(user_name, song_name, artist_name)**：添加用户收藏的歌曲。

### 更新与删除

- **update_user_info(user_id, user_name, email, tel, year, month, day)**：更新用户信息。
- **remove_favorites(user_name, song_name)**：移除用户收藏的歌曲。

### 搜索功能

- **search_albums(query, connection)**：根据关键词搜索专辑。
- **search_artists(query, connection)**：根据关键词搜索艺术家。
- **search_songs(query, connection)**：根据关键词搜索歌曲。
- **search_artists_with_filters(query, country, gender, connection)**：根据关键词和筛选条件搜索艺术家。
- **search_songs_with_filters(query, language, genre, connection)**：根据关键词和筛选条件搜索歌曲。

## 安装与运行

1. **克隆项目**

   ```bash
   git clone https://github.com/你的用户名/音乐播放软件.git
   cd 音乐播放软件
   ```

2. **配置数据库**

   - 安装并配置 openGauss 数据库。
   - 更新 `database.py` 中的数据库连接参数以匹配你的数据库设置。
   - 初始化数据库并插入初始数据：

     ```bash
     python database.py
     ```

3. **运行后端服务**

   ```bash
   python app.py
   ```

4. **访问前端**

   打开浏览器，访问 `http://localhost:5000` 开始使用音乐播放软件。

## 项目结构

```
音乐播放软件/
├── app.py
├── database.py
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── home.html
│   ├── profile.html
│   ├── edit_profile.html
│   ├── songs.html
│   ├── albums.html
│   ├── album_songs.html
│   ├── artists.html
│   ├── artist_songs.html
│   └── play.html
├── static/
│   ├── images/
│   └── audio/
└── README.md
```

## 创新与优势

1. **综合搜索与筛选功能**：用户可以通过关键词结合多种筛选条件（如国籍、性别、语言、风格）进行精准搜索，大幅提升查找效率和用户体验。
2. **动态收藏管理**：实时添加或移除收藏歌曲，系统即时更新收藏状态，并在歌曲列表中动态显示，增强用户互动性。
=======
# NNMusic-DatabaseProject

This Dababase Project "NN-Music" is proudly devised by Xie Jiaxuan, Jiang Zhenglan, Hu Yucheng.  
The project is based on the implementation of a database system using the openGauss database under the openEuler operating system, which is a major assignment for the undergraduate course on Database System Principles.  
This repository contains the front-end and back-end related to the database system, and ultimately uses the content of this database to implement a visual web page, with the relevant code provided for reference.
>>>>>>> 8697499173b09554adab0db4f883d8d61d5ee4d0
