from telegram import Bot
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_group_id(group_username):
    try:
        bot = Bot('7244520668:AAHhLLrMyNUvK1IWW9UJQ38nP7Kwh-N2UBE')
        chat = await bot.get_chat(group_username)
        logger.info(f'Informations du groupe :')
        logger.info(f'ID : {chat.id}')
        logger.info(f'Titre : {chat.title}')
        logger.info(f'Type : {chat.type}')
        logger.info(f'Le bot est administrateur : {chat.get_member(bot.id).status == "administrator"}')
        await bot.close()
    except Exception as e:
        logger.error(f'Erreur lors de la récupération des informations du groupe : {e}')

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python get_group_id.py @nom_du_groupe")
        sys.exit(1)
    
    group_username = sys.argv[1]
    asyncio.run(get_group_id(group_username)) 