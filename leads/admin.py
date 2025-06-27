from django.contrib import admin

# Register your models here.
from .models import PotentialCustomer,Contacts,ContactLogs

# 定義 Contact 的 Inline 表單
class ContactsInline(admin.TabularInline): # 或 admin.StackedInline
    model = Contacts
    extra = 1 # 預設顯示一個空白的聯絡人表單

# 定義 CommunicationLog 的 Inline 表單
class ContactLogsInline(admin.TabularInline):
    model = ContactLogs
    extra = 1 # 預設顯示一個空白的紀錄表單
    readonly_fields = ('created_by', 'created_at') # 這些欄位通常是唯讀的
    # 自動填入creater
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "created_by":
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PotentialCustomer)
class PotentialCustomerAdmin(admin.ModelAdmin):
    list_display = ('potential_customer_id','company_name','country','website','sales_incharge','status')
    search_fields = ('company_name','country','website')

    inlines=[
        ContactsInline,
        ContactLogsInline
    ]






