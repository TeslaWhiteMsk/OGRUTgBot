import telebot
import config
import random
import requests
import sys
import pymongo
import re
from textwrap import wrap

bot=telebot.TeleBot(config.token)

globalvar={'chatid':
    {
        'currentgameid': 0
    }
}

client=pymongo.MongoClient("mongodb://127.0.0.1:27017/?compressors=disabled&gssapiServiceName=mongodb")
db=client.ogru_data
coll=db.games


count=len(list(coll.find()))


def return_base_keyboard():
        keyboard=telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Найти игру","Случайная игра")
        keyboard.row("Список комманд")
        return keyboard
def return_context_keyboard():
        keyboard=telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row("Посмотреть обзор","Ссылка на игру")
        keyboard.row("Найти игру","Случайная игра")
        keyboard.row("Список комманд")
        return keyboard

def send_link_in_chat(game_id,message):
    page=coll.find_one({"gameid":game_id})
    name=page["name"]
    gamelink=page["link"]
    global globalvar
    globalvar.update({message.chat.id:{'currentgameid':game_id}})
    keyboard=return_context_keyboard()
    print(f"Токен: {message.chat.id} Запрошена ссылка на игру:{name}")
    bot.send_message(message.chat.id,f"{gamelink}".format(message.from_user,bot.get_me()),parse_mode='html',reply_markup=keyboard)


def send_game_in_chat(game_id,message):
        page=coll.find_one({"gameid":game_id})
        name=page['name']
        image_src=page['coverlink']
        image=requests.get("http://"+image_src)
        genre=page['genre']
        developer=page['developer']
        publisher=page['publisher']
        year=page['year']
        platform=page['platform']
        rating=page['rating']
        tags=page['tags']
        global globalvar
        globalvar.update({message.chat.id:{'currentgameid':game_id}})
        try:
            bot.send_photo(message.chat.id,image.content)
        except Exception as e:
            pass
        keyboard=return_context_keyboard()
        print(f"Токен: {message.chat.id} Запрошена игра:{name}")
        bot.send_message(message.chat.id,f"<b>{name}</b>\nЖанр:{genre}\nРазработчик:{developer}\nИздатель:{publisher}\nГод:{year}\nПлатформа:{platform}\nРейтинг:{rating}\nТеги:{tags}".format(message.from_user,bot.get_me()),parse_mode='html',reply_markup=keyboard)

def send_review_in_chat(game_id,message):
    game=coll.find_one({"gameid":game_id})
    review=game['review']
    name=game['name']
    review_wrap=wrap(review,width=4000)
    review_fragment=''
    for line in review_wrap:
        point = max(line.rfind(". "), line.rfind("! "), line.rfind("? "))
        if point== -1:
            review_fragment+=line
        else:
            newLine = "{}{}\n".format(review_fragment, line[0:point+1])
            bot.send_message(message.chat.id,f"{newLine}".format(message.from_user,bot.get_me()),parse_mode='html')
            review_fragment=line[point+2:] + " "
    global globalvar
    globalvar.update({message.chat.id:{'currentgameid':game_id}})
    keyboard=return_context_keyboard()
    print(f"Токен: {message.chat.id} Запрошен обзор игры:{name}")
    bot.send_message(message.chat.id,f"{review_fragment}".format(message.from_user,bot.get_me()),parse_mode='html',reply_markup=keyboard)

def search_game_intro(message):
    bot.send_message(message.chat.id,"Введите название игры:".format(message.from_user,bot.get_me() ) ,parse_mode='html' )

def search_game_ids(message):
    pages=coll.find({'$text':{'$search':message.text}})
    ids=[]
    for page in pages:
        ids.append(page["gameid"])
    print(f"Токен: {message.chat.id} Поисковый запрос:{message.text} Найдено игр:{len(ids)}")
    return ids

