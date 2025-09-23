# events/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import transaction # برای مدیریت Formset ها

from custom_login.models import UserLog, CustomUser
from custom_login.views import page_permision
from mahakupdate.sendtogap import send_to_admin, send_sms, send_to_managers
from .models import EventCategory, Event, EventDetail, Resolution, EventImage, Reminder
from .forms import (
    EventCategoryForm, EventForm, EventDetailForm, ResolutionForm, EventImageForm,
    ResolutionFormSet, EventImageFormSet
)

# -----------------------------------------------------------
# EventCategory Views
# -----------------------------------------------------------
# class EventCategoryListView(ListView):
#     model = EventCategory
#     template_name = 'events/category_list.html'
#     context_object_name = 'categories'

class EventCategoryListView(ListView):
    model = EventCategory
    template_name = 'events/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        # 1. بررسی مجوز (page_permission)
        name = 'دسته بندی رویدادها'
        result = page_permision(request, name)  # ← فرض می‌کنیم این تابع در همان فایل یا یک فایل دیگر تعریف شده
        if result:
            return result  # مثلاً یک Redirect یا HttpResponseForbidden

        # 2. ثبت لاگ کاربر
        user = request.user
        if user.is_authenticated and user.mobile_number != '09151006447':
            UserLog.objects.create(user=user, page='دسته بندی رویدادها', code=0)

        # 3. اجرای dispatch اصلی
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 4. افزودن user به context
        context['user'] = self.request.user

        # 5. افزودن title به context
        context['title'] = 'دسته بندی رویدادها'

        return context


class EventCategoryCreateView(CreateView):
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'events/category_form.html'
    success_url = reverse_lazy('events:category_list')

class EventCategoryUpdateView(UpdateView):
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'events/category_form.html'
    success_url = reverse_lazy('events:category_list')

class EventCategoryDeleteView(DeleteView):
    model = EventCategory
    template_name = 'events/category_confirm_delete.html'
    success_url = reverse_lazy('events:category_list')

# -----------------------------------------------------------
# Event Views
# -----------------------------------------------------------
class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 10 # اختیاری: برای صفحه بندی
    def dispatch(self, request, *args, **kwargs):
        # 1. بررسی مجوز (page_permission)
        name = 'لیست رویدادها'
        result = page_permision(request, name)  # ← فرض می‌کنیم این تابع در همان فایل یا یک فایل دیگر تعریف شده
        if result:
            return result  # مثلاً یک Redirect یا HttpResponseForbidden

        # 2. ثبت لاگ کاربر
        user = request.user
        if user.is_authenticated and user.mobile_number != '09151006447':
            UserLog.objects.create(user=user, page='لیست رویدادها', code=0)

        # 3. اجرای dispatch اصلی
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 4. افزودن user به context
        context['user'] = self.request.user

        # 5. افزودن title به context
        context['title'] = 'لیست رویدادها'

        return context

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    def dispatch(self, request, *args, **kwargs):
        # 1. بررسی مجوز (page_permission)
        name = 'جزئیات رویداد'
        result = page_permision(request, name)  # ← فرض می‌کنیم این تابع در همان فایل یا یک فایل دیگر تعریف شده
        if result:
            return result  # مثلاً یک Redirect یا HttpResponseForbidden

        # 2. ثبت لاگ کاربر
        user = request.user
        if user.is_authenticated and user.mobile_number != '09151006447':
            UserLog.objects.create(user=user, page='جزئیات رویداد', code=0)

        # 3. اجرای dispatch اصلی
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 4. افزودن user به context
        context['user'] = self.request.user

        # 5. افزودن title به context
        context['title'] = 'جزئیات رویداد'

        return context


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:event_list')

class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    context_object_name = 'event'
    success_url = reverse_lazy('events:event_list')

