# lead_enquiries/views.py

import csv

from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Sum, F, ExpressionWrapper, FloatField
# Q,F,ExpressionWrapper使用場合還要再多練習
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import escape_uri_path

from leads.models import PotentialCustomer
from .forms import EnquiryForm,EnquiryItemForm,EnquiryTrackForm,EnquiryAttachmentForm
from .models import Enquiry, EnquiryItem, EnquiryTrack, STATUS_CHOICES, EnquiryAttachment
from django.contrib.auth.models import User


# 輔助函式

# 處理報價單 (Enquiry) 的查詢、過濾和排序邏輯。
def _get_filtered_enquiries_queryset(request):

    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    owner_filter = request.GET.get('owner', '')
    sort_field = request.GET.get('sort', 'created_at')
    sort_order = request.GET.get('order', 'desc')
    enquiries = Enquiry.objects.select_related('potential_customer', 'created_by').all()
    # 篩選區, Q 用來做多條件判斷
    if query:
        enquiries = enquiries.filter(
            Q(bwp_no__icontains=query) |
            Q(potential_customer__company_name__icontains=query) |
            Q(enquiry_no__icontains=query) |
            Q(items__item_name__icontains=query)
        ).distinct()
    if status_filter:
        enquiries = enquiries.filter(status=status_filter)
    if owner_filter:
        enquiries = enquiries.filter(created_by__username=owner_filter)

    valid_sort_fields = {'bwp_no', 'potential_customer__company_name', 'status', 'created_at',
                         'annotated_total_amount_ntd'}

    sort_by = sort_field if sort_field in valid_sort_fields else 'created_at'

    if 'annotated_total_amount_ntd' in sort_by:
        enquiries = enquiries.annotate(
            annotated_total_amount_ntd=ExpressionWrapper(
                Sum(F('items__quantity') * F('items__unit_price') * F('items__exchange_rate')),
                output_field=FloatField()
            )
        )

    if sort_order == 'desc':
        sort_by = '-' + sort_by

    return enquiries.order_by(sort_by)



# 報價單
@login_required
def enquiry_list(request):
    enquiries_qs = _get_filtered_enquiries_queryset(request)

    # F 從資料庫層級、跨模型去抓關聯的items的Attr
    # 不需要把物件都讀取出來，執行大量運算時效率佳
    enquiries_with_total = enquiries_qs.annotate(
        annotated_total_amount_ntd=ExpressionWrapper(
            Sum(F('items__quantity') * F('items__unit_price') * F('items__exchange_rate')),
            output_field=FloatField()
        )
    )

    owners = User.objects.filter(enquiry__in=Enquiry.objects.all()).distinct()
    paginator = Paginator(enquiries_with_total, 20)
    page = request.GET.get('page')

    try:
        enquiries_page = paginator.page(page)
    except PageNotAnInteger:
        enquiries_page = paginator.page(1)
    except EmptyPage:
        enquiries_page = paginator.page(paginator.num_pages)

    status_choices = STATUS_CHOICES

    context = {
        'enquiries': enquiries_page,
        'query': request.GET.get('q', ''),
        'status_filter': request.GET.get('status', ''),
        'owner_filter': request.GET.get('owner', ''),
        'owners': owners,
        'sort_field': request.GET.get('sort', 'created_at'),
        'sort_order': request.GET.get('order', 'desc'),
        'status_choices': status_choices,
    }
    return render(request, 'lead_enquiries/enquiry_list.html', context)

# 報價詳細頁
@login_required
def enquiry_detail(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)
    context = {'enquiry': enquiry}
    return render(request, 'lead_enquiries/enquiry_detail.html', context)

# 建立報價
@login_required
def enquiry_create(request):
    initial_data = {}
    customer_id = request.GET.get('customer_id')
    # 建立報價可從 潛在客戶的表單執行 也可從Enquiry區塊執行 若從客戶表單執行會自動代入，否則要選取一個有效客戶
    if customer_id:
        try:
            customer = PotentialCustomer.objects.get(pk=customer_id)
            initial_data['potential_customer'] = customer
        except PotentialCustomer.DoesNotExist:
            pass

    if request.method == 'POST':
        form = EnquiryForm(request.POST, initial=initial_data)
        if form.is_valid():
            enquiry = form.save(commit=False)
            enquiry.created_by = request.user
            if 'potential_customer' in initial_data:
                enquiry.potential_customer = initial_data['potential_customer']

            enquiry.save()

            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(enquiry).id,
                object_id=enquiry.pk,
                object_repr=str(enquiry),
                action_flag=ADDITION,
                change_message="建立報價單"
            )
            return redirect('lead_enquiries:enquiry_detail', pk=enquiry.pk)
    else:
        form = EnquiryForm(initial=initial_data)

    return render(request, 'lead_enquiries/enquiry_form.html', {'form': form})