def print_ids_list(message,ids,mode=0):
    string_for_bsm=f"Найдено игр:{len(ids)},\n "
    for id in ids:
        gamedata=coll.find_one({"gameid" : id})
        name=gamedata['name']
        rating=gamedata['rating']
        if mode==1:
            string_for_bsm+=f"<b>{id}</b> : {name} Рейтинг:{rating}, \n "
        else:
            string_for_bsm+=f"<b>{id}</b> : {name}, \n "
    string_for_bsm+="Введите номер нужной игры чтобы открыть её карточку."
    str_bsm_wrap=wrap(string_for_bsm,width=4000)
    str_bsm_fragment=''
    for line in str_bsm_wrap:
        point=max(line.rfind(", "), line.rfind("! "), line.rfind("? "))
        if point== -1:
            str_bsm_fragment+=line
            str_bsm_fragment.replace(",","\n")
        else:
           newLine="{}{}\n".format(str_bsm_fragment,line[0:point+1]).replace(",","\n")
           bot.send_message(message.chat.id,f"{newLine}".format(message.from_user,bot.get_me()),parse_mode='html')
           str_bsm_fragment=line[point+2:]+" "
           str_bsm_fragment.replace(",","\n")
    bot.send_message(message.chat.id,f"{str_bsm_fragment}".format(message.from_user,bot.get_me()),parse_mode='html')

def top_20_games_year_ids(message):
    year=re.findall(r'\d+',message.text)[0]
    pages=coll.find({"year":year}).sort([("rating",pymongo.DESCENDING)]).limit(20)
    ids=[]
    for page in pages:
        ids.append(page["gameid"])
    print(f"Токен: {message.chat.id} Поисковый запрос:{message.text} Найдено игр:{len(ids)}")
    return ids

def print_commands_list(message,mode=0):
    if mode==1:
        keyboard=return_base_keyboard()
    else:
        keyboard=return_context_keyboard()
    bot.send_message(message.chat.id, "<b>Список комманд бота:</b>\n<b>Случайная игра</b>- вывести карточку случайной игры.\n <b>Посмотреть обзор</b>-показать текстовый  обзор игры.\n <b>Ссылка на игру</b>-ссылка на игру на сайте Old-Games.ru\n<b>Топ (номер года)</b>- топ 20 игр указанного года по рейтингу сайта Old-Games.ru".format(message.from_user,bot.get_me()),parse_mode='html',reply_markup=keyboard)



@bot.message_handler(commands=['start'])
def welcome(message):
    globalvar.update({message.chat.id:{'currentgameid':0}})
    keyboard=return_base_keyboard()
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, ,бот для поиска игр по базе сайта <a href=old-GAMES.RU>Old-Games.ru</a>\nЧтобы вывести полный список комманд бота нажмите кнопку <b> Список комманд</b> .".format(message.from_user,bot.get_me()),parse_mode='html',reply_markup=keyboard)

@bot.message_handler(content_types=['text'])
def lalala (message):
    if message.text=="Посмотреть обзор":
        try:
            currentgameid=globalvar[message.chat.id]['currentgameid']
        except:
            currentgameid=0
        send_review_in_chat(currentgameid,message)
    elif message.text=="Список комманд":
        try:
            currentgameid=globalvar[message.chat.id]['currentgameid']
        except:
            currentgameid=0
        if currentgameid==0:
            print_commands_list(message,1)
        else:
            print_commands_list(message)
    elif message.text=="Ссылка на игру":
        try:
            currentgameid=globalvar[message.chat.id]['currentgameid']
        except:
            currentgameid=0
        send_link_in_chat(currentgameid,message)
    elif message.text=="Найти игру":
        search_game_intro(message)
    elif re.fullmatch("Топ \d\d\d\d",message.text):
        id_s=top_20_games_year_ids(message)
        print_ids_list(message,id_s,1)
    elif message.text=="Случайная игра":
        random.seed()
        game_id=random.randint(0,count-1)
        send_game_in_chat(game_id,message)
    elif message.text.isdigit():
        try:
            int(message.text)
        except:
            bot.send_message(message.chat.id,"Некорректный id игры, пожалуйста, вводите только целые положительные числа")
        else:
            if int(message.text)>=0& int(message.text)<count-1:
                send_game_in_chat(int(message.text),message)
            else:
                bot.send_message(message.chat.id,f"Некорректный id игры, пожалуйста, введите число от 0 до {len(games_base)}")

    else:
        id_s=search_game_ids(message)
        print_ids_list(message,id_s)


while True:
    try:
        bot.polling(none_stop=True)
    except Exception:
        time.sleep(3)
        print (e)


