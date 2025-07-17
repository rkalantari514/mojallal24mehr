# events/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import transaction # برای مدیریت Formset ها

from .models import EventCategory, Event, EventDetail, Resolution, EventImage
from .forms import (
    EventCategoryForm, EventForm, EventDetailForm, ResolutionForm, EventImageForm,
    ResolutionFormSet, EventImageFormSet
)

# -----------------------------------------------------------
# EventCategory Views
# -----------------------------------------------------------
class EventCategoryListView(ListView):
    model = EventCategory
    template_name = 'events/category_list.html'
    context_object_name = 'categories'

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

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

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
class EventDetailCreateView(CreateView):
    model = EventDetail
    form_class = EventDetailForm
    template_name = 'events/eventdetail_form.html'
    # success_url به صورت داینامیک در get_success_url تعیین می شود

    def get_initial(self):
        initial = super().get_initial()
        # اگر event_pk در URL باشد، آن را به عنوان مقدار اولیه برای فیلد event تنظیم می کند
        event_pk = self.kwargs.get('event_pk')
        if event_pk:
            initial['event'] = get_object_or_404(Event, pk=event_pk)
        return initial

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['resolutions'] = ResolutionFormSet(self.request.POST, prefix='resolutions')
            data['images'] = EventImageFormSet(self.request.POST, self.request.FILES, prefix='images')
        else:
            data['resolutions'] = ResolutionFormSet(prefix='resolutions')
            data['images'] = EventImageFormSet(prefix='images')
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        resolutions = context['resolutions']
        images = context['images']
        with transaction.atomic():
            self.object = form.save() # ابتدا EventDetail را ذخیره می کنیم
            if resolutions.is_valid():
                resolutions.instance = self.object
                resolutions.save()
            if images.is_valid():
                images.instance = self.object
                images.save()
        return super().form_valid(form)

    def get_success_url(self):
        # پس از ایجاد موفقیت آمیز، به صفحه جزئیات رویداد اصلی برگرد
        return reverse_lazy('events:event_detail', kwargs={'pk': self.object.event.pk})


class EventDetailDetailView(DetailView):
    model = EventDetail
    template_name = 'events/eventdetail_detail.html'
    context_object_name = 'event_detail'

class EventDetailUpdateView(UpdateView):
    model = EventDetail
    form_class = EventDetailForm
    template_name = 'events/eventdetail_form.html'
    context_object_name = 'event_detail'
    # success_url به صورت داینامیک در get_success_url تعیین می شود

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['resolutions'] = ResolutionFormSet(self.request.POST, prefix='resolutions', instance=self.object)
            data['images'] = EventImageFormSet(self.request.POST, self.request.FILES, prefix='images', instance=self.object)
        else:
            data['resolutions'] = ResolutionFormSet(prefix='resolutions', instance=self.object)
            data['images'] = EventImageFormSet(prefix='images', instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        resolutions = context['resolutions']
        images = context['images']
        with transaction.atomic():
            self.object = form.save()
            if resolutions.is_valid():
                resolutions.instance = self.object
                resolutions.save()
            if images.is_valid():
                images.instance = self.object
                images.save()
        return super().form_valid(form)

    def get_success_url(self):
        # پس از ویرایش موفقیت آمیز، به صفحه جزئیات رویداد اصلی برگرد
        return reverse_lazy('events:event_detail', kwargs={'pk': self.object.event.pk})


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
