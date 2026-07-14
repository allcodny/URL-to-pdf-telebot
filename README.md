[![eng](https://img.shields.io/badge/lang-en-en)](https://github.com/allcodny/URL-to-pdf-telebot/blob/main/README.md)
[![rus](https://img.shields.io/badge/lang-ru-ru?color=DCDCDC)](https://github.com/allcodny/URL-to-pdf-telebot/blob/main/README-ru.md)

## About the bot
A simple Telegram bot for converting **multiple** web pages to PDF format. The user can choose to download the file in standard size or optimized for mobile devices.

## ✨ How the bot works:
1. The user sends text containing several links (as plain text or hyperlinks)
2. The bot converts each link to PDF in order and saves everything into a single archive
3. A zip archive containing all PDF files is sent to the user (If there is only one link, the PDF file is sent directly)

## ⚙️ Installation and Setup

**Note:** It is recommended to run the bot on a hosting service or server, as any Telegram bot requires constantly running code for continuous operation.

1. Prerequisites
   - Python 3.8+
   - Your Telegram bot token ([Where to get it](https://t.me/BotFather))
   - Installed [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)
  
2. Cloning the repository
   <br>`git clone https://github.com/allcodny/URL-to-pdf-telebot`
   <br>*or*
   <br>download as a ZIP file and extract it

3. Installing dependencies
   <br>In the command line: `pip install -r requirements.txt`

4. Create a `.env` file based on the `.env.example` file

5. Start the bot
   <br>`python bot.py`

#### If you liked the project, don't forget to give it a ⭐ on GitHub!
