import logging
import re
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated, Message
import asyncio
import requests
from bs4 import BeautifulSoup
from utils import fetch_page_source

# Замените на токен вашего бота
BOT_TOKEN = "8162503602:AAEpmVV7-AiFQDUvTQHKmqhYNSZemg_H4VM"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
router = Router()
dp = Dispatcher()
USER_ID = 1251966117

GOOGLE_FORM = re.compile(
    r'https://docs.google.com/forms/d/(?:e/)?([a-zA-Z0-9_-]+)(?:/viewform)?(?:/edit)?'
)
GOOGLE_FORM_SHORT = re.compile(r'https://forms\.gle/([a-zA-Z0-9_-]+)')


@router.message(Command("id"))
async def get_user_id(message: Message):
    logging.info(f'id: {message.from_user.id}')
    await message.reply(f"Ваш ID: {message.from_user.id}")

async def get_form_data(form_url):

    try:
        html, current_url = fetch_page_source(form_url)
        
        logging.info(f"url {current_url}")
        soup = BeautifulSoup(html, 'lxml')


        match = GOOGLE_FORM.match(current_url)
        if not match:
          logging.warning(f"Invalid Google Form URL-2: {current_url}")
          return None, None, None

        form_id = match.group(1)
        logging.info(f"Actual form_id: {form_id}")

        form_elements_head = []
        if soup.head:
            form_elements_head = soup.head.find_all(
                'input', {'name': re.compile(r'entry\.\d+')}
            )
        
        form_elements_body = soup.body.find_all(
            'input', {'name': re.compile(r'entry\.\d+')}
        )

        form_elements = form_elements_head + form_elements_body

        entry_ids = []

        logging.info(f'form_elements: {form_elements}')
        for el in form_elements:
            if 'name' in el.attrs:
                entry_ids.append(el.attrs['name'])

        entry_ids = [entry_id.replace("_sentinel", "") for entry_id in entry_ids]
        
        logging.info(f'entry_ids: {entry_ids}')

        time_text = None
        if "19:30-20:15" in soup.text:
            time_text = "19:30-20:15"
        elif "17:00-17:45" in soup.text:
            time_text = "17:00-17:45"
        elif "19:30 - 20:15" in soup.text:
            time_text = "19:30 - 20:15"
        elif "17:00 - 17:45":
            time_text = "17:00 - 17:45"

        with open("bs_text.txt", 'w', encoding="utf-8") as file:
            file.write(soup.text)

        logging.info(f'Time text found: {time_text}')

        if len(entry_ids) < 3:
          logging.warning(f"Not enough form elements found: {form_url}")
          return None, None, None
          
        return entry_ids[:3], time_text, form_id, current_url

    except Exception as e:
        logging.error(f"Error fetching Google Form HTML-2: {e}")
        return None, None, None

async def submit_form(form_url, text1, text2, choice, form_id, entry_ids=None):
    if not form_id or not entry_ids:
        entry_ids, time_text, form_id, url = await get_form_data(form_url)
        if not entry_ids:
            return False

    if time_text is None:
        time_text = choice
    
    logging.info(f"time_text: {time_text}")
    logging.info(f"Actual form_id: {form_id}")

    text_field_1_entry_id, text_field_2_entry_id, single_choice_entry_id = entry_ids
    if "/d/e/" in url:
        post_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
    else:
        post_url = f"https://docs.google.com/forms/d/{form_id}/formResponse"
    logging.info(f"ids: {entry_ids}")
    payload = {
            f"{text_field_1_entry_id}": text1,
            f"{text_field_2_entry_id}": text2,
            f"{single_choice_entry_id}": time_text,
        }
    try:
        response = requests.post(post_url, data=payload)
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Error submitting Google Form: {e}")
        return False

async def process_google_form_link(message: Message, url):
    text1 = "Павел Юлов"
    text2 = "11 Прог"
    choice = "19:30-20:15" 
    logging.info(f'url: {url}')
    success = await submit_form(url, text1, text2, choice, None)

    if success:
        await bot.send_message(USER_ID, "✅ Данные успешно отправлены в Google Form!")
    else:
        await bot.send_message(USER_ID, "❌ Ошибка при отправке данных в Google Form.")

async def extract_and_reply(message: Message):
    if message.text:
        urls = GOOGLE_FORM.findall(message.text)
        short_urls = GOOGLE_FORM_SHORT.findall(message.text)
       
        if urls:
            for url in urls:
                match = GOOGLE_FORM.search(message.text)
                if match:
                    full_url = match.group(0)
                    await process_google_form_link(message, full_url)
        
        if short_urls:
           for short_url in short_urls:
              short_match = GOOGLE_FORM_SHORT.search(message.text)
              if short_match:
                  full_short_url = short_match.group(0)
                  await process_google_form_link(message, full_short_url)


@dp.message()
async def handle_message(message: Message):
    logging.info(f'id: {message.from_user.id}')
    await extract_and_reply(message)

# Обработчик для добавления бота в группу
# @dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
# async def on_bot_added_to_chat(event: ChatMemberUpdated):
#     if event.new_chat_member.status == ChatMemberStatus.MEMBER:
#         await bot.send_message(event.chat.id, "Привет, теперь я буду отслеживать ссылки на Google Forms в этом чате!")
    
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())