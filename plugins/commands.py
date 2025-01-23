from __future__ import unicode_literals
import os, requests, asyncio, math, time, wget, logging, random, string, pytz, re, base64
from telegraph import upload_file
from time import time as time_now
import datetime
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup , ForceReply, ReplyKeyboardMarkup, Message, CallbackQuery
from database.ia_filterdb import Media, get_file_details, delete_files
from database.users_chats_db import db
from info import INDEX_CHANNELS, MOVIE_UPDATE_CHANNEL, ADMINS, IS_VERIFY, VERIFY_TUTORIAL, VERIFY_EXPIRE, SHORTLINK_API, SHORTLINK_URL, DELETE_TIME, SUPPORT_LINK, UPDATES_LINK, LOG_CHANNEL, PICS, IS_STREAM, PAYMENT_QR, OWNER_USERNAME, PM_FILE_DELETE_TIME, OWNER_UPI_ID
from utils import get_settings, get_size, is_subscribed, is_check_admin, get_shortlink, get_verify_status, update_verify_status, save_group_settings, temp, get_readable_time, get_wish, get_seconds
from plugins.pm_filter import auto_filter
from pyrogram.errors import PeerIdInvalid, FloodWait
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL
from asyncio import sleep
from plugins.rename.filedetect import refunc
from info import RENAME_MODE
import humanize
import random

