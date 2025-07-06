# lead_enquiries/forms.py
from django import forms
from .models import Enquiry, EnquiryItem, EnquiryTrack, EnquiryAttachment
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset



# 報價單主頁 - Crispy Forms
class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = [
            'bwp_no',
            'potential_customer',
            'enquiry_no',
            'status',
        ]

    # 用 Crispy Forms的準備
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # form_tag = False 這樣可以在模板中自己控制 <form> 標籤和按鈕
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Fieldset(
                '報價單主要資訊',
                Row(
                    Column('bwp_no', css_class='form-group col-md-6 mb-3'),
                    # potential_customer 欄位會自動渲染成一個下拉選單
                    Column('potential_customer', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('enquiry_no', css_class='form-group col-md-6 mb-3'),
                    Column('status', css_class='form-group col-md-6 mb-3'),
                )
            )
        )
        self.fields['potential_customer'].widget.attrs.update({'class': 'form-select'})
        # 如果表單在初始化時有客戶資料，就把它設為唯讀
        if 'initial' in kwargs and 'potential_customer' in kwargs['initial']:
            self.fields['potential_customer'].disabled = True


# 報價單品項 - AJAX Modal
class EnquiryItemForm(forms.ModelForm):
    class Meta:
        model = EnquiryItem

        exclude = ('enquiry',) # 必定連結到報價，這邊可排除掉
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),  # 格式化
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 為所有欄位自動加上 bootstrap class，以便在 modal 中渲染
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})



# 追蹤紀錄表單 - AJAX Modal
class EnquiryTrackForm(forms.ModelForm):
    class Meta:
        model = EnquiryTrack
        fields = ['content'] # 其他的都會自動建立
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': '請輸入追蹤內容...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'form-control'})

# 上傳檔案
class EnquiryAttachmentForm(forms.ModelForm):
    class Meta:
        model = EnquiryAttachment
        fields = ['file', 'description']