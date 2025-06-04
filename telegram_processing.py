from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)


class TelegramBotHandler:
    def __init__(self, bot_token, chat_id, message_list):
        self.__bot_token = bot_token
        self.__chat_id = chat_id
        self.message_list = message_list
        self.app = None

    async def start(self):
        self.app = ApplicationBuilder().token(self.__bot_token).build()

        self.app.add_handler(MessageHandler(
            filters.ALL & filters.Chat(chat_id=self.__chat_id),
            self.__handle_message
        ))

        await self.app.initialize()
        diagnostics_result = await self.__bot_diagnostics()
        if diagnostics_result:
            print(f"Error starting bot: {diagnostics_result}")
            return

        await self.app.start()
        print(f"[BOT] Listening to chat ID: {self.__chat_id}")
        await self.app.updater.start_polling()

    # async def manual_polling(self):
    #     await self.app.updater.start_polling()

    async def __handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message and update.message.text:
            print(update.message.text)
            self.message_list.append(update.message.text)

    async def __bot_diagnostics(self):
        try:
            me = await self.app.bot.get_me()
            admins = await self.app.bot.get_chat_administrators(self.__chat_id)
            if me.id not in [admin.user.id for admin in admins]:
                raise Exception("Bot is not an admin in the chat.")
        except Exception as e:
            print(f"Diagnostics error: {e}")
            return e
        return None

    async def stop(self):
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        print("[BOT] Bot stopped.")

    def get_participants(self):
        count = self.app.bot.get_chat_member_count(self.__chat_id)
        return count