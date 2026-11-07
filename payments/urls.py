from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('choose/<int:booking_id>/', views.choose_payment_method, name='choose_payment_method'),
    path('process/<int:booking_id>/', views.process_payment, name='process_payment'),
    path('result/<int:payment_id>/', views.payment_result, name='payment_result'),
]
