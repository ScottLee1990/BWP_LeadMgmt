from . import views
from django.urls import path

app_name = 'leads'

urlpatterns = [
    path('detail/<int:pk>/toggle_pin/', views.toggle_pin, name='toggle_pin'),
    path('', views.potential_customer_list, name='potential_customer_list'),
    path('create/', views.potential_customer_create, name='potential_customer_create'),
    path('delete/<int:pk>/', views.potential_customer_delete, name='potential_customer_delete'),
    path('detail/<int:pk>/',views.potential_customer_detail,name='potential_customer_detail'),
    path('detail/<int:pk>/update/', views.potential_customer_update, name='potential_customer_update'),
    path('detail/<int:pk>/contacts/add/', views.contact_create, name='contact_create'),
    path('detail/<int:pk>/logs/add/', views.contact_log_create, name='contact_log_create'),
    path('logs/update/<int:pk>/', views.contact_log_update, name='contact_log_update'),
    path('logs/delete/<int:pk>/', views.contact_log_delete, name='contact_log_delete'),
    path('contacts/update/<int:pk>/', views.contact_update, name='contact_update'),
    path('contacts/delete/<int:pk>/', views.contact_delete, name='contact_delete'),
    path('leads/export_csv/', views.export_customers_csv, name='export_customers_csv'),
]