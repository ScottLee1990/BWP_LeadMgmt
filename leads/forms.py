# leads/forms.py
# Crispy_forms用法還沒有很熟 如果之後還常做MTV架構的全端網站，需要多練習

from django import forms
from .models import PotentialCustomer, Contacts, ContactLogs
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, Div

# 潛在客戶區塊
class PotentialCustomerForm(forms.ModelForm):
    class Meta:
        model = PotentialCustomer
        fields = [
            'company_name', 'country', 'website', 'phone', 'email',
            'currency', 'source', 'company_type', 'rank', 'industries',
            'required_products', 'status', 'notes'
        ]
        widgets = {
            'industries': forms.CheckboxSelectMultiple,
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    # 這邊的覆寫是for Crispy form
    def __init__(self, *args, **kwargs):
        super(PotentialCustomerForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # form_tag = False 可在模板中手動加入 <form> 和 {% csrf_token %} 標籤
        # 操作上有更大的彈性，例如加上取消按鈕
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '基本資料',  # Fieldset 的第一個參數是它的標題
                Row(
                    Column('company_name', css_class='form-group col-md-6 mb-3'),
                    Column('country', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('website', css_class='form-group col-md-6 mb-3'),
                    Column('phone', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('email', css_class='form-group col-md-6 mb-3'),
                    Column('currency', css_class='form-group col-md-6 mb-3'),
                )
            ),
            Fieldset(
                '分類資訊',
                Row(
                    Column('source', css_class='form-group col-md-6 mb-3'),
                    Column('company_type', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('rank', css_class='form-group col-md-6 mb-3'),
                    Column('status', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('required_products', css_class='form-group col-md-6 mb-3'),
                    # 對於 Checkbox，我們給它整個 row 的寬度以獲得更好的排版
                    Column('industries', css_class='form-group col-md-12 mb-3'),
                )
            ),
            Fieldset(
                '備註',
                'notes'
            ),
        )

# 聯絡人區塊
class ContactsForm(forms.ModelForm):
    class Meta:
        model = Contacts
        fields = ['name', 'position', 'phone', 'email', 'notes']

# 聯絡紀錄區塊
class ContactLogsForm(forms.ModelForm):
    class Meta:
        model = ContactLogs
        fields = ['contact', 'topic', 'content']

    # 這邊的覆寫是for Crispy form
    def __init__(self, *args, **kwargs):
        # 記得從view丟出potential_customer參數
        potential_customer = kwargs.pop('potential_customer', None)
        super().__init__(*args, **kwargs)
        # 這邊建立了一個下拉選單,讓user直接選擇contact
        self.fields['contact'].widget.attrs.update({'class': 'form-select'})
        if potential_customer:
            self.fields['contact'].queryset = Contacts.objects.filter(potential_customer=potential_customer)
        else:
            self.fields['contact'].queryset = Contacts.objects.none()