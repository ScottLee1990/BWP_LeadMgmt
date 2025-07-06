# lead_enquiries/urls.py

from . import views
from django.urls import path

app_name = 'lead_enquiries'

urlpatterns = [
    # 報價單 CRUD
    path('', views.enquiry_list, name='enquiry_list'),
    path('create/', views.enquiry_create, name='enquiry_create'),
    path('detail/<int:pk>/', views.enquiry_detail, name='enquiry_detail'),
    path('detail/<int:pk>/update/', views.enquiry_update, name='enquiry_update'),
    path('delete/<int:pk>/', views.enquiry_delete, name='enquiry_delete'),
    # 報價單品項 - AJAX
    path('detail/<int:enquiry_pk>/items/add/', views.enquiry_item_create, name='enquiry_item_create'),
    path('items/update/<int:pk>/', views.enquiry_item_update, name='enquiry_item_update'),
    path('items/delete/<int:pk>/', views.enquiry_item_delete, name='enquiry_item_delete'),
    # 報價單追蹤 - AJAX
    path('detail/<int:enquiry_pk>/tracks/add/', views.enquiry_track_create, name='enquiry_track_create'),
    path('tracks/update/<int:pk>/', views.enquiry_track_update, name='enquiry_track_update'),
    path('tracks/delete/<int:pk>/', views.enquiry_track_delete, name='enquiry_track_delete'),
    # 重點追蹤功能
    path('detail/<int:pk>/toggle_pin/', views.toggle_enquiry_pin, name='toggle_enquiry_pin'),
    # 匯出 CSV
    path('export_csv/', views.export_enquiries_csv, name='export_enquiries_csv'),
    path('detail/<int:enquiry_pk>/attachments/upload/', views.enquiry_attachment_upload,
         name='enquiry_attachment_upload'),
    path('attachments/delete/<int:pk>/', views.enquiry_attachment_delete, name='enquiry_attachment_delete'),
]