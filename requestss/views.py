from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
# Create your views here.
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.decorators import parser_classes
from rest_framework.response import Response

from random import randint
import datetime
import json


def home(request):
    return HttpResponse("Home Page!")


def pprint(request):
    print("THIS")
    print(request.POST.get('message'))
    return HttpResponse("priiint!")


pprint.csrf_exempt = True


def get_film(collection, attrs):
    year = None
    genres = []
    for attr in attrs:
        if attr.isnumeric():
            year = attr
        else:
            genres.append(attr)
    request = {'$and': []}
    if year is not None:
        request['$and'].append({'Year': year})
    for genre in genres:
        request['$and'].append({'Genres': genre})

    cursor = collection.find(request)
    result = list(cursor)

    need_index = randint(0, len(result) - 1)
    return result[need_index]


def get_illnes(collection, attrs):
    attrs = attrs.split('.')
    request = {'$and': []}
    for attr in attrs:
        request['$and'].append({'Simptoms': attr.strip()})

    cursor = collection.find(request)
    if cursor.count() == 0:
        cursor = collection.find({'Simptoms': '-'})

    result = list(cursor)
    need_index = randint(0, len(result) - 1)
    return result[need_index]


def set_notice(db, user, notice):
    if len(notice) < 3:
        return False
    try:
        date = [int(i) for i in notice[0].split('.')]
        time = [int(i) for i in notice[1].split(':')]
    except:
        return False
    message = " ".join(notice[2:])
    datime = datetime.datetime(date[2], date[1], date[0], time[0], time[1], 0, 0)
    db.insert_one({"User": user, "Datetime": datime, "Text": message})
    return True


