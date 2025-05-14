from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

# Указываем пути к страницам приложения
urlpatterns = ([
	path('', views.index, name='shop_home'),
	#path('create', views.create_film, name='add_film'),
]	+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
	+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))