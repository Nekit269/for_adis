from django.http import HttpResponse


def index(request):
    return HttpResponse("Привет, мир! Я ебанулся, ничего нового")


def test(request):
    return HttpResponse("Зачем ты сюdа зашел, придурок?")