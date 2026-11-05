from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('write/<int:booking_id>/', views.write_review, name='write_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('mine/', views.my_reviews, name='my_reviews'),
    path('<str:item_type>/<int:item_id>/', views.item_reviews, name='item_reviews'),
]