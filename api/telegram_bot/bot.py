import os
from os import getenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text

os.environ["PATH"] += os.pathsep + path
bot = Bot(token=getenv('TOKEN'))
dp = Dispatcher(bot)

 # LentaParser


@dp.message_handler(commands='start')
async def start(message: types.Message):
    start_buttons = ['Chelyabinsk']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)
    await message.answer('Please select a City', reply_markup=keyboard)


@dp.message_handler(Text(equals='Chelyabinsk'))
async def ekb_city(message: types.Message):
    retail_buttons = ['Lenta']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*retail_buttons)
    await message.answer('Please select retail', reply_markup=keyboard)
    # chat_id = message.chat.id
    # await send_data(city_code='85', chat_id=chat_id)


# async def send_data(city_code='', chat_id=''):
#     # file = await collect_data(city_code=city_code)
#     await message.answer('Please select a City', reply_markup=keyboard)
#     # await bot.send_document(chat_id=chat_id, document=open(file, 'rb'))
#     # await os.remove(file)



if __name__ == '__main__':
    executor.start_polling(dp)
