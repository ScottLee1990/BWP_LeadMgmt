# main/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from leads.models import PotentialCustomer
from lead_enquiries.models import Enquiry
from .models import DashboardGoal
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, FloatField


# 根據傳入的週期字串，計算開始與結束日期
def get_date_range(period):

    today = timezone.now().date()
    if period == 'quarterly':
        current_quarter = (today.month - 1) // 3 + 1
        start_date = timezone.make_aware(timezone.datetime(today.year, 3 * current_quarter - 2, 1))
        end_date = timezone.now()
    elif period == 'yearly':
        start_date = timezone.make_aware(timezone.datetime(today.year, 1, 1))
        end_date = timezone.now()
    else:  # 預設為 'monthly'
        start_date = timezone.make_aware(timezone.datetime(today.year, today.month, 1))
        end_date = timezone.now()
    return start_date, end_date

# 儀錶板
@login_required
def dashboard(request):
    period = request.GET.get('period', 'monthly')
    start_date, end_date = get_date_range(period)

    goal, _ = DashboardGoal.objects.get_or_create(period=period)

    customers_in_period = PotentialCustomer.objects.filter(created_at__range=(start_date, end_date))
    enquiries_in_period = Enquiry.objects.filter(created_at__range=(start_date, end_date))

    # 客戶區塊統計表
    new_customers_count = customers_in_period.count()
    inquired_customers_count = PotentialCustomer.objects.filter(created_at__range=(start_date, end_date),
                                                                enquiries__isnull=False).distinct().count()
    success_customers_count = PotentialCustomer.objects.filter(created_at__range=(start_date, end_date),
                                                               enquiries__status='success').distinct().count()
    pinned_customers = PotentialCustomer.objects.filter(is_pinned=True)

    # 報價區塊統計表
    new_enquiries_count = enquiries_in_period.count()

    # 計算新增報價總額
    new_enquiries_amount_agg = enquiries_in_period.aggregate(
        total_ntd=Sum(
            F('items__quantity') * F('items__unit_price') * F('items__exchange_rate'),
            output_field=FloatField()
        )
    )
    new_enquiries_amount = new_enquiries_amount_agg['total_ntd'] or 0

    success_enquiries = enquiries_in_period.filter(status='success')
    success_enquiries_count = success_enquiries.count()

    # 計算成交報價總額
    success_enquiries_amount_agg = success_enquiries.aggregate(
        total_ntd=Sum(
            F('items__quantity') * F('items__unit_price') * F('items__exchange_rate'),
            output_field=FloatField()
        )
    )
    success_enquiries_amount = success_enquiries_amount_agg['total_ntd'] or 0

    pinned_enquiries = Enquiry.objects.filter(is_pinned=True)

    # 百分比計算
    try:
        success_customers_percentage = (success_customers_count / goal.new_customer_target) * 100 if goal.new_customer_target > 0 else 0
    except (TypeError, ZeroDivisionError):
        success_customers_percentage = 0

    try:
        new_enquiries_amount_percentage = (float(new_enquiries_amount) / float(
            goal.enquiry_amount_target)) * 100 if goal.enquiry_amount_target > 0 else 0
    except (TypeError, ZeroDivisionError):
        new_enquiries_amount_percentage = 0

    try:
        success_enquiries_amount_percentage = (float(success_enquiries_amount) / float(
            goal.success_amount_target)) * 100 if goal.success_amount_target > 0 else 0
    except (TypeError, ZeroDivisionError):
        success_enquiries_amount_percentage = 0

    context = {
        'period': period,
        'goal': goal,
        # 客戶數據
        'new_customers_count': new_customers_count,
        'inquired_customers_count': inquired_customers_count,
        'success_customers_count': success_customers_count,
        'pinned_customers': pinned_customers,
        # 報價數據
        'new_enquiries_count': new_enquiries_count,
        'new_enquiries_amount': new_enquiries_amount,
        'success_enquiries_count': success_enquiries_count,
        'success_enquiries_amount': success_enquiries_amount,
        'pinned_enquiries': pinned_enquiries,
        # 百分比數據
        'success_customers_percentage': success_customers_percentage,
        'new_enquiries_amount_percentage': new_enquiries_amount_percentage,
        'success_enquiries_amount_percentage': success_enquiries_amount_percentage,
    }
    return render(request, 'main/main.html', context)