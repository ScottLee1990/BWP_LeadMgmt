from django import forms
from .models import PotentialCustomer,Contacts,ContactLogs
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

# leads/forms.py

from django import forms
from .models import PotentialCustomer, Contacts, ContactLogs
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, Div


class PotentialCustomerForm(forms.ModelForm):
    class Meta:
        model = PotentialCustomer
        fields = [
            'company_name', 'country', 'website', 'phone', 'email',
            'currency', 'source', 'company_type', 'rank', 'industries',
            'required_products', 'status', 'notes'
        ]
        # 【核心修正】在這裡明確指定 industries 欄位使用 Checkbox 小工具
        # 同時也可以為 notes 指定 Textarea 的尺寸
        widgets = {
            'industries': forms.CheckboxSelectMultiple,
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(PotentialCustomerForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # form_tag = False 表示我們會在模板中手動加入 <form> 和 {% csrf_token %} 標籤
        # 這給了我們更大的彈性，例如在表單旁加上取消按鈕
        self.helper.form_tag = False

        # 【核心修正】使用 Fieldset 和完整的欄位列表來重新定義佈局
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
            # Crispy Forms 可以幫我們產生提交按鈕
            # Submit('submit', '儲存客戶資料', css_class='btn-primary mt-3')
        )



class ContactsForm(forms.ModelForm):
    class Meta:
        model = Contacts
        fields = ['name', 'position', 'phone', 'email', 'notes']

class ContactLogsForm(forms.ModelForm):
    class Meta:
        model = ContactLogs
        fields = ['contact', 'topic', 'content']

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