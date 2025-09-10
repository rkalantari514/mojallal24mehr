from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, EventDetail
from datetime import timedelta
from dateutil.relativedelta import relativedelta


@receiver(post_save, sender=Event)
def create_event_details(sender, instance, created, **kwargs):
    if created:
        details = []
        start_date = instance.first_occurrence
        end_date = instance.last_occurrence or instance.first_occurrence

        # فاصله تکرار بر اساس repeat_interval
        delta = None
        if instance.repeat_interval == 'daily':
            delta = timedelta(days=1)
        elif instance.repeat_interval == 'weekly':
            delta = timedelta(weeks=1)
        elif instance.repeat_interval == 'biweekly':
            delta = timedelta(weeks=2)
        elif instance.repeat_interval == 'monthly':
            delta = relativedelta(months=1)
        elif instance.repeat_interval == 'quarterly':
            delta = relativedelta(months=3)
        elif instance.repeat_interval == 'semi_annually':
            delta = relativedelta(months=6)
        elif instance.repeat_interval == 'annually':
            delta = relativedelta(years=1)

        current_date = start_date
        seq = 1
        while current_date <= end_date:
            details.append(EventDetail(
                event=instance,
                scheduled_date=current_date,
                sequence_number=seq,
                status_relative_to_schedule='not_held'
            ))
            seq += 1

            if delta:
                current_date = current_date + delta
            else:  # بدون تکرار
                break

        EventDetail.objects.bulk_create(details)
