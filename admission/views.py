# admissions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import HttpResponse, Http404

from .models import Department, Teacher, Application, ApplicationFile, Payment

# ---------- Page views (render the templates in templates/admission/) ----------

def index(request):
    """
    Home page -> templates/admission/index.html
    """
    return render(request, 'admission/index.html', {})


def admission_info(request):
    """
    Admission information page.
    Provides department list to populate the calculator / info sections.
    Template: templates/admission/admission.html
    """
    departments = Department.objects.all().order_by('code')
    return render(request, 'admission/admission.html', {'departments': departments})


def admission_online(request):
    """
    Apply online page.
    Template: templates/admission/admission_online.html
    Provide departments & teachers for dropdowns / directory.
    """
    departments = Department.objects.all().order_by('code')
    teachers = Teacher.objects.select_related('department').all().order_by('department__code', 'name')
    return render(request, 'admission/admission_online.html', {
        'departments': departments,
        'teachers': teachers,
    })


# ---------- Form handler: application submission (multipart POST) ----------

@require_http_methods(["POST"])
def application_create(request):
    """
    Handle multipart/form-data POST from admission_online form.
    Expects the form field names:
      - full_name, email, phone, guardian, address, education, exam_roll
      - department (id or code), program
      - optional: fee_amount (if frontend supplied)
      - files keys: 'photo', 'sign', 'transcript'
    Saves Application and ApplicationFile objects.
    """

    data = request.POST
    files = request.FILES

    # Basic required validation
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    dept_value = data.get('department', '').strip()
    program = data.get('program', '').strip() or 'bachelors'

    if not (full_name and email and phone and dept_value):
        messages.error(request, 'Please fill name, email, phone and select department.')
        return redirect(reverse('admission:admission_online'))

    # Resolve department: try primary key then code
    department = None
    try:
        # try integer pk first
        try:
            department = Department.objects.get(pk=int(dept_value))
        except Exception:
            department = Department.objects.filter(code__iexact=dept_value).first()
        if not department:
            raise Department.DoesNotExist
    except Department.DoesNotExist:
        messages.error(request, 'Selected department does not exist.')
        return redirect(reverse('admission:admission_online'))

    # Fee resolution: frontend may pass fee_amount, otherwise fallback to dept.per_credit_fee
    fee_amount = data.get('fee_amount')
    try:
        fee_amount = int(fee_amount) if fee_amount else int(department.per_credit_fee or 0)
    except Exception:
        fee_amount = int(department.per_credit_fee or 0)

    # create application
    app = Application.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        guardian=data.get('guardian', '').strip(),
        address=data.get('address', '').strip(),
        education=data.get('education', '').strip(),
        exam_roll=data.get('exam_roll', '').strip(),
        department=department,
        program=program,
        fee_amount=fee_amount,
        status='submitted',
    )

    # handle uploaded files (if any)
    saved_any_file = False
    for kind in ('photo', 'sign', 'transcript'):
        f = files.get(kind)
        if f:
            ApplicationFile.objects.create(application=app, kind=kind, file=f)
            saved_any_file = True

    # if files exist mark docs_verified
    if saved_any_file:
        app.status = 'docs_verified'
        app.save()

    messages.success(request, f'Application submitted successfully (ID: {str(app.id)[:10]}).')
    # redirect back to apply page (or to a thank-you page if you create one)
    return redirect(reverse('admission:admission_online'))


# ---------- Utility / admin actions (staff only) ----------

def staff_required(view_func):
    """Shortcut decorator to require is_staff."""
    return user_passes_test(lambda u: u.is_active and u.is_staff, login_url='/admin/login/')(view_func)


@staff_required
@require_http_methods(["POST"])
def accept_applicant(request, pk):
    """
    Mark application accepted and decrement department seats.
    Accessible to staff users only.
    """
    app = get_object_or_404(Application, pk=pk)
    dept = app.department
    if dept.seats <= 0:
        messages.error(request, f'No seats left in {dept.code}.')
        return redirect(request.META.get('HTTP_REFERER', reverse('admin:index')))

    app.status = 'accepted'
    app.save()
    dept.seats = dept.seats - 1
    dept.save()
    messages.success(request, f'Application {app.id} accepted; seats left: {dept.seats}')
    return redirect(request.META.get('HTTP_REFERER', reverse('admin:index')))


@staff_required
@require_http_methods(["POST"])
def reject_applicant(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.status = 'rejected'
    app.save()
    messages.success(request, f'Application {app.id} rejected.')
    return redirect(request.META.get('HTTP_REFERER', reverse('admin:index')))


# ---------- Optional: view application detail (for dashboard display) ----------

def application_detail(request, pk):
    """
    Render a detail view for a given application, showing uploaded files.
    Template (optional): templates/admission/application_detail.html
    If that template does not exist, this view will simply return JSON or a 404.
    """
    app = get_object_or_404(Application, pk=pk)
    # If you created a template:
    try:
        return render(request, 'admission/application_detail.html', {'application': app})
    except Exception:
        # fallback: simple HttpResponse with basic info
        content = f'Application: {app.full_name} ({str(app.id)}) - Status: {app.status}'
        return HttpResponse(content)


# ---------- Auth views: login/logout (uses templates/admission/login.html) ----------

class CustomLoginView(LoginView):
    template_name = 'admission/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = '/'
