# admissions/models.py
from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import FileExtensionValidator

def app_media_path(instance, filename):
    return f'applications/{instance.application.id}/{filename}'

class Department(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    total_credits = models.PositiveIntegerField(default=0)
    per_credit_fee = models.PositiveIntegerField(default=0)
    seats = models.PositiveIntegerField(default=0)
    def __str__(self): return f'{self.code}'

class Teacher(models.Model):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='teachers')
    name = models.CharField(max_length=128)
    position = models.CharField(max_length=128, blank=True)
    degrees = models.CharField(max_length=256, blank=True)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    def __str__(self): return self.name

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    guardian = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    education = models.CharField(max_length=300, blank=True)
    exam_roll = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='applications')
    program = models.CharField(max_length=50, choices=[('bachelors','Bachelors'),('masters','Masters'),('postgraduate','Postgraduate')])
    fee_amount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, default='submitted')
    applied_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_text = models.TextField(blank=True)
    def __str__(self): return f'{self.full_name}'

class ApplicationFile(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='files')
    kind = models.CharField(max_length=32, choices=[('photo','photo'),('sign','sign'),('transcript','transcript')])
    file = models.FileField(upload_to=app_media_path, validators=[FileExtensionValidator(['jpg','jpeg','png','pdf'])])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.application.id} - {self.kind}'

class Payment(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='payment')
    amount = models.PositiveIntegerField()
    method = models.CharField(max_length=64, default='mock')
    status = models.CharField(max_length=32, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_data = models.TextField(blank=True)
    def __str__(self): return f'Payment {self.application_id}'