class EventDeleteView(DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('events:event_list')

# -----------------------------------------------------------
# EventDetail Views (با Formsets برای Resolution و EventImage)
# -----------------------------------------------------------
# events/views.py

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import transaction

from .models import Event, EventDetail
from .forms import EventDetailForm, ResolutionFormSet, EventImageFormSet

# --- (باقی Event / EventCategory views اینجا باشند اگر لازم داری) ---
# برای کوتاهی اینجا فقط EventDetail views را می‌آورم


class EventDetailCreateView(CreateView):
    model = EventDetail
    form_class = EventDetailForm
    template_name = 'events/eventdetail_form.html'

    def dispatch(self, request, *args, **kwargs):
        # والد (Event) را اینجا نگه می‌داریم
        self.parent_event = get_object_or_404(Event, pk=kwargs.get('event_pk'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # اگر فرم از قبل در kwargs پاس شده، از آن استفاده کن تا ارورها نشان داده شوند
        form = kwargs.get('form', data.get('form', self.get_form()))
        data['form'] = form

        if self.request.POST:
            data['resolutions'] = ResolutionFormSet(self.request.POST, prefix='resolutions')
            data['images'] = EventImageFormSet(self.request.POST, self.request.FILES, prefix='images')
        else:
            # در ایجاد، کوئری‌ست خالی باشه
            data['resolutions'] = ResolutionFormSet(prefix='resolutions', queryset=Resolution.objects.none())
            data['images'] = EventImageFormSet(prefix='images', queryset=EventImage.objects.none())

        # برای قالب راحتتر باشه که object برای create None باشه
        data['object'] = None
        return data

    def form_valid(self, form):
        # بازسازی فرم‌ست‌ها از POST تا دقیقاً bound باشند
        resolutions = ResolutionFormSet(self.request.POST, prefix='resolutions')
        images = EventImageFormSet(self.request.POST, self.request.FILES, prefix='images')

        # ست کردن event روی instance قبل از ذخیره
        form.instance.event = self.parent_event

        if form.is_valid() and resolutions.is_valid() and images.is_valid():
            with transaction.atomic():
                self.object = form.save()
                resolutions.instance = self.object
                resolutions.save()
                images.instance = self.object
                images.save()
            return redirect(self.get_success_url())
        # اگر اعتبارسنجی شکست، فرم و فرم‌ست‌ها را دوباره render کن تا ارورها نمایش داده شوند
        return self.form_invalid(form)

    def form_invalid(self, form):
        # get_context_data در حالت POST فرم‌ست‌های bound را می‌سازد (پس کافی است)
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        # بعد از ذخیره به صفحه‌ی جزئیات رویداد اصلی هدایت می‌کنیم
        return reverse_lazy('events:event_detail', kwargs={'pk': self.parent_event.pk})


class EventDetailUpdateView(UpdateView):
    model = EventDetail
    form_class = EventDetailForm
    template_name = 'events/eventdetail_form.html'
    context_object_name = 'event_detail'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        form = kwargs.get('form', data.get('form', self.get_form()))
        data['form'] = form

        if self.request.POST:
            data['resolutions'] = ResolutionFormSet(self.request.POST, prefix='resolutions', instance=self.object)
            data['images'] = EventImageFormSet(self.request.POST, self.request.FILES, prefix='images', instance=self.object)
        else:
            data['resolutions'] = ResolutionFormSet(prefix='resolutions', instance=self.object)
            data['images'] = EventImageFormSet(prefix='images', instance=self.object)

        # برای قالب
        data['object'] = self.object
        return data

    def form_valid(self, form):
        resolutions = ResolutionFormSet(self.request.POST, prefix='resolutions', instance=self.object)
        images = EventImageFormSet(self.request.POST, self.request.FILES, prefix='images', instance=self.object)

        if form.is_valid() and resolutions.is_valid() and images.is_valid():
            with transaction.atomic():
                self.object = form.save()
                resolutions.instance = self.object
                resolutions.save()
                images.instance = self.object
                images.save()
            return redirect(self.get_success_url())
        return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        # بعد از ویرایش به صفحه رویداد اصلی برمی‌گردیم
        return reverse_lazy('events:event_detail', kwargs={'pk': self.object.event.pk})


from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from .models import Event, EventDetail, Resolution, EventImage
from .forms import EventDetailForm, ResolutionFormSet, EventImageFormSet



class EventDetailDetailView(DetailView):
    model = EventDetail
    template_name = 'events/eventdetail_detail.html'
    context_object_name = 'event_detail'



class EventDetailDeleteView(DeleteView):
    model = EventDetail
    template_name = 'events/eventdetail_confirm_delete.html'
    # success_url به صورت داینامیک در get_success_url تعیین می شود

    def get_success_url(self):
        # پس از حذف موفقیت آمیز، به صفحه جزئیات رویداد اصلی برگرد
        # باید مطمئن شویم که event_detail هنوز در دسترس است یا event_pk را از URL بگیریم
        event_pk = self.object.event.pk # قبل از حذف شیء، pk رویداد اصلی را بگیرید
        return reverse_lazy('events:event_detail', kwargs={'pk': event_pk})

# -----------------------------------------------------------
# سایر Views (اگر نیاز به مدیریت جداگانه Resolution و EventImage دارید)
# فعلاً برای اینها View جداگانه ای تعریف نمی کنیم چون از Formset استفاده می کنیم.
# -----------------------------------------------------------



from django.utils import timezone
from django.views.generic import ListView
from .models import EventDetail

class UpcomingEventDetailsListView(ListView):
    model = EventDetail
    template_name = 'events/upcoming_event_details.html'
    context_object_name = 'upcoming_details'
    paginate_by = 20  # اختیاری

    def get_queryset(self):
        today = timezone.now().date()
        # فقط جزئیاتی که هنوز برگزار نشده و تاریخ آنها در آینده است
        return EventDetail.objects.filter(
            occurrence_date__isnull=True,
            scheduled_date__gte=today
        ).select_related('event', 'event__category').order_by('scheduled_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


# events/views.py - ادامه کد

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import ListView
from .models import Resolution

class ResolutionListView(LoginRequiredMixin, ListView):
    model = Resolution
    template_name = 'events/resolutions.html'
    context_object_name = 'resolutions'
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        # 1. بررسی مجوز (page_permission)
        name = 'لیست برگزاری'
        result = page_permision(request, name)  # ← فرض می‌کنیم این تابع در همان فایل یا یک فایل دیگر تعریف شده
        if result:
            return result  # مثلاً یک Redirect یا HttpResponseForbidden

        # 2. ثبت لاگ کاربر
        user = request.user
        if user.is_authenticated and user.mobile_number != '09151006447':
            UserLog.objects.create(user=user, page='لیست برگزاری', code=0)

        # 3. اجرای dispatch اصلی
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 4. افزودن user به context
        context['user'] = self.request.user

        # 5. افزودن title به context
        context['title'] = 'لیست برگزاری'

        return context


    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'event_detail__event',
            'responsible_person'
        ).order_by('due_date', 'status')

        # فیلترهای دستی (از URL)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        # فیلتر مسئول
        if self.request.GET.get('assigned_to_me') == 'true':
            qs = qs.filter(responsible_person=self.request.user)
        elif self.request.GET.get('assigned_to_others') == 'true':
            qs = qs.exclude(responsible_person=self.request.user).filter(responsible_person__isnull=False)

        # فیلتر زمانی (due_date)
        date_filter = self.request.GET.get('date_filter')
        today = timezone.now().date()

        if date_filter == 'today':
            qs = qs.filter(due_date=today)
        elif date_filter == 'tomorrow':
            qs = qs.filter(due_date=today + timezone.timedelta(days=1))
        elif date_filter == 'next_week':
            end_of_week = today + timezone.timedelta(days=7)
            qs = qs.filter(due_date__range=[today, end_of_week])
        elif date_filter == 'overdue':
            qs = qs.filter(due_date__lt=today, status='pending')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        context['status_choices'] = Resolution.STATUS_CHOICES
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_date_filter'] = self.request.GET.get('date_filter', '')
        context['assigned_to_me'] = self.request.GET.get('assigned_to_me', '')
        context['assigned_to_others'] = self.request.GET.get('assigned_to_others', '')
        return context


# events/views.py

# ... (سایر ایمپورت‌های موجود)

# ایمپورت‌های جدید برای ویو یادآور
from django.http import JsonResponse
from django.utils import timezone
import requests
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
import jdatetime




# ویو اصلی برای ارسال یادآورها
# events/views.py

# ... (سایر ایمپورت‌های موجود)




# ویو اصلی برای ارسال یادآورها
def SendScheduledReminders(request):
    now = timezone.now()
    work_hours = [6, 7, 8,21]  # بازه مجاز ارسال

    print(f'ساعت جاری: {now.hour}')
    if now.hour not in work_hours:
        error_msg = f'❌ ارسال پیام غیر مجاز است ({now.hour}:00)'
        print(error_msg)
        send_to_admin(error_msg)
        return redirect('/updatedb')


    today = now.date()
    success_count = 0
    failure_count = 0
    created_reminder_count = 0

    try:
        upcoming_event_details = EventDetail.objects.filter(
            scheduled_date__gte=today,
            occurrence_date__isnull=True,  # هنوز برگزار نشده
            event__is_active=True
        ).select_related('event')

        for ed in upcoming_event_details:
            event = ed.event
            days_until_event = (ed.scheduled_date - today).days
            reminder_days = set()
            if event.reminder_interval > 0:
                reminder_days.add(event.reminder_interval)
            reminder_days.add(1)  # همیشه یک یادآور 1 روز قبل

            for days_before in reminder_days:
                scheduled_date = ed.scheduled_date - timedelta(days=days_before)
                # اگر scheduled_date گذشته باشد، دیگر نیازی به ایجاد ریمایندر نیست.
                if scheduled_date < today:
                    continue

                # بررسی اینکه آیا ریمایندر مربوطه قبلاً ایجاد شده است یا خیر.
                content_type = ContentType.objects.get_for_model(ed)
                reminder, created = Reminder.objects.get_or_create(
                    content_type=content_type,
                    object_id=ed.pk,
                    scheduled_send_date=scheduled_date,
                    defaults={
                        'reminder_type': 'event',
                        'is_sent': False
                    }
                )
                if created:
                    created_reminder_count += 1
                    print(f"Reminder created for EventDetail {ed.pk} (scheduled for {scheduled_date})")

        # 1.2 برای Resolution ها
        # پیدا کردن Resolution هایی که تاریخ مهلت آنها در آینده است و هنوز انجام نشده‌اند.
        upcoming_resolutions = Resolution.objects.filter(
            due_date__gte=today,
            status='pending',  # فقط مصوبات در حال انتظار
            event_detail__event__is_active=True
        )

        for res in upcoming_resolutions:
            days_until_due = (res.due_date - today).days

            # تعیین تعداد روزهای قبل که باید یادآور ارسال شود: 7 روز و 1 روز قبل.
            reminder_days = {7, 1}

            for days_before in reminder_days:
                scheduled_date = res.due_date - timedelta(days=days_before)
                # اگر scheduled_date گذشته باشد، دیگر نیازی به ایجاد ریمایندر نیست.
                if scheduled_date < today:
                    continue

                # بررسی اینکه آیا ریمایندر مربوطه قبلاً ایجاد شده است یا خیر.
                content_type = ContentType.objects.get_for_model(res)
                reminder, created = Reminder.objects.get_or_create(
                    content_type=content_type,
                    object_id=res.pk,
                    scheduled_send_date=scheduled_date,
                    defaults={
                        'reminder_type': 'resolution',
                        'is_sent': False
                    }
                )
                if created:
                    created_reminder_count += 1
                    print(f"Reminder created for Resolution {res.pk} (scheduled for {scheduled_date})")

        # --- مرحله 2: ارسال ریمایندرهای امروز ---

        # return redirect('/updatedb')

        # پیدا کردن تمام ریمایندرهای قابل ارسال برای امروز
        reminders_to_send = Reminder.objects.filter(
            scheduled_send_date__lte=today,
            is_sent=False
        ).select_related('content_type')

        for reminder in reminders_to_send:
            print(reminder)
        # return redirect('/updatedb')

        for reminder in reminders_to_send:
            try:
                # دریافت شیء مرتبط (EventDetail یا Resolution)
                related_object = reminder.content_object
                if not related_object:
                    print(f"Warning: Reminder {reminder.id} has no valid content_object. Skipping.")
                    failure_count += 1
                    continue

                # تعیین شماره موبایل گیرنده
                phone_number = None
                message = ""

                if isinstance(related_object, EventDetail):
                    # منطق برای EventDetail
                    event = related_object.event
                    days_until_event = (
                                related_object.scheduled_date - today).days if related_object.scheduled_date else None

                    # ساخت متن پیامک — با تاریخ شمسی و زیباسازی
                    event_name = event.name
                    category_name = event.category.name if event.category else "عمومی"

                    # تبدیل scheduled_date به شمسی
                    scheduled_date_str = jdatetime.date.fromgregorian(date=related_object.scheduled_date).strftime(
                        '%Y/%m/%d') if related_object.scheduled_date else "نامشخص"

                    # تعیین ایموجی و پیشوند بر اساس فاصله زمانی
                    if days_until_event is not None and days_until_event > 1:
                        emoji = "📅"
                        prefix = f"{emoji} یادآوری رویداد ({days_until_event} روز مانده)"
                        message = f"""\
                    مدیر محترم
                    {prefix}
                    📌 عنوان: {event_name}
                    🏛 از گروه: {category_name}
                    📆 تاریخ برنامه‌ریزی شده: {scheduled_date_str}

                    #یادآور_رویداد #{category_name.replace(' ', '_')} #هیئت_مدیره
                    """
                    elif days_until_event == 1:
                        emoji = "⚠️"
                        prefix = f"{emoji} فردا! یادآوری فوری رویداد"
                        message = f"""\
                    مدیر محترم
                    {prefix}
                    📌 عنوان: {event_name}
                    🏛 از گروه: {category_name}
                    📆 تاریخ: {scheduled_date_str}

                    #فردا_رویداد #{category_name.replace(' ', '_')} #هیئت_مدیره
                    """
                    else:  # days_until_event <= 0 یا None
                        emoji = "🔔"
                        prefix = f"{emoji} یادآوری فوری: امروز رویداد برگزار می‌شود!"
                        message = f"""\
                    مدیر محترم
                    {prefix}
                    📌 عنوان: {event_name}
                    🏛 از گروه: {category_name}
                    📆 تاریخ: {scheduled_date_str}

                    #امروز_رویداد #{category_name.replace(' ', '_')} #هیئت_مدیره
                    """



                    # تعیین گیرنده: اولین مسئول از مصوبات مرتبط
                    # تعیین گیرندگان: تمام اعضای گروه 'manager1'
                    try:
                        from django.contrib.auth.models import Group
                        manager_group = Group.objects.get(name='manager1')
                        responsible_users = CustomUser.objects.filter(
                            groups=manager_group,
                            is_active=True
                        ).values_list('mobile_number', flat=True)

                        if not responsible_users.exists():
                            admin_msg = f"⚠️ هشدار: گروه 'manager1' وجود ندارد یا عضو فعالی ندارد. (EventDetail ID: {related_object.id})"
                            send_to_admin(admin_msg)
                            print(
                                f"Warning: No active users found in group 'manager1' for EventDetail {related_object.id}. SMS skipped.")
                            failure_count += 1
                            continue

                        # حالا به جای یک شماره، یک لیست از شماره‌ها داریم
                        phone_numbers = list(responsible_users)
                        print("----------------------")
                        print(phone_numbers)

                    except Group.DoesNotExist:
                        admin_msg = f"❌ خطا: گروه 'manager1' در سیستم وجود ندارد. (EventDetail ID: {related_object.id})"
                        send_to_admin(admin_msg)
                        print(
                            f"Error: Group 'manager1' does not exist for EventDetail {related_object.id}. SMS skipped.")
                        failure_count += 1
                        continue
                    except Exception as e:
                        admin_msg = f"❌ خطای غیرمنتظره در بازیابی گروه 'manager1': {str(e)} (EventDetail ID: {related_object.id})"
                        send_to_admin(admin_msg)
                        print(f"Critical Error: {e} for EventDetail {related_object.id}. SMS skipped.")
                        failure_count += 1
                        continue

                elif isinstance(related_object, Resolution):
                    # منطق برای Resolution
                    due_date = related_object.due_date
                    days_until_due = (due_date - today).days if due_date else None

                    # ساخت متن پیامک — با تاریخ شمسی
                    # ساخت متن پیام — با تاریخ شمسی و شخصی‌سازی
                    resolution_text = related_object.text[:100] + "..." if len(
                        related_object.text) > 100 else related_object.text
                    status_display = related_object.get_status_display()

                    # >>>>>>>> تبدیل due_date به شمسی <<<<<<<<
                    due_date_str = jdatetime.date.fromgregorian(date=due_date).strftime(
                        '%Y/%m/%d') if due_date else "نامشخص"

                    # دریافت نام کامل مسئول
                    responsible_name = "مسئول محترم"
                    if related_object.responsible_person:
                        responsible_name = related_object.responsible_person.get_full_name() or related_object.responsible_person.mobile_number

                    # دریافت عنوان رویداد مربوطه
                    event_name = "رویداد نامشخص"
                    if related_object.event_detail and related_object.event_detail.event:
                        event_name = related_object.event_detail.event.name

                    # تعیین ایموجی و پیشوند بر اساس فاصله زمانی
                    if days_until_due is not None and days_until_due > 1:
                        emoji = "📅"
                        prefix = f"{emoji} یادآوری مصوبه ({days_until_due} روز مانده)"
                        message = f"""\
                    {responsible_name} عزیز
                    {prefix}
                    📌 مصوبه: {resolution_text}
                    🏛 رویداد مرتبط: {event_name}
                    📊 وضعیت: {status_display}
                    📆 مهلت انجام: {due_date_str}

                    #یادآور_مصوبه #مهلت_نزدیک #{event_name.replace(' ', '_')} #هیئت_مدیره
                    """
                    elif days_until_due == 1:
                        emoji = "⚠️"
                        prefix = f"{emoji} فردا! مهلت انجام مصوبه"
                        message = f"""\
                    {responsible_name} عزیز
                    {prefix}
                    📌 مصوبه: {resolution_text}
                    🏛 رویداد مرتبط: {event_name}
                    📊 وضعیت: {status_display}
                    📆 مهلت: {due_date_str}

                    #فردا_مهلت #مصوبه_فوری #{event_name.replace(' ', '_')} #هیئت_مدیره
                    """
                    elif days_until_due == 0:
                        emoji = "🚨"
                        prefix = f"{emoji} امروز! آخرین مهلت انجام مصوبه"
                        message = f"""\
                    {responsible_name} عزیز
                    {prefix}
                    📌 مصوبه: {resolution_text}
                    🏛 رویداد مرتبط: {event_name}
                    📊 وضعیت: {status_display}
                    📆 مهلت: {due_date_str}

                    #امروز_مهلت #مصوبه_فوری #{event_name.replace(' ', '_')} #هیئت_مدیره
                    """
                    else:  # days_until_due < 0
                        emoji = "⛔️"
                        prefix = f"{emoji} مهلت انجام مصوبه منقضی شده است!"
                        message = f"""\
                    {responsible_name} عزیز
                    {prefix}
                    📌 مصوبه: {resolution_text}
                    🏛 رویداد مرتبط: {event_name}
                    📊 وضعیت: {status_display}
                    📆 مهلت: {due_date_str} (منقضی شده)

                    #مهلت_گذشته #مصوبه_منقضی #{event_name.replace(' ', '_')} #هیئت_مدیره
                    """





                    # تعیین گیرنده: مسئول اجرا
                    if related_object.responsible_person and related_object.responsible_person.mobile_number:
                        phone_number = related_object.responsible_person.mobile_number
                    else:
                        admin_msg = f"⚠️ هشدار: برای مصوبه '{resolution_text[:30]}...' مسئولی با شماره موبایل تعریف نشده است. (Resolution ID: {related_object.id})"
                        send_to_admin(admin_msg)
                        print(
                            f"Warning: No responsible person or mobile number for Resolution {related_object.id}. SMS skipped.")
                        failure_count += 1
                        continue

                else:
                    print(f"Warning: Unsupported content type for Reminder {reminder.id}. Skipping.")
                    failure_count += 1
                    continue

                # ارسال پیام (از طریق گپ)
                try:
                    if isinstance(related_object, EventDetail):
                        # حالت اول: ارسال به لیست شماره‌ها (گروه manager1)
                        if not phone_numbers:
                            print(f"Warning: No phone numbers provided for EventDetail {related_object.id}. Skipping.")
                            failure_count += len(phone_numbers) if phone_numbers is not None else 1
                            continue

                        # ارسال گروهی با تابع send_to_managers
                        send_to_managers(phone_numbers, message)

                        # فرض می‌کنیم اگر تابع بدون Exception اجرا شد، ارسال موفق بوده است.
                        # (اگر می‌خواهید دقیق‌تر باشید، می‌توانید تابع send_to_managers را طوری تغییر دهید که وضعیت ارسال را برگرداند)
                        sent_successfully_to_at_least_one = True  # یا می‌توانید بر اساس پاسخ API تنظیم کنید

                        if sent_successfully_to_at_least_one:
                            reminder.is_sent = True
                            reminder.sent_at = now
                            reminder.save(update_fields=['is_sent', 'sent_at'])
                            success_count += len(phone_numbers)  # تعداد پیام‌های ارسالی
                        else:
                            failure_count += len(phone_numbers)
                            print(f"All Gap messages failed for Reminder {reminder.id}. Will retry later.")

                    elif isinstance(related_object, Resolution):
                        # حالت دوم: ارسال به یک شماره (مسئول مصوبه)
                        if phone_number and message:
                            # تبدیل phone_number به یک لیست تک‌عضوی برای استفاده در send_to_managers
                            send_to_managers([phone_number], message)

                            # فرض موفقیت (مگر اینکه Exception بدهد)
                            reminder.is_sent = True
                            reminder.sent_at = now
                            reminder.save(update_fields=['is_sent', 'sent_at'])
                            success_count += 1
                        else:
                            print(f"Warning: No phone number or message for Resolution {related_object.id}. Skipping.")
                            failure_count += 1
                            continue

                except Exception as e:
                    # اگر در ارسال گپ خطایی رخ داد
                    error_msg = f"Error sending via Gap for Reminder {reminder.id}: {e}"
                    print(error_msg)
                    send_to_admin(error_msg)

                    # افزایش failure_count بر اساس تعداد گیرندگان
                    if isinstance(related_object, EventDetail) and phone_numbers:
                        failure_count += len(phone_numbers)
                    elif isinstance(related_object, Resolution):
                        failure_count += 1


            except Exception as e:
                # در صورت بروز هرگونه خطای غیرمنتظره، لاگ کرده و به سراغ مورد بعدی بروید.
                failure_count += 1
                error_detail = f"Critical error processing Reminder {reminder.id}: {e}"
                print(error_detail)
                send_to_admin(f"❌ خطا در پردازش یادآور:\n{error_detail}")

        # ارسال گزارش نهایی به ادمین
        # ارسال گزارش نهایی به ادمین — با تاریخ شمسی و ایموجی
        jalali_today = jdatetime.date.fromgregorian(date=today).strftime('%Y/%m/%d')
        summary_msg = (
            f"📊 گزارش روزانه ارسال یادآورها\n"
            f"📅 تاریخ: {jalali_today}\n"
            f"🆕 ریمایندرهای جدید ایجاد شده: {created_reminder_count}\n"
            f"📬 ریمایندرهای قابل ارسال: {reminders_to_send.count()}\n"
            f"✅ رسال موفق: {success_count}\n"
            f"❌ ارسال ناموفق: {failure_count}"
        )
        send_to_admin(summary_msg)


        # # بازگرداندن یک پاسخ JSON برای نظارت و لاگینگ
        # return JsonResponse({
        #     'status': 'completed',
        #     'date': str(today),
        #     'reminders_created': created_reminder_count,
        #     'reminders_processed': reminders_to_send.count(),
        #     'success_count': success_count,
        #     'failure_count': failure_count,
        #     'message': 'Scheduled reminders processed successfully.'
        # })
    except Exception as e:
        # در صورت بروز خطای کلی در فرآیند
        critical_error_msg = f"❌ خطای بحرانی در اجرای SendScheduledReminders: {e}"
        print(critical_error_msg)
        send_to_admin(critical_error_msg)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return redirect('/updatedb')

