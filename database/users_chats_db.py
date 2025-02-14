from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_NAME, DATABASE_URL, IMDB_TEMPLATE, WELCOME_TEXT, LINK_MODE, TUTORIAL, SHORTLINK_URL, SHORTLINK_API, SHORTLINK, FILE_CAPTION, IMDB, WELCOME, SPELL_CHECK, PROTECT_CONTENT, AUTO_FILTER, AUTO_DELETE, IS_STREAM, VERIFY_EXPIRE, IS_PM_SEARCH, IS_SEND_MOVIE_UPDATE, FORCE_SUB
import time
import datetime

client = AsyncIOMotorClient(DATABASE_URL)
mydb = client[DATABASE_NAME]

class Database:
    default_setgs = {
        'auto_filter': AUTO_FILTER,
        'file_secure': PROTECT_CONTENT,
        'imdb': IMDB,
        'spell_check': SPELL_CHECK,
        'auto_delete': AUTO_DELETE,
        'welcome': WELCOME,
        'welcome_text': WELCOME_TEXT,
        'template': IMDB_TEMPLATE,
        'caption': FILE_CAPTION,
        'url': SHORTLINK_URL,
        'api': SHORTLINK_API,
        'shortlink': SHORTLINK,
        'tutorial': TUTORIAL,
        'links': LINK_MODE,
        'fsub': FORCE_SUB,
        'is_stream': IS_STREAM
    }

    default_verify = {
        'is_verified': False,
        'verified_time': 0,
        'verify_token': "",
        'link': "",
        'expire_time': 0
    }
    
    def __init__(self):
        self.col = mydb.Users
        self.grp = mydb.Groups
        self.users = mydb.uersz
        self.botcol = mydb["bot_id"]
        self.movies_update_channel = mydb.movies_update_channel
        self.channel_col = mydb.channel_data
        self.users = mydb.UsersData
        self.black = mydb.TamilMV_List
        self.tb = mydb.TamilBlaster_List
        self.tr = mydb.TamilRockers_List
        self.domains = mydb.Domains
    
    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
            verify_status=self.default_verify
        )

    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
            settings=self.default_setgs
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def delete_chat(self, grp_id):
        await self.grp.delete_many({'id': int(grp_id)})

    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    
    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)

    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    
    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        
    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})      
    
    async def get_settings(self, id):
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', self.default_setgs)
        return self.default_setgs
    
    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
    
    async def get_verify_status(self, user_id):
        user = await self.col.find_one({'id':int(user_id)})
        if user:
            info = user.get('verify_status', self.default_verify)
            try:
                info.get('expire_time')
            except:
                expire_time = info.get('verified_time') + datetime.timedelta(seconds=VERIFY_EXPIRE)
                info.append({
                    'expire_time': expire_time
                })
            return info
        return self.default_verify
        
    async def update_verify_status(self, user_id, verify):
        await self.col.update_one({'id': int(user_id)}, {'$set': {'verify_status': verify}})
    
    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    
    async def get_all_chats(self):
        return self.grp.find({})
    
    async def get_db_size(self):
        return (await mydb.command("dbstats"))['dataSize']
   
    async def get_user(self, user_id):
        user_data = await self.users.find_one({"id": user_id})
        return user_data
            
    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is None:
                # User previously used the free trial, but it has ended.
                return False
            elif isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            else:
                await self.users.update_one({"id": user_id}, {"$set": {"expiry_time": None}})
        return False
    
    async def check_remaining_uasge(self, userid):
        user_id = userid
        user_data = await self.get_user(user_id)        
        expiry_time = user_data.get("expiry_time")
        # Calculate remaining time
        remaining_time = expiry_time - datetime.datetime.now()
        return remaining_time
    
    async def get_free_trial_status(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            return user_data.get("has_free_trial", False)
        return False

    async def give_free_trail(self, userid):        
        user_id = userid
        seconds = 5*60         
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time, "has_free_trial": True}
        await self.users.update_one({"id": user_id}, {"$set": user_data}, upsert=True)

    async def all_premium_users(self):
        count = await self.users.count_documents({
        "expiry_time": {"$gt": datetime.datetime.now()}
        })
        return count

    async def get_send_movie_update_status(self, bot_id):
        bot = await self.botcol.find_one({'id': bot_id})
        if bot and bot.get('movie_update_feature'):
            return bot['movie_update_feature']
        else:
            return IS_SEND_MOVIE_UPDATE

    async def update_send_movie_update_status(self, bot_id, enable):
        bot = await self.botcol.find_one({'id': int(bot_id)})
        if bot:
            await self.botcol.update_one({'id': int(bot_id)}, {'$set': {'movie_update_feature': enable}})
        else:
            await self.botcol.insert_one({'id': int(bot_id), 'movie_update_feature': enable})  

    async def get_pm_search_status(self, bot_id):
        bot = await self.botcol.find_one({'id': bot_id})
        if bot and bot.get('bot_pm_search'):
            return bot['bot_pm_search']
        else:
            return IS_PM_SEARCH

    async def update_pm_search_status(self, bot_id, enable):
        bot = await self.botcol.find_one({'id': int(bot_id)})
        if bot:
            await self.botcol.update_one({'id': int(bot_id)}, {'$set': {'bot_pm_search': enable}})
        else:
            await self.botcol.insert_one({'id': int(bot_id), 'bot_pm_search': enable})

    async def set_movie_update_channels(self, channels):
        """
        Save the list of movie update channels to the database.
        """
        await self.movies_update_channel.update_one(
            {}, {'$set': {'channels': channels}}, upsert=True
        )

    async def get_movie_update_channels(self):
        """
        Retrieve the list of movie update channels from the database.
        """
        result = await self.movies_update_channel.find_one({})
        return result.get("channels", []) if result else []

    async def set_channel(self, command_type, destination_channel_ids, original_text, replace_text, my_link, web_link, my_username):
        channel_data = {
            "command_type": command_type,
            "destination_channel_ids": destination_channel_ids,
            "original_text": original_text,
            "replace_text": replace_text,
            "my_link": my_link,
            "web_link": web_link,
            "my_username": my_username
        }
        
        # Update or insert the data for the given command_type
        await self.channel_col.update_one(
            {"command_type": command_type},
            {"$set": channel_data},
            upsert=True  # If the command_type doesn't exist, create a new entry
        )

    async def get_channel(self, command_type):
        return await self.channel_col.find_one({
            "command_type": command_type
        })
    
    async def get_all_chats_count(self):
        grp = await self.grp.find().to_list(None)
        return grp

    def tamilmv(self, Name, link, url):
        return dict(
            FileName = Name,
            magnet_link = link,
            magnet_url = url,
            upload_date=datetime.date.today().isoformat()
        )

    async def add_tamilmv(self, Name, link, url):
        user = self.tamilmv(Name, link, url)
        await self.black.insert_one(user)

    async def is_tamilmv_exist(self, Name, link, url):
        user = await self.black.find_one({'magnet_url': url})
        return True if user else False

    def tbx(self, Name, link, url):
        return dict(
            FileName = Name,
            magnet_link = link,
            magnet_url = url,
            upload_date=datetime.date.today().isoformat()
        )

    async def add_tb(self, Name, link, url):
        user = self.tbx(Name, link, url)
        await self.tb.insert_one(user)

    async def is_tb_exist(self, Name, link, url):
        user = await self.tb.find_one({'magnet_url': url})
        return True if user else False

    # TamilRockers DB Functions

    def tr(self, Name, link, url):
        return dict(
            FileName = Name,
            magnet_link = link,
            magnet_url = url,
            upload_date=datetime.date.today().isoformat()
        )

    async def add_tr(self, Name, link, url):
        user = self.tr(Name, link, url)
        await self.tr.insert_one(user)

    async def is_tr_exist(self, Name, link, url):
        user = await self.tr.find_one({'magnet_url': url})
        return True if user else False

    # Domain Management Functions
    async def update_domain(self, key, url):
        """
        Add a new domain or update an existing one with the provided key and URL.
        """
        existing_domain = await self.domains.find_one({"key": key})
        if existing_domain:
            # Update existing domain
            await self.domains.update_one({"key": key}, {"$set": {"url": url}})
        else:
            # Insert new domain
            await self.domains.insert_one({"key": key, "url": url})
    
    async def get_all_domains(self):
        """
        Retrieve all domains from the database.
        """
        domains = {}
        async for domain in self.domains.find():
            domains[domain["key"]] = domain["url"]
        return domains

    async def get_domain(self, key):
        """
        Retrieve a specific domain URL by its key.
        """
        domain = await self.domains.find_one({"key": key})
        return domain["url"] if domain else None

    async def delete_domain(self, key):
        """
        Delete a domain by its key.
        """
        result = await self.domains.delete_one({"key": key})
        return result.deleted_count > 0
        
db = Database()
