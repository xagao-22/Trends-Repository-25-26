from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BorrowRecordForm, EquipmentForm, RegistrationForm, StudentForm
from .models import BorrowRecord, Equipment, Student


def staff_required(view):
    return login_required(user_passes_test(lambda user: user.is_staff, login_url="dashboard")(view))


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Student.objects.create(
                user=user, student_id=form.cleaned_data["student_id"],
                first_name=form.cleaned_data["first_name"], last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"], course=form.cleaned_data["course"],
                year_level=form.cleaned_data["year_level"],
            )
        login(request, user)
        messages.success(request, "Your EQUI-Track account is ready.")
        return redirect("dashboard")
    return render(request, "tracker/register.html", {"form": form})


@login_required
def dashboard(request):
    today = timezone.localdate()
    if request.user.is_staff:
        records = BorrowRecord.objects.select_related("student", "equipment")
        stats = [
            ("Total students", Student.objects.count(), "people", "blue"),
            ("Total equipment", Equipment.objects.count(), "boxes", "teal"),
            ("Active borrowed", records.filter(status=BorrowRecord.Status.BORROWED).count(), "activity", "amber"),
            ("Overdue", records.filter(status=BorrowRecord.Status.BORROWED, due_date__lt=today).count(), "clock", "red"),
        ]
        recent = records[:6]
    else:
        student = Student.objects.filter(user=request.user).first()
        own_records = BorrowRecord.objects.filter(student=student) if student else BorrowRecord.objects.none()
        stats = [
            ("Equipment types", Equipment.objects.count(), "boxes", "blue"),
            ("Items available", sum(Equipment.objects.values_list("available_quantity", flat=True)), "check", "teal"),
            ("My active loans", own_records.filter(status=BorrowRecord.Status.BORROWED).count(), "activity", "amber"),
            ("My overdue", own_records.filter(status=BorrowRecord.Status.BORROWED, due_date__lt=today).count(), "clock", "red"),
        ]
        recent = own_records.select_related("student", "equipment")[:6]
    return render(request, "tracker/dashboard.html", {"stats": stats, "recent": recent})


@staff_required
def students(request):
    query = request.GET.get("q", "").strip()
    student_list = Student.objects.all()
    if query:
        student_list = student_list.filter(
            Q(student_id__icontains=query) | Q(first_name__icontains=query) |
            Q(last_name__icontains=query) | Q(course__icontains=query)
        )
    return render(request, "tracker/students.html", {"students": student_list, "query": query})


@staff_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student account added.")
        return redirect("students")
    return render(request, "tracker/form_page.html", {"form": form, "title": "Add student", "back_url": "students"})


@staff_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student details updated.")
        return redirect("students")
    return render(request, "tracker/form_page.html", {"form": form, "title": "Edit student", "back_url": "students"})


@login_required
def equipment_list(request):
    query = request.GET.get("q", "").strip()
    equipment = Equipment.objects.all()
    if query:
        equipment = equipment.filter(Q(name__icontains=query) | Q(category__icontains=query))
    return render(request, "tracker/equipment.html", {"equipment_list": equipment, "query": query})


@staff_required
def equipment_create(request):
    form = EquipmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Equipment added to inventory.")
        return redirect("equipment")
    return render(request, "tracker/form_page.html", {"form": form, "title": "Add equipment", "back_url": "equipment"})


@staff_required
def equipment_update(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    form = EquipmentForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Inventory details updated.")
        return redirect("equipment")
    return render(request, "tracker/form_page.html", {"form": form, "title": "Edit equipment", "back_url": "equipment"})


@staff_required
def equipment_delete(request, pk):
    item = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        if item.borrow_records.exists():
            messages.error(request, "Equipment with borrowing history cannot be deleted.")
        else:
            item.delete()
            messages.success(request, "Equipment removed from inventory.")
        return redirect("equipment")
    return redirect("equipment")


@login_required
def borrow_records(request):
    records = BorrowRecord.objects.select_related("student", "equipment")
    if not request.user.is_staff:
        student = Student.objects.filter(user=request.user).first()
        records = records.filter(student=student) if student else records.none()
    status = request.GET.get("status", "")
    if status in BorrowRecord.Status.values:
        records = records.filter(status=status)
    return render(request, "tracker/borrow_records.html", {"records": records, "status_filter": status})


@login_required
def borrow_create(request):
    student = Student.objects.filter(user=request.user).first()
    if not request.user.is_staff and student is None:
        messages.error(request, "Your account needs a student profile before you can borrow equipment.")
        return redirect("dashboard")
    form = BorrowRecordForm(request.POST or None, initial={"equipment": request.GET.get("equipment")})
    if not request.user.is_staff:
        form.fields["student"].queryset = Student.objects.filter(pk=student.pk)
        form.fields["student"].initial = student
        form.fields["student"].widget = form.fields["student"].hidden_widget()
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            item = Equipment.objects.select_for_update().get(pk=form.cleaned_data["equipment"].pk)
            quantity = form.cleaned_data["quantity"]
            if quantity > item.available_quantity:
                form.add_error("quantity", f"Only {item.available_quantity} available right now.")
            else:
                record = form.save(commit=False)
                record.equipment = item
                if not request.user.is_staff:
                    record.student = student
                item.available_quantity -= quantity
                item.save(update_fields=["available_quantity"])
                record.save()
                messages.success(request, "Borrowing recorded. Inventory has been updated.")
                return redirect("borrow_records")
    return render(request, "tracker/borrow_form.html", {"form": form})


@staff_required
def borrow_return(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            record = get_object_or_404(BorrowRecord.objects.select_for_update(), pk=pk)
            if record.status == BorrowRecord.Status.BORROWED:
                item = Equipment.objects.select_for_update().get(pk=record.equipment_id)
                item.available_quantity += record.quantity
                item.save(update_fields=["available_quantity"])
                record.status = BorrowRecord.Status.RETURNED
                record.returned_on = timezone.now()
                record.save(update_fields=["status", "returned_on"])
                messages.success(request, "Return confirmed and inventory restored.")
    return redirect("borrow_records")


@staff_required
def borrow_lost(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            record = get_object_or_404(BorrowRecord.objects.select_for_update(), pk=pk)
            if record.status == BorrowRecord.Status.BORROWED:
                item = Equipment.objects.select_for_update().get(pk=record.equipment_id)
                item.total_quantity -= record.quantity
                item.save(update_fields=["total_quantity"])
                record.status = BorrowRecord.Status.LOST
                record.save(update_fields=["status"])
                messages.warning(request, "Record marked lost. The recorded stock total was reduced.")
    return redirect("borrow_records")