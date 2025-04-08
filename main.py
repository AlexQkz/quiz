import asyncio
import random
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputMediaPhoto
from aiogram import F


API_TOKEN = '7763720709:AAEDyS9BhH4sHRHpRNuF5RRKIodjtf5TtSU'  # Replace with your bot token

bot = Bot(token=API_TOKEN)  # Create Bot instance
dp = Dispatcher()  # Create Dispatcher instance

# --- Game Data ---
players = set()
scores = {}
current_question = {}
question_index = 0
questions = []
GAME_STARTED = False

# --- Load Questions from JSON ---
def load_questions():
    global questions
    with open('meme_questions.json', 'r') as f:
        questions = json.load(f)

# --- Commands ---
@dp.message(F.command('startgame'))
async def start_game(message: types.Message):
    global players, scores, GAME_STARTED, question_index
    if GAME_STARTED:
        await message.reply("بازی در حال اجراست!")
        return
    players = set()
    scores = {}
    question_index = 0
    GAME_STARTED = True
    load_questions()
    await message.answer("🎮 بازی Meme Quiz شروع شد! بازیکنان دستور /join رو بزنن برای ورود.")

@dp.message(F.command('join'))
async def join_game(message: types.Message):
    if not GAME_STARTED:
        await message.reply("بازی هنوز شروع نشده. اول /startgame رو بزن.")
        return
    user = message.from_user
    if user.id not in players:
        players.add(user.id)
        scores[user.id] = 0
        await message.answer(f"{user.full_name} به بازی پیوست ✅")
    else:
        await message.answer("شما قبلاً عضو بازی شدین!")

@dp.message(F.command('next'))
async def next_question(message: types.Message):
    global current_question, question_index
    if not GAME_STARTED:
        await message.reply("بازی فعال نیست.")
        return
    if question_index >= len(questions):
        await message.answer("✅ همه سوالات تموم شدن.")
        return
    q = questions[question_index]
    current_question = q
    question_index += 1

    options = q['options']
    random.shuffle(options)

    keyboard = types.InlineKeyboardMarkup()
    for option in options:
        keyboard.add(types.InlineKeyboardButton(option, callback_data=option))

    await bot.send_photo(chat_id=message.chat.id, photo=q['image_url'], caption=f"❓ این میم رو می‌شناسی؟", reply_markup=keyboard)

    await asyncio.sleep(15)  # wait for 15 seconds for answers
    await remove_low_scores(message.chat.id)

async def remove_low_scores(chat_id):
    if not scores:
        return
    min_score = min(scores.values())
    to_remove = [uid for uid, score in scores.items() if score == min_score]
    for uid in to_remove:
        players.discard(uid)
        del scores[uid]
    if len(players) <= 1:
        winner_id = list(players)[0] if players else None
        if winner_id:
            winner = await bot.get_chat_member(chat_id, winner_id)
            await bot.send_message(chat_id, f"🏆 برنده نهایی: {winner.user.full_name}!")
        else:
            await bot.send_message(chat_id, "هیچ برنده‌ای وجود ندارد.")
        global GAME_STARTED
        GAME_STARTED = False

# --- Callback to receive answers ---
@dp.callback_query(F.data)
async def answer_callback(call: types.CallbackQuery):
    if not GAME_STARTED or not current_question:
        return
    user_id = call.from_user.id
    if user_id not in players:
        await call.answer("شما در بازی نیستید.")
        return
    selected = call.data
    correct = current_question['answer']
    if selected == correct:
        scores[user_id] += 1
        await call.answer("✅ درست بود!")
    else:
        await call.answer("❌ اشتباه بود!")

@dp.message(F.command('score'))
async def show_score(message: types.Message):
    if not scores:
        await message.reply("هنوز امتیازی ثبت نشده.")
        return
    text = "📊 امتیازات فعلی:\\n"
    for uid, score in scores.items():
        user = await bot.get_chat_member(message.chat.id, uid)
        text += f"{user.user.full_name}: {score}\\n"
    await message.answer(text)

if __name__ == '__main__':
    # Corrected to await the start_polling coroutine
    asyncio.run(dp.start_polling(bot))
