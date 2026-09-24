from django.urls import path
from . import views

app_name = 'hotels'

urlpatterns = [
    path('search/', views.search_hotels, name='search_hotels'),
    path('<int:hotel_id>/', views.hotel_detail, name='hotel_detail'),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
]