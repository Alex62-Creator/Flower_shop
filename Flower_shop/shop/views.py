from django.shortcuts import render, redirect
from Flower_shop.catalog.models import Category

# Create your views here.
#Создаем функцию главной страницы
def index(request):
    categories = Category.objects.all()
    return render(request, 'shop/index.html', {'categories': categories})
