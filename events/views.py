# events/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import transaction # برای مدیریت Formset ها

from custom_login.models import UserLog
from custom_login.views import page_permision
from .models import EventCategory, Event, EventDetail, Resolution, EventImage
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