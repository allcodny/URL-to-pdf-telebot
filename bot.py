import asyncio
import pdfkit
from requests  import get
from bs4 import BeautifulSoup
import string
import os
import zipfile
import re
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

AUTHOR = "@allcodny"

MAX_URLS = 50
MAX_PAGE_SIZE = 400
MAX_CONVERSION_TIME = 60

options_mobile = {
    'encoding': "UTF-8",
    'user-style-sheet': 'resize.css'
}
options = {'encoding': "UTF-8",}

load_dotenv()
bot = Bot(os.getenv("TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

url_pattern = r'https?://[^\s\)\]\}<>"]+'

async def convert_url_to_pdf(url: str, id: int, n: int, m: int, mobile: bool):
    try:
        response = get(url)
        content_length = len(response.content)
        if content_length > MAX_PAGE_SIZE * 1024:
            size_mb = content_length / 1024
            await bot.edit_message_text(
                f'Страница слишком большая ({size_mb:.1f} КБ). Максимум: {MAX_PAGE_SIZE} КБ', 
                chat_id=id, 
                message_id=m
            )
            return False
        title = BeautifulSoup(response.content, 'html.parser').title.string
        if title is None:
            title = "Сайт в pdf"
        title = str(n) + ". " + title.translate(str.maketrans('', '', string.punctuation)) + ".pdf"
        if mobile:
            options_ = options_mobile
        else:
            options_ = options
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: pdfkit.from_url(url, title, options=options_)
                ),
                timeout=MAX_CONVERSION_TIME
            )
        return title
    except TimeoutError:
            await bot.edit_message_text(
                f'Превышено время ожидания ({MAX_CONVERSION_TIME} секунд)',
                chat_id=id,
                message_id=m
            )
            return False
    except Exception as e:
        await bot.edit_message_text(f'Произошла ошибка: {e}', chat_id=id, message_id=m)
        print(f'Error: {e}')
        return False
    

@dp.message(Command("start"))
@dp.message(Command("help"))
async def delete_command(message: types.Message, state: FSMContext):
    await state.clear()
    await bot.send_message(message.from_user.id,
    f'''Отправьте боту сообщение содержащее ссылку или несколько ссылок на web-страницу, бот сконвертирует и отправит вам pdf-файл.
\nПо ошибкам и вопросам писать: {AUTHOR}\n<a href="https://github.com/N0Fanru/URL-to-pdf-telebot">Исходный код бота</a>''',
    parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@dp.message()
async def echo_message(message: types.Message, state: FSMContext):
    if message.chat.type == 'private':
        if await state.get_data() != {}:
            await bot.send_message(message.from_user.id, "Сначала дождитесь завершения предыдущих конвертаций.")
            return 0
        urls = re.findall(url_pattern, message.text)
        if message.entities:
            for entity in message.entities:
                if entity.type == "text_link":
                    urls.append(entity.url)
        if len(urls) > MAX_URLS:
            await bot.send_message(message.from_user.id, f"Максимальное количество ссылок на обработку: {MAX_URLS}")
        elif len(urls) == 0:
            state.clear()
            await bot.send_message(message.from_user.id, "Ни одного url не найдено")
        else:
            await state.update_data(urls=urls)
            markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text='Обычный', callback_data='normal'),
                types.InlineKeyboardButton(text='Для телефона', callback_data='mobile')],
                [types.InlineKeyboardButton(text='Отмена', callback_data='cancel')]
            ])
            await bot.send_message(message.from_user.id, f"Найдено {len(urls)} ссылок, выберите режим.", reply_markup=markup)


@dp.message(Command("cancel"))
async def callback_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await bot.send_message(message.from_user.id, "Действие отменено.")

@dp.callback_query(F.data == 'cancel')
async def callback_cancel(call: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await call.message.edit_text("Действие отменено.")
    except TelegramBadRequest:
        await call.answer("Сообщение устарело")

async def convert_and_send(urls: list, id: int, mes_id: int, mobile: bool, state):
    await bot.delete_message(id, mes_id)
    n = 0
    com = 0
    if len(urls) > 1 and len(urls) <= MAX_URLS:
        name = f'archive-{id}{mes_id}.zip'
        zipf = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
        for url in urls:
            n += 1
            m = await bot.send_message(id, f"Процесс над файлом номер {n}, это может занять некоторое время.")
            file = await convert_url_to_pdf(url, id, n, m.message_id, mobile)
            if file:
                zipf.write(file)
                os.remove(file)
                com += 1
        zipf.close()
        await bot.send_document(
                chat_id=id,
                document=FSInputFile(name)
                )
        os.remove(name)
        await bot.send_message(id, f"Успешно сконвертировано {com} из {n} ссылок")
    elif len(urls) == 1:
        m = await bot.send_message(id, f"Процесс над файлом, это может занять некоторое время.")
        file = await convert_url_to_pdf(urls[0], id, "", m.message_id, mobile)
        if file:
            await bot.send_document(
                    chat_id=id,
                    document=FSInputFile(file)
                    )
            os.remove(file)
    await state.clear()

@dp.callback_query(F.data == 'normal')
async def callback_normal(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await convert_and_send(data.get('urls'), call.from_user.id, call.message.message_id, False, state)

@dp.callback_query(F.data == 'mobile')
async def callback_mobile(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await convert_and_send(data.get('urls'), call.from_user.id, call.message.message_id, True, state)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
