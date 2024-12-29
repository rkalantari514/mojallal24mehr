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

    objects = CustomUserManager()

    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.mobile_number

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

@receiver(post_save, sender=CustomUser)
def resize_avatar(sender, instance, **kwargs):
    if instance.avatar and hasattr(instance.avatar, 'path'):
        temp_image = Image.open(instance.avatar.path)
        width, height = temp_image.size
        min_dimension = min(width, height)
        crop_image = temp_image.crop((
            (width - min_dimension) // 2,
            (height - min_dimension) // 2,
            (width + min_dimension) // 2,
            (height + min_dimension) // 2,
        ))
        resized_image = crop_image.resize((200, 200), Image.LANCZOS)
        resized_image.save(instance.avatar.path)


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