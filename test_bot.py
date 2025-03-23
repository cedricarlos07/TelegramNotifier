from telegram import Bot
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot():
    try:
        bot = Bot('7244520668:AAHhLLrMyNUvK1IWW9UJQ38nP7Kwh-N2UBE')
        me = await bot.get_me()
        logger.info(f'Bot info: {me}')
        await bot.close()
    except Exception as e:
        logger.error(f'Erreur lors du test du bot : {e}')

if __name__ == '__main__':
    asyncio.run(test_bot()) 