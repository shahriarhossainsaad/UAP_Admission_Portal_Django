from django.contrib import admin
from .models import Department, Teacher, Application, ApplicationFile, Payment

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code','name','seats','total_credits','per_credit_fee')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name','department','position','email')

class ApplicationFileInline(admin.TabularInline):
    model = ApplicationFile
    readonly_fields = ('uploaded_at',)
    extra = 0

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id','full_name','department','program','status','applied_at')
    inlines = [ApplicationFileInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id','application','amount','status','paid_at')