def check_for_spec_text(user, text):
    text_sep = text.lower().split(" ")
    db = settings.DATABASES['mongo']['db'].sounds
    if 'фильм' in text_sep[:2]:
        film = None
        if text_sep[0] == 'случайный':
            film = db.movies.aggregate([{'$sample':{'size':1}}])
            film = film.next()
        else:
            film = get_film(db.movies, text_sep[1:])
        if film is None:
            return "Неправильный формат запроса"
        out_str = film['Name'] + "\n" + film['Year'] + "\n"
        for genre in film['Genres']:
            out_str += genre + ", "
        out_str += "\n"
        for director in film['Directors']:
            out_str += director + ", "
        out_str += "\n" + film['Description']
        return out_str
    elif text_sep[0] == 'книга':
        book = db.books.aggregate([{'$sample':{'size':1}}])
        book = book.next()
        out_str = book['Name'] + "\n" + book['Writer'] + "\n" + book['Description']
        return out_str
    elif text_sep[0] == 'цитата':
        sound = db.quotes_n.aggregate([{'$sample': {'size': 1}}])
        sound = sound.next()
        out_str = sound['Text']
        return out_str
    elif text_sep[0] == 'мем':
        user = db.users.find({'user': user})
        if user.count() == 0:
            return "Ошибка проверки пользователя"
        user.next()
        user_id = user['id']

        cursor = db.mems.find({ "ID_forbid": {"$ne" : user_id} })

        result = list(cursor)
        need_index = randint(0, len(result) - 1)
        mem = reult[need_index]
        db.last_mem.remove({'user':user})
        db.last_mem.insert_one({'user': user, 'mem': mem['mem']})

        return mem['mem']
    elif text_sep[:2] == ['запретить', 'мем']:
        mem = db.last_mem.find({'user': user})
        if mem.count() == 0:
            return "Неизвестно какой мем запретить"
        mem = mem.next()
        mem_text = mem['mem']

        user = db.users.find({'user': user})
        if user.count() == 0:
            return "Ошибка проверки пользователя"
        user.next()
        user_id = user['id']

        mem_forbid = db.mems.find({'mem': mem_text})
        if mem_forbid.count() == 0:
            return "Не найден последний мем в базе данных"
        mem_forbid = mem_forbid.next()
        list_forbid = mem_forbid['ID_forbid']
        list_forbid.append(user_id)
        db.mems.update({'mem': mem_text}, {"$set": { "ID_forbid": list_forbid }})
        return "Последний мем запрещен"

    elif text_sep[0] == 'гороскоп':
        if len(text_sep) < 3:
            return "Неправильный формат запроса"
        horoscope = db.horoscopes.find({"Sign": text_sep[1].lower()})
        horo = horoscope.next()
        out_str = horo['Today'] if 'сегодня' in text_sep[2:] else horo['Tomorrow']
        return out_str
    elif text_sep[0] == 'напоминание':
        res = set_notice(db.notes, user, text_sep[1:])
        if res:
            return "Напоминание сохранено"
        else:
            return "Неправильный формат запроса"
    elif text_sep[0] == 'диагностика':
        if len(text_sep) < 2:
            return "Неправильный формат запроса"
        illnes = get_illnes(db.diagnost, " ".join(text_sep[1:]))

        phrases = ['У тебя {})','Очень смахивает на заболевание {}', 'Подозрительно похоже на болезнь {}', 'Неожиданно и неприятно, но возможно это {}', 'Поздравляю, у тебя {}, сходи уже к врачу', 'Полагаю, это {}, береги себя и своих близких']
        phrase_ind = randint(0, 5)
        out_str = phrases[phrase_ind].format(illnes['name'])
        return out_str
    elif text_sep[0] in ['помощь', 'help']:
	    out_str = "Набор спец команд:\n"
	    out_str += "случайный фильм\n" + "фильм <жанр> <год>\n"
	    out_str += "книга\n" + "цитата\n" + "мем\n" + "гороскоп <знак> <сегодня/завтра>\n"
	    out_str += "напоминание 25.05.2020 15:10 текст\n"
	    out_str += "диагностика <симптом>\n"
	    return out_str
    else:
        return None


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def message(request, format=None):
    # получение данных запроса в виде json
    data = request.data
    text = data['message']
    user = data['user']
    answer = check_for_spec_text(user, text)
    if answer is not None:
        return Response(answer)
    norm_text = settings.NORMALIZER.normalize_text(text)
    print(text)
    num = randint(1,3)
    answer = ' '.join(settings.PREDICTOR.predict(norm_text, num))
    print(answer)
    return Response(answer)
    # return JsonResponse({'message': 'test'})


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def login(request, format=None):
    data = request.data
    try:
        login = data['login']
        password = data['password']
    except:
        print("ERROR: в запросе нет нужных данных")
        return HttpResponse(status=400)

    try:
        db_users = settings.DATABASES['mongo']['db'].sounds.users
    except:
        print("ERROR: не удалось подключиться к базе данных")
        return HttpResponse(status=500)

    if db_users.count({'$and': [{'login': login}, {'password': password}]}) > 0:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=404)


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def registration(request, format=None):
    # регистрация нового пользователя
    data = request.data
    try:
        login = data['login']
        password = data['password']
    except:
        print("ERROR: в запросе нет нужных данных")
        return HttpResponse(status=400)

    try:
        db_users = settings.DATABASES['mongo']['db'].sounds.users
        db_history = settings.DATABASES['mongo']['db'].sounds.history
    except:
        print("ERROR: не удалось подключиться к базе данных")
        return HttpResponse(status=500)

    if db_users.count({'login': login}) > 0:
        return HttpResponse(status=401)
    #добавление в бд
    db_users.insert_one({'login': login, 'password': password})
    db_history.insert_one({'login': login, 'messages': []})

    return HttpResponse(status=200)

@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def save_history(request, format=None):
    # регистрация нового пользователя
    data = request.data
    try:
        user = data['user']
        users = data['users']
        messages = data['messages']
        times = data['times']
    except:
        print("ERROR: в запросе нет нужных данных")
        return HttpResponse(status=400)

    try:
        db_history = settings.DATABASES['mongo']['db'].sounds.history
    except:
        print("ERROR: не удалось подключиться к базе данных")
        return HttpResponse(status=500)
    db_history.remove({'user': user})
    db_history.insert_one({'user': user, 'users': users, 'messages': messages, 'times':times})

    return HttpResponse(status=200)


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def load_history(request, format=None):

    data = request.data
    try:
        user = data['user']
    except:
        print("ERROR: в запросе нет нужных данных")
        return HttpResponse(status=400)

    try:
        db_history = settings.DATABASES['mongo']['db'].sounds.history
    except:
        print("ERROR: не удалось подключиться к базе данных")
        return HttpResponse(status=500)

    if db_history.count({'user': user}) == 0:
        return HttpResponse(status=401)

    cursor = db_history.find({'user': user})
    data = cursor.next()

    out_dict = {'users': data['users'], 'messages': data['messages'], 'times': data['times']}
    json_out = json.dumps(out_dict)

    return HttpResponse(json_out)
