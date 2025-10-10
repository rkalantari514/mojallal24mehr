from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os

class CustomUserManager(BaseUserManager):
    def create_user(self, mobile_number, password=None):
        if not mobile_number:
            raise ValueError('Users must have a mobile number')

        user = self.model(
            mobile_number=mobile_number,
            is_active=True,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, password):
        user = self.create_user(
            mobile_number=mobile_number,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

def upload_image_path(instance, filename):
    name, ext = get_filename_ext(filename)
    final_name = f"{instance.id}{ext}"
    return f"profile/{final_name}"

class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    mobile_number = models.CharField(max_length=15, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    password_expiry_date = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(upload_to=upload_image_path, default='unnamed.png', null=True, blank=True, verbose_name='تصویر پروفایل')
    is_dark_mode = models.BooleanField(default=False)  # فیلد جدید برای ذخیره حالت شب

    objects = CustomUserManager()

    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def set_password_expiry(self):
        self.password_expiry_date = timezone.now() + timedelta(days=30)
        self.save()

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.mobile_number

@receiver(post_save, sender=CustomUser)
def resize_avatar(sender, instance, **kwargs):
    """
    Safely crop/resize avatar to 200x200 when the avatar file is actually present.
    - Skip on saves that don't update the avatar (e.g., last_login updates during login).
    - Guard against missing files and any PIL errors to avoid 500 on login.
    """
    # If this save didn't touch the avatar field, skip processing
    update_fields = kwargs.get('update_fields')
    if update_fields and ('avatar' not in update_fields):
        return

    from django.core.files.storage import default_storage
    try:
        # Ensure there is an avatar set and the file exists in storage
        if not instance.avatar or not getattr(instance.avatar, 'name', None):
            return
        avatar_name = instance.avatar.name
        if not default_storage.exists(avatar_name):
            return

        # Resolve a filesystem path if possible
        avatar_path = getattr(instance.avatar, 'path', None)
        if not avatar_path:
            try:
                avatar_path = default_storage.path(avatar_name)
            except Exception:
                avatar_path = None
        if not avatar_path or not os.path.exists(avatar_path):
            return

        # Open, center-crop to square, resize, and save back
        with Image.open(avatar_path) as temp_image:
            width, height = temp_image.size
            min_dimension = min(width, height)
            crop_image = temp_image.crop((
                (width - min_dimension) // 2,
                (height - min_dimension) // 2,
                (width + min_dimension) // 2,
                (height + min_dimension) // 2,
            ))
            resized_image = crop_image.resize((200, 200), Image.LANCZOS)
            # Preserve format if possible; fallback to PNG
            format_ = temp_image.format or 'PNG'
            resized_image.save(avatar_path, format=format_)
    except Exception:
        # Never fail the request due to avatar processing
        return


class UserLog(models.Model):
    user=models.ForeignKey(CustomUser,blank=True, null=True, on_delete=models.CASCADE ,verbose_name='کاربر')
    page=models.CharField(max_length=150, verbose_name='صفحه',null=True, blank=True)
    code=models.CharField(max_length=150, verbose_name='کد',null=True, blank=True)
    time=models.DateTimeField(auto_now_add=True,verbose_name='زمان بازدید',null=True, blank=True)

    class Meta:
        verbose_name = 'بازدید کاربر'
        verbose_name_plural = 'بازدید کاربران'

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'


from django.contrib.auth.models import Group  # برای دسترسی به مدل Group

class MyPage(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='نام')
    v_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='نام ویو')
    p_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='صفحات سایت')
    # allowed_groups = models.ManyToManyField(
    #     Group,
    #     blank=True,
    #     related_name='allowed_pages',
    #     verbose_name='گروه‌های مجاز'
    # )

    class Meta:
        verbose_name = 'صفحه سایت'
        verbose_name_plural = 'صفحات سایت'

    def __str__(self):
        return self.name




from django.contrib.auth.models import Group
from django.db import models

from django.contrib.auth.models import Group
from django.db import models

# افزودن فیلد نام فارسی و صفحات مجاز به مدل Group
class CustomGroup(Group):
    persian_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='نام فارسی')
    allowed_pages = models.ManyToManyField(
        MyPage,
        blank=True,
        related_name='allowed_groups',
        verbose_name='صفحات مجاز'
    )
    default_page = models.ForeignKey(
        MyPage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='default_for_groups',
        verbose_name='صفحه پیش‌فرض'
    )

    class Meta:
        verbose_name = 'گروه کاربری'
        verbose_name_plural = 'گروه‌های کاربری'