MOVIE_UPDATE_CHANNEL = []

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            username = f'@{message.chat.username}' if message.chat.username else 'Private'
            await client.send_message(LOG_CHANNEL, script.NEW_GROUP_TXT.format(message.chat.title, message.chat.id, username, total))       
            await db.add_chat(message.chat.id, message.chat.title)
        wish = get_wish()
        user = message.from_user.mention if message.from_user else "Dear"
        btn = [[
            InlineKeyboardButton('⚡️ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ⚡️', url=UPDATES_LINK),
            InlineKeyboardButton('💡 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ 💡', url=SUPPORT_LINK)
        ]]
        await message.reply(text=f"<b>ʜᴇʏ {user}, <i>{wish}</i>\nʜᴏᴡ ᴄᴀɴ ɪ ʜᴇʟᴘ ʏᴏᴜ??</b>", reply_markup=InlineKeyboardMarkup(btn))
        return 
        
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.NEW_USER_TXT.format(message.from_user.mention, message.from_user.id))

    verify_status = await get_verify_status(message.from_user.id)
    if verify_status['is_verified'] and datetime.datetime.now() > verify_status['expire_time']:
        await update_verify_status(message.from_user.id, is_verified=False)

    if len(message.command) == 2 and message.command[1].startswith('getfile'):
        searches = message.command[1].split("-", 1)[1] 
        search = searches.replace('-',' ')
        message.text = search
        s = await message.reply(f"<b>⚠️ `{message.text}` Searching...</b>", quote=True)
        await auto_filter(client, message, s) 
        return
    
    if (len(message.command) != 2) or (len(message.command) == 2 and message.command[1] == 'start'):
        buttons = [[
            InlineKeyboardButton("+ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ +", url=f'http://t.me/{temp.U_NAME}?startgroup=start')
        ],[
            InlineKeyboardButton('ℹ️ ᴜᴘᴅᴀᴛᴇs', url=UPDATES_LINK),
            InlineKeyboardButton('🧑‍💻 sᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
        ],[
            InlineKeyboardButton('👨‍🚒 ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('🔎 sᴇᴀʀᴄʜ ɪɴʟɪɴᴇ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('📚 ᴀʙᴏᴜᴛ', callback_data='about')
        ],[
            InlineKeyboardButton('💰 ᴇᴀʀɴ ᴜɴʟɪᴍɪᴛᴇᴅ ᴍᴏɴᴇʏ ʙʏ ʙᴏᴛ 💰', callback_data='earn')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, get_wish()),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return

    if len(message.command) == 2 and message.command[1] == "plans":
        btn = [            
            [InlineKeyboardButton("ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ʀᴇᴄᴇɪᴘᴛ 🧾", url=OWNER_USERNAME)],
            [InlineKeyboardButton("⚠️ ᴄʟᴏsᴇ / ᴅᴇʟᴇᴛᴇ ⚠️", callback_data="close_data")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        await message.reply_photo(
            photo=PAYMENT_QR,
            caption=script.PREMIUM_PLAN_TEXT.format(OWNER_UPI_ID),
            reply_markup=reply_markup
        )
        return

    mc = message.command[1]

    if mc.startswith('verify'):
        _, token = mc.split("_", 1)
        verify_status = await get_verify_status(message.from_user.id)
        if verify_status['verify_token'] != token:
            return await message.reply("Your verify token is invalid.")
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=VERIFY_EXPIRE)
        await update_verify_status(message.from_user.id, is_verified=True, verified_time=time_now(), expire_time=expiry_time)
        if verify_status["link"] == "":
            reply_markup = None
        else:
            btn = [[
                InlineKeyboardButton("📌 Get File 📌", url=f'https://t.me/{temp.U_NAME}?start={verify_status["link"]}')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
        await message.reply(f"✅ You successfully verified until: {get_readable_time(VERIFY_EXPIRE)}", reply_markup=reply_markup, protect_content=True)
        return
    
    verify_status = await get_verify_status(message.from_user.id)
    if not await db.has_premium_access(message.from_user.id):
        if IS_VERIFY and not verify_status['is_verified']:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(message.from_user.id, verify_token=token, link="" if mc == 'inline_verify' else mc)
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://t.me/{temp.U_NAME}?start=verify_{token}')
            btn = [[
                InlineKeyboardButton("🧿 Verify 🧿", url=link)
            ],[
                InlineKeyboardButton('🗳 Tutorial 🗳', url=VERIFY_TUTORIAL)
            ]]
            await message.reply("You not verified today! Kindly verify now. 🔐", reply_markup=InlineKeyboardMarkup(btn), protect_content=True)
            return

    settings = await get_settings(int(mc.split("_", 2)[1]))
    if not await db.has_premium_access(message.from_user.id):
        if settings['fsub']:
            btn = await is_subscribed(client, message, settings['fsub'])
            if btn:
                btn.append(
                    [InlineKeyboardButton("💫 Join Our Channel 💫", url="https://t.me/+YeduZ6Ztq2YwNTdl")],
                    [InlineKeyboardButton("🔁 Try Again 🔁", callback_data=f"checksub#{mc}")]
                )
                reply_markup = InlineKeyboardMarkup(btn)
                await message.reply_photo(
                    photo=random.choice(PICS),
                    caption=f"👋 Hello {message.from_user.mention},\n\nPlease join my 'Updates Channel' and try again. 😇",
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
                return 
        
    if mc.startswith('all'):
        _, grp_id, key = mc.split("_", 2)
        files = temp.FILES.get(key)
        if not files:
            return await message.reply('No Such All Files Exist!')
        settings = await get_settings(int(grp_id))
        file_ids = []
        total_files = await message.reply(f"<b><i>🗂 Total files - <code>{len(files)}</code></i></b>")
        for file in files:
            CAPTION = settings['caption']
            f_caption = CAPTION.format(
                file_name=file.file_name,
                file_size=get_size(file.file_size),
                file_caption=file.caption
            )      
            if settings.get('is_stream', IS_STREAM):
                btn = [[
                    InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f"stream#{file.file_id}")
                ],[
                    InlineKeyboardButton('⚡️ ᴜᴘᴅᴀᴛᴇs', url=UPDATES_LINK),
                    InlineKeyboardButton('💡 ꜱᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
                ],[
                    InlineKeyboardButton('⁉️ ᴄʟᴏsᴇ ⁉️', callback_data='close_data')
                ]]
            else:
                btn = [[
                    InlineKeyboardButton('⚡️ ᴜᴘᴅᴀᴛᴇs', url=UPDATES_LINK),
                    InlineKeyboardButton('💡 ꜱᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
                ],[
                    InlineKeyboardButton('⁉️ ᴄʟᴏsᴇ ⁉️', callback_data='close_data')
                ]]

            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file.file_id,
                caption=f_caption,
                protect_content=False if await db.has_premium_access(message.from_user.id) else True,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            file_ids.append(msg.id)

        time = get_readable_time(PM_FILE_DELETE_TIME)
        vp = await message.reply(f"Nᴏᴛᴇ: Tʜɪs ғɪʟᴇs ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇ ɪɴ {time} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛs. Sᴀᴠᴇ ᴛʜᴇ ғɪʟᴇs ᴛᴏ sᴏᴍᴇᴡʜᴇʀᴇ ᴇʟsᴇ")
        await asyncio.sleep(PM_FILE_DELETE_TIME)
        buttons = [[InlineKeyboardButton('ɢᴇᴛ ғɪʟᴇs ᴀɢᴀɪɴ', callback_data=f"get_del_send_all_files#{grp_id}#{key}")]] 
        await client.delete_messages(
            chat_id=message.chat.id,
            message_ids=file_ids + [total_files.id]
        )
        await vp.edit("Tʜᴇ ғɪʟᴇ ʜᴀs ʙᴇᴇɴ ɢᴏɴᴇ ! Cʟɪᴄᴋ ɢɪᴠᴇɴ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪᴛ ᴀɢᴀɪɴ.", reply_markup=InlineKeyboardMarkup(buttons))
        return

    type_, grp_id, file_id = mc.split("_", 2)
    files_ = await get_file_details(file_id)
    if not files_:
        return await message.reply('No Such File Exist!')
    files = files_[0]
    settings = await get_settings(int(grp_id))
    if type_ != 'shortlink' and settings['shortlink']:
        if not await db.has_premium_access(message.from_user.id):
            link = await get_shortlink(settings['url'], settings['api'], f"https://t.me/{temp.U_NAME}?start=shortlink_{grp_id}_{file_id}")
            btn = [[
                InlineKeyboardButton("♻️ Get File ♻️", url=link)
            ],[
                InlineKeyboardButton("📍 ʜᴏᴡ ᴛᴏ ᴏᴘᴇɴ ʟɪɴᴋ 📍", url=settings['tutorial'])
            ]]
            await message.reply(f"[{get_size(files.file_size)}] {files.file_name}\n\nYour file is ready, Please get using this link. 👍", reply_markup=InlineKeyboardMarkup(btn), protect_content=True)
            return
            
    CAPTION = settings['caption']
    f_caption = CAPTION.format(
        file_name = files.file_name,
        file_size = get_size(files.file_size),
        file_caption=files.caption
    )
    if settings.get('is_stream', IS_STREAM):
        btn = [[
            InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f"stream#{file_id}")
        ],[
            InlineKeyboardButton('⚡️ ᴜᴘᴅᴀᴛᴇs', url=UPDATES_LINK),
            InlineKeyboardButton('💡 ꜱᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
        ],[
            InlineKeyboardButton('⁉️ ᴄʟᴏsᴇ ⁉️', callback_data='close_data')
        ]]
    else:
        btn = [[
            InlineKeyboardButton('⚡️ ᴜᴘᴅᴀᴛᴇs', url=UPDATES_LINK),
            InlineKeyboardButton('💡 ꜱᴜᴘᴘᴏʀᴛ', url=SUPPORT_LINK)
        ],[
            InlineKeyboardButton('⁉️ ᴄʟᴏsᴇ ⁉️', callback_data='close_data')
        ]]
    vp = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=False if await db.has_premium_access(message.from_user.id) else True,
        reply_markup=InlineKeyboardMarkup(btn)
    )
    time = get_readable_time(PM_FILE_DELETE_TIME)
    msg = await vp.reply(f"Nᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇ ɪɴ {time} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛs. Sᴀᴠᴇ ᴛʜᴇ ғɪʟᴇ ᴛᴏ sᴏᴍᴇᴡʜᴇʀᴇ ᴇʟsᴇ")
    await asyncio.sleep(PM_FILE_DELETE_TIME)
    btns = [[
        InlineKeyboardButton('ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ', callback_data=f"get_del_file#{grp_id}#{file_id}")
    ]]
    await msg.delete()
    await vp.delete()
    await vp.reply("Tʜᴇ ғɪʟᴇ ʜᴀs ʙᴇᴇɴ ɢᴏɴᴇ ! Cʟɪᴄᴋ ɢɪᴠᴇɴ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪᴛ ᴀɢᴀɪɴ.", reply_markup=InlineKeyboardMarkup(btns))

@Client.on_message(filters.command('index_channels'))
async def channels_info(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    ids = INDEX_CHANNELS
    if not ids:
        return await message.reply("Not set INDEX_CHANNELS")
    text = '**Indexed Channels:**\n\n'
    for id in ids:
        chat = await bot.get_chat(id)
        text += f'{chat.title}\n'
    text += f'\n**Total:** {len(ids)}'
    await message.reply(text)

@Client.on_message(filters.command('stats'))
async def stats(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    files = await Media.count_documents()
    users = await db.total_users_count()
    chats = await db.total_chat_count()
    premium = await db.all_premium_users()
    u_size = get_size(await db.get_db_size())
    u_size_int = await db.get_db_size()
    f_size = get_size(536870912 - u_size_int)
    uptime = get_readable_time(time_now() - temp.START_TIME)
    await message.reply_text(script.STATUS_TXT.format(files, users, chats, premium, u_size, f_size, uptime))    
    
@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")
    grp_id = message.chat.id
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group.')
    settings = await get_settings(grp_id)
    if settings is not None:
        buttons = [[
            InlineKeyboardButton('Auto Filter', callback_data=f'setgs#auto_filter#{settings["auto_filter"]}#{grp_id}'),
            InlineKeyboardButton('✅ Yes' if settings["auto_filter"] else '❌ No', callback_data=f'setgs#auto_filter#{settings["auto_filter"]}#{grp_id}')
        ],[
            InlineKeyboardButton('IMDb Poster', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}'),
            InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}')
        ],[
            InlineKeyboardButton('Spelling Check', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}'),
            InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}')
        ],[
            InlineKeyboardButton('Auto Delete', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}'),
            InlineKeyboardButton(f'{get_readable_time(DELETE_TIME)}' if settings["auto_delete"] else '❌ No', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}')
        ],[
            InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',),
            InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No', callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}'),
        ],[
            InlineKeyboardButton('Shortlink', callback_data=f'setgs#shortlink#{settings["shortlink"]}#{grp_id}'),
            InlineKeyboardButton('✅ Yes' if settings["shortlink"] else '❌ No', callback_data=f'setgs#shortlink#{settings["shortlink"]}#{grp_id}'),
        ],[
            InlineKeyboardButton('Result Page', callback_data=f'setgs#links#{settings["links"]}#{str(grp_id)}'),
            InlineKeyboardButton('⛓ Link' if settings["links"] else '🧲 Button', callback_data=f'setgs#links#{settings["links"]}#{str(grp_id)}')
        ],[
            InlineKeyboardButton('Stream', callback_data=f'setgs#is_stream#{settings.get("is_stream", IS_STREAM)}#{str(grp_id)}'),
            InlineKeyboardButton('✅ On' if settings.get("is_stream", IS_STREAM) else '❌ Off', callback_data=f'setgs#is_stream#{settings.get("is_stream", IS_STREAM)}#{str(grp_id)}')
        ],[
            InlineKeyboardButton('❌ Close ❌', callback_data='close_data')
        ]]
        await message.reply_text(
            text=f"Change your settings for <b>'{message.chat.title}'</b> as your wish. ⚙",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text('Something went wrong!')

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")      
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group.')
    try:
        template = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")   
    await save_group_settings(grp_id, 'template', template)
    await message.reply_text(f"Successfully changed template for {title} to\n\n{template}")  
    
@Client.on_message(filters.command('set_caption'))
async def save_caption(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")      
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group.')
    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!") 
    await save_group_settings(grp_id, 'caption', caption)
    await message.reply_text(f"Successfully changed caption for {title} to\n\n{caption}")
        
@Client.on_message(filters.command('set_shortlink'))
async def save_shortlink(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")    
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group.')
    try:
        _, url, api = message.text.split(" ", 2)
    except:
        return await message.reply_text("<b>Command Incomplete:-\n\ngive me a shortlink & api along with the command...\n\nEx:- <code>/shortlink mdisklink.link 5843c3cc645f5077b2200a2c77e0344879880b3e</code>")   
    try:
        await get_shortlink(url, api, f'https://t.me/{temp.U_NAME}')
    except:
        return await message.reply_text("Your shortlink API or URL invalid, Please Check again!")   
    await save_group_settings(grp_id, 'url', url)
    await save_group_settings(grp_id, 'api', api)
    await message.reply_text(f"Successfully changed shortlink for {title} to\n\nURL - {url}\nAPI - {api}")
    
@Client.on_message(filters.command('get_custom_settings'))
async def get_custom_settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group...')    
    settings = await get_settings(grp_id)
    text = f"""Custom settings for: {title}

Shortlink URL: {settings["url"]}
Shortlink API: {settings["api"]}

IMDb Template: {settings['template']}

File Caption: {settings['caption']}

Welcome Text: {settings['welcome_text']}

Tutorial Link: {settings['tutorial']}

Force Channels: {str(settings['fsub'])[1:-1] if settings['fsub'] else 'Not Set'}"""

    btn = [[
        InlineKeyboardButton(text="Close", callback_data="close_data")
    ]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)

@Client.on_message(filters.command('set_welcome'))
async def save_welcome(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")      
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group.')
    try:
        welcome = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")    
    await save_group_settings(grp_id, 'welcome_text', welcome)
    await message.reply_text(f"Successfully changed welcome for {title} to\n\n{welcome}")
        
@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    reply = message.reply_to_message
    if reply and reply.media: msg = await message.reply("Processing...⏳", quote=True)
    else: return await message.reply('Reply to file with /delete which you want to delete', quote=True)
    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None: break
    else: return await msg.edit('This Is Not Supported File Format')
    file_id, file_ref = unpack_new_file_id(media.file_id)
    result = await Media.collection.delete_one({'_id': file_id})
    if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
        else:
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count: await msg.edit('File Is Successfully Deleted From Database')
            else: await msg.edit('File Not Found In Database')

@Client.on_message(filters.command('delete_all'))
async def delete_all_index(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    btn = [[
        InlineKeyboardButton(text="YES", callback_data="delete_all")
    ],[
        InlineKeyboardButton(text="CLOSE", callback_data="close_data")
    ]]
    files = await Media.count_documents()
    if int(files) == 0:
        return await message.reply_text('Not have files to delete')
    await message.reply_text(f'Total {files} files have.\nDo you want to delete all?', reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command('set_tutorial'))
async def set_tutorial(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")       
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('You not admin in this group.')
    try:
        tutorial = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")   
    await save_group_settings(grp_id, 'tutorial', tutorial)
    await message.reply_text(f"Successfully changed tutorial for {title} to\n\n{tutorial}")

#@Client.on_message(filters.command('telegraph'))
async def telegraph(bot, message):
    reply_to_message = message.reply_to_message
    if not reply_to_message:
        return await message.reply('Reply to any photo or video.')
    file = reply_to_message.photo or reply_to_message.video or None
    if file is None:
        return await message.reply('Invalid media.')
    if file.file_size >= 5242880:
        await message.reply_text(text="Send less than 5MB")   
        return
    text = await message.reply_text(text="ᴘʀᴏᴄᴇssɪɴɢ....")   
    media = await reply_to_message.download()  
    try:
        response = upload_file(media)
    except Exception as e:
        await text.edit_text(text=f"Error - {e}")
        return    
    try:
        os.remove(media)
    except:
        pass
    await text.edit_text(
        text=f"<b>Link :-</b>\n\n<code>https://graph.org{response[0]}</code>",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup( [[
            InlineKeyboardButton(text="Open Link", url=f"https://graph.org{response[0]}"),
            InlineKeyboardButton(text="Share Link", url=f"https://telegram.me/share/url?url=https://graph.org{response[0]}")
            ],[
            InlineKeyboardButton(text="✗ Close ✗", callback_data="close")
            ]])
    )

def upload_image_requests(image_path):
    upload_url = "https://envs.sh"

    try:
        with open(image_path, 'rb') as file:
            files = {'file': file} 
            response = requests.post(upload_url, files=files)

            if response.status_code == 200:
                return response.text.strip() 
            else:
                return print(f"Upload failed with status code {response.status_code}")

    except Exception as e:
        print(f"Error during upload: {e}")
        return None

def upload_image_requests(image_path):
    upload_url = "https://envs.sh"

    try:
        with open(image_path, 'rb') as file:
            files = {'file': file} 
            response = requests.post(upload_url, files=files)

            if response.status_code == 200:
                return response.text.strip() 
            else:
                return print(f"Upload failed with status code {response.status_code}")

    except Exception as e:
        print(f"Error during upload: {e}")
        return None

@Client.on_message(filters.command("telegraph") & filters.private)
async def telegraph_upload(bot, update):
    t_msg = await bot.ask(chat_id = update.from_user.id, text = "Now Send Me Your Photo Or Video Under 5MB To Get Media Link.")
    if not t_msg.media:
        return await update.reply_text("**Only Media Supported.**")
    path = await t_msg.download()
    uploading_message = await update.reply_text("<b>ᴜᴘʟᴏᴀᴅɪɴɢ...</b>")
    try:
        image_url = upload_image_requests(path)
        if not image_url:
            return await uploading_message.edit_text("**Failed to upload file.**")
    except Exception as error:
        await uploading_message.edit_text(f"**Upload failed: {error}**")
        return
    await uploading_message.edit_text(
        text=f"<b>Link :-</b>\n\n<code>{image_url}</code>",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup( [[
            InlineKeyboardButton(text="Open Link", url=image_url),
            InlineKeyboardButton(text="Share Link", url=f"https://telegram.me/share/url?url={image_url}")
            ],[
            InlineKeyboardButton(text="✗ Close ✗", callback_data="close")
            ]])
    )

@Client.on_message(filters.command('ping'))
async def ping(client, message):
    start_time = time_now.monotonic()
    msg = await message.reply("👀")
    end_time = time_now.monotonic()
    await msg.edit(f'{round((end_time - start_time) * 1000)} ms')
    
@Client.on_message(filters.command("add_premium"))
async def give_premium_cmd_handler(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    if len(message.command) == 3:
        user_id = int(message.command[1])  # Convert the user_id to integer
        time = message.command[2]        
        seconds = await get_seconds(time)
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time} 
            await db.update_user(user_data)  # Use the update_user method to update or insert user data
            await message.reply_text("Premium access added to the user.")            
            await client.send_message(
                chat_id=user_id,
                text=f"<b>ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ꜰᴏʀ {time} ᴇɴᴊᴏʏ 😀\n</b>",                
            )
        else:
            await message.reply_text("Invalid time format. Please use '1day for days', '1hour for hours', or '1min for minutes', or '1month for months' or '1year for year'")
    else:
        await message.reply_text("<b>Usage: /add_premium user_id time \n\nExample /add_premium 1252789 10day \n\n(e.g. for time units '1day for days', '1hour for hours', or '1min for minutes', or '1month for months' or '1year for year')</b>")
        
@Client.on_message(filters.command("remove_premium"))
async def remove_premium_cmd_handler(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    if len(message.command) == 2:
        user_id = int(message.command[1])  # Convert the user_id to integer
        time = "1s"
        seconds = await get_seconds(time)
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time}  # Using "id" instead of "user_id"
            await db.update_user(user_data)  # Use the update_user method to update or insert user data
            await message.reply_text("Premium access removed to the user.")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>premium removed by admins \n\n Contact Admin if this is mistake \n\n 👮 Admin : {OWNER_USERNAME} \n</b>",
                disable_web_page_preview=True
            )
        else:
            await message.reply_text("Invalid time format.'")
    else:
        await message.reply_text("Usage: /remove_premium user_id")
        
@Client.on_message(filters.command("plan"))
async def plans_list(client, message):
    btn = [[
        InlineKeyboardButton("ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ʀᴇᴄᴇɪᴘᴛ 🧾", url=OWNER_USERNAME)
    ],[
        InlineKeyboardButton("⚠️ ᴄʟᴏsᴇ / ᴅᴇʟᴇᴛᴇ ⚠️", callback_data="close_data")
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await message.reply_photo(
        photo=PAYMENT_QR,
        caption=script.PREMIUM_PLAN_TEXT.format(OWNER_UPI_ID),
        reply_markup=reply_markup
    )
        
@Client.on_message(filters.command("myplan"))
async def check_plans_cmd(client, message):
    user_id  = message.from_user.id
    if await db.has_premium_access(user_id):         
        remaining_time = await db.check_remaining_uasge(user_id)             
        expiry_time = remaining_time + datetime.datetime.now()
        await message.reply_text(f"**Your plans details are :\n\nRemaining Time : {remaining_time}\n\nExpirytime : {expiry_time}**")
    else:
        btn = [ 
            [InlineKeyboardButton("ɢᴇᴛ ғʀᴇᴇ ᴛʀᴀɪʟ ғᴏʀ 𝟻 ᴍɪɴᴜᴛᴇꜱ ☺️", callback_data="get_trail")],
            [InlineKeyboardButton("ʙᴜʏ sᴜʙsᴄʀɪᴘᴛɪᴏɴ : ʀᴇᴍᴏᴠᴇ ᴀᴅs", callback_data="buy_premium")],
            [InlineKeyboardButton("⚠️ ᴄʟᴏsᴇ / ᴅᴇʟᴇᴛᴇ ⚠️", callback_data="close_data")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        m=await message.reply_sticker("CAACAgIAAxkBAAIBTGVjQbHuhOiboQsDm35brLGyLQ28AAJ-GgACglXYSXgCrotQHjibHgQ")         
        await message.reply_text("**😢 You Don't Have Any Premium Subscription.\n\n Check Out Our Premium /plan**",reply_markup=reply_markup)
        await asyncio.sleep(2)
        await m.delete()

@Client.on_message(filters.private & filters.command("set_pm_search"))
async def set_pm_search(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return
    try:
        option = (message.text).split(" ", 1)[1].lower()
    except IndexError:
        return await message.reply_text("<b>💔 Invalid option. Please send me 'on' or 'off' / 'true' or 'false' after the command.</b>")
    if option in ['on', 'true']:
        await db.update_pm_search_status(bot_id, enable=True)
        await message.reply_text("<b>✅️ ᴘᴍ ꜱᴇᴀʀᴄʜ ᴇɴᴀʙʟᴇᴅ ꜰʀᴏᴍ ɴᴏᴡ ᴜꜱᴇʀꜱ ᴀʙʟᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ ɪɴ ʙᴏᴛ ᴘᴍ.</b>")
    elif option in ['off', 'false']:
        await db.update_pm_search_status(bot_id, enable=False)
        await message.reply_text("<b>❌️ ᴘᴍ ꜱᴇᴀʀᴄʜ ᴅɪꜱᴀʙʟᴇᴅ, ɴᴏ ᴏɴᴇ ᴜꜱᴇʀꜱ ᴀʙʟᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ ɪɴ ʙᴏᴛ ᴘᴍ.</b>")
    else:
        await message.reply_text("<b>💔 Invalid option. Please send me 'on' or 'off' / 'true' or 'false' after the command.</b>")

@Client.on_message(filters.command('set_fsub'))
async def set_fsub(client, message):
    user_id = message.from_user.id
    if not user_id:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")      
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, user_id):
        return await message.reply_text('You not admin in this group.')
    try:
        ids = message.text.split(" ", 1)[1]
        fsub_ids = list(map(int, ids.split()))
    except IndexError:
        return await message.reply_text("Command Incomplete!\n\nCan multiple channel add separate by spaces. Like: /set_fsub id1 id2 id3")
    except ValueError:
        return await message.reply_text('Make sure ids is integer.')        
    channels = "Channels:\n"
    for id in fsub_ids:
        try:
            chat = await client.get_chat(id)
        except Exception as e:
            return await message.reply_text(f"<code>{id}</code> is invalid!\nMake sure this bot admin in that channel.\n\nError - {e}")
        if chat.type != enums.ChatType.CHANNEL:
            return await message.reply_text(f"<code>{id}</code> is not channel.")
        channels += f'{chat.title}\n'
    await save_group_settings(grp_id, 'fsub', fsub_ids)
    await message.reply_text(f"Successfully set force channels for {title} to\n\n<code>{channels}</code>")

@Client.on_message(filters.command('remove_fsub'))
async def remove_fsub(client, message):
    grp_id = message.chat.id
    settings = await get_settings(int(grp_id))
    user_id = message.from_user.id
    chat_type = message.chat.type
    if not user_id:
        return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("Use this command in group.")
    if not await is_check_admin(client, grp_id, user_id):
        return await message.reply_text('You not admin in this group.')
    if not settings['fsub']:
        await message.reply_text("ʏᴏᴜ ᴅɪᴅɴ'ᴛ ᴀᴅᴅᴇᴅ ᴀɴʏ ꜰᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ᴄʜᴀɴɴᴇʟ...") # query.answer not work in command so I can change to message.reply_text
        return
    await save_group_settings(grp_id, 'fsub', None)
    await message.reply_text("<b>Successfully removed your force channel id...</b>")

@Client.on_message(filters.command("set_channels") & filters.user(ADMINS))
async def set_channel(bot, message):
    global MOVIE_UPDATE_CHANNEL
    try:
        command_args = message.text.split(" ", 1)
        if len(command_args) != 2:
            await message.reply_text("Usage: `set_channel <channel_id1> <channel_id2> ...`")
            return
        channel_ids = command_args[1].split()
        new_channels = []
        for channel_id in channel_ids:
            if channel_id.startswith("-") and channel_id[1:].isdigit():
                new_channels.append(int(channel_id))
            else:
                await message.reply_text(f"Invalid channel ID: `{channel_id}`")
                return
        MOVIE_UPDATE_CHANNEL = new_channels
        await db.set_movie_update_channels(MOVIE_UPDATE_CHANNEL)
        await message.reply_text(
            f"Successfully updated the channels: `{', '.join(map(str, MOVIE_UPDATE_CHANNEL))}`"
        )
    except Exception as e:
        print(f"Error in set_channel: {e}")
        await message.reply_text(f"An error occurred: `{e}`")

@Client.on_message(filters.command("get_channels") & filters.user(ADMINS))
async def get_channel(bot, message):
    try:
        channels = await db.get_movie_update_channels()
        if not channels:
            channels = MOVIE_UPDATE_CHANNEL
        channels_list = "\n".join([str(channel) for channel in channels])
        await message.reply_text(f"Current movie update channels:\n\n{channels_list}")
    except Exception as e:
        print(f"Error in get_channel: {e}")
        await message.reply_text(f"An error occurred: `{e}`")

@Client.on_message(filters.command(['song', 'mp3']) & filters.private)
async def song(client, message):
    user_id = message.from_user.id 
    user_name = message.from_user.first_name 
    rpk = "["+user_name+"](tg://user?id="+str(user_id)+")"
    query = ''
    for i in message.command[1:]:
        query += ' ' + str(i)
    print(query)
    m = await message.reply(f"**ѕєαrchíng чσur ѕσng...!\n {query}**")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]       
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f'thumb{title}.jpg'
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, 'wb').write(thumb.content)
        performer = f"[NETWORKS™]" 
        duration = results[0]["duration"]
        url_suffix = results[0]["url_suffix"]
        views = results[0]["views"]
    except Exception as e:
        print(str(e))
        return await m.edit("Example: /song vaa vaathi song")
                
    await m.edit("**dσwnlσαdíng чσur ѕσng...!**")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_file = ydl.prepare_filename(info_dict)
            ydl.process_info(info_dict)

        cap = f"**BY›› [UPDATE]({CHNL_LNK})**"
        secmul, dur, dur_arr = 1, 0, duration.split(':')
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
        await message.reply_audio(
            audio_file,
            caption=cap,            
            quote=False,
            title=title,
            duration=dur,
            performer=performer,
            thumb=thumb_name
        )            
        await m.delete()
    except Exception as e:
        await m.edit("**🚫 𝙴𝚁𝚁𝙾𝚁 🚫**")
        print(e)
    try:
        os.remove(audio_file)
        os.remove(thumb_name)
    except Exception as e:
        print(e)

def get_text(message: Message) -> [None,str]:
    text_to_return = message.text
    if message.text is None:
        return None
    if " " not in text_to_return:
        return None
    try:
        return message.text.split(None, 1)[1]
    except IndexError:
        return None


@Client.on_message(filters.command(["video", "mp4"]))
async def vsong(client, message: Message):
    urlissed = get_text(message)
    pablo = await client.send_message(message.chat.id, f"**𝙵𝙸𝙽𝙳𝙸𝙽𝙶 𝚈𝙾𝚄𝚁 𝚅𝙸𝙳𝙴𝙾** `{urlissed}`")
    if not urlissed:
        return await pablo.edit("Example: /video Your video link")     
    search = SearchVideos(f"{urlissed}", offset=1, mode="dict", max_results=1)
    mi = search.result()
    mio = mi["search_result"]
    mo = mio[0]["link"]
    thum = mio[0]["title"]
    fridayz = mio[0]["id"]
    mio[0]["channel"]
    kekme = f"https://img.youtube.com/vi/{fridayz}/hqdefault.jpg"
    await asyncio.sleep(0.6)
    url = mo
    sedlyf = wget.download(kekme)
    opts = {
        "format": "best",
        "addmetadata": True,
        "key": "FFmpegMetadata",
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "outtmpl": "%(id)s.mp4",
        "logtostderr": False,
        "quiet": True,
    }
    try:
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(url, download=True)
    except Exception as e:
        return await pablo.edit_text(f"**𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍 𝙵𝚊𝚒𝚕𝚎𝚍 𝙿𝚕𝚎𝚊𝚜𝚎 𝚃𝚛𝚢 𝙰𝚐𝚊𝚒𝚗..♥️** \n**Error :** `{str(e)}`")       
    
    file_stark = f"{ytdl_data['id']}.mp4"
    capy = f"""**𝚃𝙸𝚃𝙻𝙴 :** [{thum}]({mo})\n**𝚁𝙴𝚀𝚄𝙴𝚂𝚃𝙴𝙳 𝙱𝚈 :** {message.from_user.mention}"""

    await client.send_video(
        message.chat.id,
        video=open(file_stark, "rb"),
        duration=int(ytdl_data["duration"]),
        file_name=str(ytdl_data["title"]),
        thumb=sedlyf,
        caption=capy,
        supports_streaming=True,        
        reply_to_message_id=message.id 
    )
    await pablo.delete()
    for files in (sedlyf, file_stark):
        if files and os.path.exists(files):
            os.remove(files)
            
@Client.on_message(filters.command("stickerid") & filters.private)
async def stickerid(bot, message):
    s_msg = await bot.ask(chat_id = message.from_user.id, text = "Now Send Me Your Sticker")
    if s_msg.sticker:
        await s_msg.reply_text(f"**Sticker ID is**  \n `{s_msg.sticker.file_id}` \n \n ** Unique ID is ** \n\n`{s_msg.sticker.file_unique_id}`")
    else: 
        await s_msg.reply_text("Oops !! Not a sticker file")
        
@Client.on_message(filters.private & filters.command("rename"))
async def rename_start(client, message):
    if RENAME_MODE == False:
        return 
    msg = await client.ask(message.chat.id, "**Now send me your file/video/audio to rename.**")
    if not msg.media:
        return await message.reply("**Please send me supported media.**")
    if msg.media in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT, enums.MessageMediaType.AUDIO]:
        file = getattr(msg, msg.media.value)
        filename = file.file_name
        filesize = humanize.naturalsize(file.file_size) 
        fileid = file.file_id
        text = f"""**__𝙿𝚕𝚎𝚊𝚜𝚎 𝙴𝚗𝚝𝚎𝚛 𝙽𝚎𝚠 𝙵𝚒𝚕𝚎𝙽𝚊𝚖𝚎...__**\n\n**File Name** :- `{filename}`\n\n**File Size** :- `{filesize}`"""
        await message.reply_text(text)
        kk = await client.listen(message.from_user.id)
        await refunc(client, message, kk.text, msg)
      