# 修改報價
@login_required
def enquiry_update(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)
    if request.method == 'POST':
        form = EnquiryForm(request.POST, instance=enquiry)
        if form.is_valid():
            updated_enquiry = form.save()
            LogEntry.objects.log_action(user_id=request.user.id,
                                        content_type_id=ContentType.objects.get_for_model(updated_enquiry).id,
                                        object_id=updated_enquiry.pk, object_repr=str(updated_enquiry),
                                        action_flag=CHANGE, change_message="編輯報價單資料")
            return redirect('lead_enquiries:enquiry_detail', pk=enquiry.pk)
    else:
        form = EnquiryForm(instance=enquiry)
    return render(request, 'lead_enquiries/enquiry_form.html', {'form': form})

# 刪除報價 - AJAX Modals
@login_required
def enquiry_delete(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)
    if request.method == 'POST':
        enquiry_repr = str(enquiry)
        enquiry.delete()
        LogEntry.objects.log_action(user_id=request.user.id,
                                    content_type_id=ContentType.objects.get_for_model(Enquiry).id, object_id=pk,
                                    object_repr=enquiry_repr, action_flag=DELETION, change_message="刪除報價單")
        return JsonResponse({'success': True, 'redirect_url': reverse('lead_enquiries:enquiry_list')})

    context = {'enquiry': enquiry}
    html_form = render_to_string('lead_enquiries/enquiry_delete_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})

# 加入關注
@login_required
def toggle_enquiry_pin(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)
    enquiry.is_pinned = not enquiry.is_pinned
    enquiry.save()
    change_message = "重點追蹤報價單" if enquiry.is_pinned else "取消重點追蹤報價單"
    LogEntry.objects.log_action(user_id=request.user.id, content_type_id=ContentType.objects.get_for_model(enquiry).id,
                                object_id=enquiry.pk, object_repr=str(enquiry), action_flag=CHANGE,
                                change_message=change_message)
    return redirect('lead_enquiries:enquiry_detail', pk=pk)



# 報價單品項 - AJAX Modals
@login_required
def enquiry_item_create(request, enquiry_pk):
    enquiry = get_object_or_404(Enquiry, pk=enquiry_pk)
    if request.method == 'POST':
        form = EnquiryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.enquiry = enquiry
            item.save()
            LogEntry.objects.log_action(user_id=request.user.id,
                                        content_type_id=ContentType.objects.get_for_model(item).id, object_id=item.pk,
                                        object_repr=str(item), action_flag=ADDITION,
                                        change_message=f"為報價單 {enquiry.bwp_no} 新增品項")
            return JsonResponse({'success': True})
    else:
        form = EnquiryItemForm()

    context = {'form': form, 'enquiry': enquiry,
               'form_action': reverse('lead_enquiries:enquiry_item_create', args=[enquiry_pk])}
    html_form = render_to_string('lead_enquiries/item_form_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})

# 更新報價單品項
@login_required
def enquiry_item_update(request, pk):
    item = get_object_or_404(EnquiryItem, pk=pk)
    if request.method == 'POST':
        form = EnquiryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            LogEntry.objects.log_action(user_id=request.user.id,
                                        content_type_id=ContentType.objects.get_for_model(item).id, object_id=item.pk,
                                        object_repr=str(item), action_flag=CHANGE,
                                        change_message=f"編輯報價單 {item.enquiry.bwp_no} 的品項")
            return JsonResponse({'success': True})
    else:
        form = EnquiryItemForm(instance=item)

    context = {'form': form, 'enquiry': item.enquiry,
               'form_action': reverse('lead_enquiries:enquiry_item_update', args=[pk])}
    html_form = render_to_string('lead_enquiries/item_form_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})

# 刪除報價單品項
@login_required
def enquiry_item_delete(request, pk):
    item = get_object_or_404(EnquiryItem, pk=pk)
    if request.method == 'POST':
        item_repr = str(item)
        enquiry_bwp_no = item.enquiry.bwp_no
        item.delete()
        LogEntry.objects.log_action(user_id=request.user.id,
                                    content_type_id=ContentType.objects.get_for_model(EnquiryItem).id, object_id=pk,
                                    object_repr=item_repr, action_flag=DELETION,
                                    change_message=f"刪除報價單 {enquiry_bwp_no} 的品項")
        return JsonResponse({'success': True})

    context = {'item': item}
    html_form = render_to_string('lead_enquiries/item_delete_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})



# 報價單追蹤 - AJAX Modals
@login_required
def enquiry_track_create(request, enquiry_pk):
    enquiry = get_object_or_404(Enquiry, pk=enquiry_pk)
    if request.method == 'POST':
        form = EnquiryTrackForm(request.POST)
        if form.is_valid():
            track = form.save(commit=False)
            track.enquiry = enquiry
            track.created_by = request.user
            track.save()
            return JsonResponse({'success': True})
    else:
        form = EnquiryTrackForm()

    context = {'form': form, 'enquiry': enquiry,
               'form_action': reverse('lead_enquiries:enquiry_track_create', args=[enquiry_pk])}
    html_form = render_to_string('lead_enquiries/track_form_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})

# 更新報價單追蹤紀錄
@login_required
def enquiry_track_update(request, pk):
    track = get_object_or_404(EnquiryTrack, pk=pk)
    if track.created_by != request.user:
        return HttpResponseForbidden("您不是此追蹤紀錄的建立者")
    if request.method == 'POST':
        form = EnquiryTrackForm(request.POST, instance=track)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
    else:
        form = EnquiryTrackForm(instance=track)

    context = {'form': form, 'enquiry': track.enquiry,
               'form_action': reverse('lead_enquiries:enquiry_track_update', args=[pk])}
    html_form = render_to_string('lead_enquiries/track_form_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})

# 刪除報價單追蹤紀錄
@login_required
def enquiry_track_delete(request, pk):
    track = get_object_or_404(EnquiryTrack, pk=pk)
    if track.created_by != request.user:
        return HttpResponseForbidden("您不是此追蹤紀錄的建立者")
    if request.method == 'POST':
        track.delete()
        return JsonResponse({'success': True})

    context = {'track': track}
    html_form = render_to_string('lead_enquiries/track_delete_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})



# 匯出功能
@login_required
def export_enquiries_csv(request):
    enquiries = _get_filtered_enquiries_queryset(request).annotate(
        annotated_total_amount_ntd=ExpressionWrapper(
            Sum(F('items__quantity') * F('items__unit_price') * F('items__exchange_rate')),
            output_field=FloatField()
        )
    )

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')
    filename = escape_uri_path(f"報價單清單_{timezone.now().date()}.csv")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['博威單號', '客戶單號', '客戶名稱', '狀態', '總金額', '建立者', '建立時間'])

    for enquiry in enquiries:
        writer.writerow([
            enquiry.bwp_no,
            enquiry.enquiry_no,
            enquiry.potential_customer.company_name,
            enquiry.get_status_display(),
            enquiry.annotated_total_amount_ntd or 0,
            enquiry.created_by.username,
            enquiry.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response

# 上傳附件
@login_required
def enquiry_attachment_upload(request, enquiry_pk):
    enquiry = get_object_or_404(Enquiry, pk=enquiry_pk)
    if request.method == 'POST':
        # 記得要傳入 request.FILES 來處理檔案
        form = EnquiryAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.enquiry = enquiry
            attachment.uploaded_by = request.user
            attachment.save()
            return JsonResponse({'success': True})
    else:
        form = EnquiryAttachmentForm()

    context = {'form': form, 'enquiry': enquiry}
    html_form = render_to_string('lead_enquiries/attachment_form_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})

# 刪除附件
@login_required
def enquiry_attachment_delete(request, pk):
    attachment = get_object_or_404(EnquiryAttachment, pk=pk)
    if request.method == 'POST':
        # 刪除檔案本身
        attachment.file.delete(save=False)
        # 刪除資料庫紀錄
        attachment.delete()
        return JsonResponse({'success': True})

    context = {'attachment': attachment}
    html_form = render_to_string('lead_enquiries/attachment_delete_modal.html', context, request=request)
    return JsonResponse({'html_form': html_form})