from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import INDEX_CHANNELS, LOG_CHANNEL, MOVIE_UPDATE_CHANNEL
from database.ia_filterdb import save_file, unpack_new_file_id
from utils import get_poster, temp
import re
from database.users_chats_db import db

processed_movies = set()
media_filter = filters.document | filters.video

@Client.on_message(filters.chat(INDEX_CHANNELS) & media_filter)
async def media(bot, message):
    bot_id = bot.me.id
    media = getattr(message, message.media.value, None)
    if media.mime_type in ['video/mp4', 'video/x-matroska']: 
        media.file_type = message.media.value
        media.caption = message.caption
        success_sts = await save_file(media)
        if success_sts == 'suc' and await db.get_send_movie_update_status(bot_id):
            file_id, file_ref = unpack_new_file_id(media.file_id)
            await send_movie_updates(bot, file_name=media.file_name, caption=media.caption, file_id=file_id)

async def get_imdb(file_name):
    imdb_file_name = await movie_name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb and 'poster' in imdb:
        return imdb.get('poster')
    return "https://telegra.ph/file/88d845b4f8a024a71465d.jpg"  # Default poster

async def get_year(file_name):
    imdb_file_name = await movie_name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb and 'year' in imdb:
        return imdb.get('year')
    return None

async def get_genres(file_name):
    imdb_file_name = await movie_name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb and 'genres' in imdb:
        return imdb.get('genres')
    return "Animation"

async def get_seasons(file_name):
    imdb_file_name = await movie_name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb and 'seasons' in imdb:
        return imdb.get('seasons')
    return None

async def movie_name_format(file_name):
  filename = re.sub(r'http\S+', '', re.sub(r'@\w+|#\w+', '', file_name).replace('_', ' ').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('{', '').replace('}', '').replace('.', ' ').replace('@', '').replace(':', '').replace(';', '').replace("'", '').replace('-', '').replace('!', '')).strip()
  return filename

async def check_qualities(text, qualities):
    quality = [q for q in qualities if q.lower() in text.lower()]
    return ", ".join(quality)

async def check_languages(text, languages):
    matched_languages = []
    for lang, abbreviations in languages.items():
        for abbr in abbreviations:
            if abbr.lower() in text.lower():
                matched_languages.append(lang)
                break  # Avoid duplicate detection
    return " + ".join(matched_languages)

async def send_movie_updates(bot, file_name, caption, file_id):
    try:
        channels = await db.get_movie_update_channels() or MOVIE_UPDATE_CHANNEL

        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None      
        pattern = r"(?i)(?:s|season)0*(\d{1,2})"
        episode_pattern = r"(?i)(?:e|ep|episode)0*(\d{1,3})"
        season = re.search(pattern, caption)
        episode = re.search(episode_pattern, caption)
        if not season:
            season = re.search(pattern, file_name) 
        if year:
            file_name = file_name[:file_name.find(year) + 4]      
        if not year:
            if season:
                season = season.group(1) if season else None       
                file_name = file_name[:file_name.find(season) + 1]
        # Set movie quality
        qualities = ["HDCAM", "HDRip", "SDTV", "HDTV", "BluRay", "HD DVD", "WEB-DL", "CAMRip", "PreDVD", 
                     "DVDscr", "WEB-HD", "BDRip", "DVDRip", "HDTS"]
        quality = await check_qualities(caption, qualities) or "HDRip"

        # Detect languages
        language_map = {
            "Tamil": ["Tamil", "Tam"],
            "Bengali": ["Bengali", "Ben"],
            "English": ["English", "Eng"],
            "Marathi": ["Marathi", "Mar"],
            "Hindi": ["Hindi", "Hin"],
            "Telugu": ["Telugu", "Tel"],
            "Malayalam": ["Malayalam", "Mal"],
            "Kannada": ["Kannada", "Kan"],
            "Punjabi": ["Punjabi", "Pun"],
            "Gujarati": ["Gujarati", "Guj"],
            "Korean": ["Korean", "Kor"],
            "Japanese": ["Japanese", "Jap"],
            "Bhojpuri": ["Bhojpuri", "Bjp"],
            "Chinese": ["Chinese", "Ch"],
            "Dual": ["Dual"],
            "Multi": ["Multi"]
        }
        language = await check_languages(caption, language_map) or "Tamil"

        # Format movie name
        movie_name = await movie_name_format(file_name)    
        if movie_name in processed_movies:
            return 
        processed_movies.add(movie_name)    
        # Remove year from movie name
        if year:
            movie_name = movie_name.replace(f" {year}", "")
        if season:
            movie_name = movie_name.replace(f" {season}", "")
        if episode:
            movie_name = movie_name.replace(f" {episode}", "")

        # Get poster URL
        poster_url = await get_imdb(movie_name)
        imdb_year = await get_year(movie_name)
        genres = await get_genres(movie_name)
        seasons = await get_seasons(movie_name)
        caption_message = f"<b>Anime :- <code>{movie_name}</code>\n\nYear :- {year if year else imdb_year}\n\nSeason :- {season}\n\nTotal Seasons :- {seasons}\n\nEpisode :- {episode}\n\nGenres :- {genres}\n\nLanguage :- {language}\n\nQuality :- {quality.replace(', ', ' ')}\n\n📤 Uploading By :- <a href=https://t.me/TN_BOTZ>TN BOTZ</a></b>"
        # Prepare buttons
        search_movie = movie_name.replace(" ", '-')
        if year:
            search_movie = search_movie.replace(f"-{year}", "")  # Remove the year part from the search string
        btn = [
            [InlineKeyboardButton('📂 Get File 📂', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')],
            [InlineKeyboardButton('📥 How to Download 📥', url='https://t.me/How_downlode_dpbots/22')]
        ]
        reply_markup = InlineKeyboardMarkup(btn)

        # Send to channels
        for channel_id in channels:
            try:
                await bot.send_photo(
                    channel_id,
                    photo=poster_url,
                    caption=caption_message,
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Failed to send update to channel {channel_id}. Error: {e}")
                await bot.send_message(LOG_CHANNEL, f"Failed to send update to channel {channel_id}. Error: {e}")
    except Exception as e:
        print(f"Failed to send movie update. Error: {e}")
        await bot.send_message(LOG_CHANNEL, f"Failed to send movie update. Error: {e}")
        
