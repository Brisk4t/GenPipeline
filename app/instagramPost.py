from instabot import Bot
import os
from dotenv import load_dotenv
import asyncio

class Instagram:
    def __init__(self, accounts):
        """
        Initialize Instagram bot with multiple accounts.
        """
        load_dotenv()
        self.accounts = accounts

    async def post_to_instagram(self, video_path, caption: str, tags=""):
        """
        Post a video to all Instagram accounts asynchronously.
        """
        await asyncio.gather(*(asyncio.to_thread(self.post_video, account, video_path, caption, tags) for account in self.accounts))

    def post_video(self, account, video_path, caption, tags):
        """
        Logs into an account and posts a video.
        """
        bot = Bot()
        bot.login(username=account['username'], password=account['password'])
        bot.upload_video(video_path, caption=caption, tags=tags)
        bot.logout()