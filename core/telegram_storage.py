import os
import io
import aiohttp
import logging
from typing import Optional, Union

logger = logging.getLogger("TelegramStorage")

class TelegramStorageBridge:
    """
    PROJECT APEX - The Russian Trick (Infinite Free Edge Storage)
    
    Instead of paying for AWS S3 or filling up the Oracle VM disk, we use the 
    Telegram Bot API as a limitless CDN.
    - Max file size: 50MB (Bot API limit)
    - Total storage limit: INFINITE
    - Bandwidth cost: $0
    """
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID") # Private channel to dump files
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram Storage Bridge disabled: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
            self.enabled = False
        else:
            self.enabled = True

    async def upload_file(self, filename: str, file_data: Union[bytes, io.BytesIO]) -> Optional[str]:
        """
        Uploads a file to Telegram and returns the Telegram file_id.
        This file_id can be stored in the database instead of the raw file.
        """
        if not self.enabled:
            return None
            
        logger.info(f"Uploading {filename} to Telegram Infinite Storage...")
        
        url = f"{self.api_url}/sendDocument"
        
        if isinstance(file_data, io.BytesIO):
            file_data = file_data.getvalue()
            
        data = aiohttp.FormData()
        data.add_field('chat_id', self.chat_id)
        data.add_field('document', file_data, filename=filename)
        data.add_field('caption', f"PROJECT APEX Storage: {filename}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Extract the file_id of the uploaded document
                        file_id = result['result']['document']['file_id']
                        logger.info(f"Successfully uploaded {filename}. File ID: {file_id}")
                        return file_id
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to upload to Telegram: {error_text}")
                        return None
            except Exception as e:
                logger.error(f"Telegram upload exception: {e}")
                return None

    async def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Downloads a file from Telegram using its file_id.
        """
        if not self.enabled:
            return None
            
        # Step 1: Get the file path
        url_get_path = f"{self.api_url}/getFile?file_id={file_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url_get_path) as response:
                    if response.status == 200:
                        result = await response.json()
                        file_path = result['result']['file_path']
                        
                        # Step 2: Download the actual file
                        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                        async with session.get(download_url) as dl_response:
                            if dl_response.status == 200:
                                return await dl_response.read()
                    return None
            except Exception as e:
                logger.error(f"Telegram download exception: {e}")
                return None
