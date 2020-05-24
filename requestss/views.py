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


def home(request):
    return HttpResponse("Home Page!")


def pprint(request):
    print("THIS")
    print(request.POST.get('message'))
    return HttpResponse("priiint!")


pprint.csrf_exempt = True


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def message(request, format=None):
    # получение данных запроса в виде json
    data = request.data
    text = data['message']
    norm_text = settings.NORMALIZER.normalize_text(text)
    print(text)
    answer = ' '.join(settings.PREDICTOR.predict(norm_text, 1))
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
