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


# def get_film(collection, attrs=[]):
# #     if attrs == []:
# #         return collection.aggregate([{'$sample':{'size':1}}])
# #     else:
# #         attr = attrs.pop(0)
# #         print(attr)
# #         if attr.isnumeric():
# #             print(0)
# #             print(collection.count())
# #             print(collection.find({"Year": attr}).count())
# #             if collection.count({"Year": attr}) > 0:
# #                 print(0,0)
# #                 return get_film(collection.find({"Year": attr}), attrs)
# #         else:
# #             attr = attr.capitalize()
# #             print(1)
# #             if collection.count({"Genres": attr}) > 0:
# #                 print(1,0)
# #                 return get_film(collection.find({"Genres": attr}), attrs)
# #         return None


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
    if 'фильм' in text_sep[:1]:
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
        mem = db.mems.aggregate([{'$sample':{'size':1}}])
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
        out_str = "У тебя " + illnes['Name'] + ")"
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
    print(data['users'])
    print(data['messages'])
    print(data['times'])
    out_dict = {'users': data['users'], 'messages': data['messages'], 'times': data['times']}
    json_out = json.dumps(out_dict)
    # out_str =  "#".join(data['users']) + ";"
    # out_str += "#".join(data['messages']) + ";"
    # out_str += "#".join([str(i) for i in data['times']])

    return HttpResponse(json_out)
