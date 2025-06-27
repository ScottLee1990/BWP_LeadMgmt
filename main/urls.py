# main/urls.py

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # 將根路徑指向 dashboard 視圖
    path('', views.dashboard, name='main'),
]