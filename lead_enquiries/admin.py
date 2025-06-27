from django.contrib import admin
from .models import *
# Register your models here.

class EnquiryItemInline(admin.TabularInline):
    model = EnquiryItem
    extra = 1 # 預設顯示一個空白的紀錄表單

class EnquiryTrackInline(admin.TabularInline):
    model = EnquiryTrack
    extra = 1

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    model = Enquiry
    list_display = ('bwp_no','potential_customer','status')
    inlines = [EnquiryItemInline,EnquiryTrackInline]
