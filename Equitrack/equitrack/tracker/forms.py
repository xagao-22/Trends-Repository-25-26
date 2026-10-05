from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import BorrowRecord, Equipment, Student


class RegistrationForm(UserCreationForm):
    student_id = forms.CharField(max_length=24, label="Student ID")
    first_name = forms.CharField(max_length=80, label="First name")
    last_name = forms.CharField(max_length=80, label="Last name")
    email = forms.EmailField(label="School email")
    course = forms.CharField(max_length=120)
    year_level = forms.ChoiceField(choices=Student.YEAR_LEVELS, label="Year level")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "student_id", "course", "year_level")

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"]
        if Student.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("A student with this ID is already registered.")
        return student_id


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ("student_id", "first_name", "last_name", "email", "course", "year_level")


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ("name", "category", "description", "total_quantity")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_total_quantity(self):
        total = self.cleaned_data["total_quantity"]
        if self.instance.pk and total < self.instance.total_quantity - self.instance.available_quantity:
            raise forms.ValidationError("Total quantity cannot be less than the number currently on loan.")
        return total

    def save(self, commit=True):
        borrowed = self.instance.total_quantity - self.instance.available_quantity if self.instance.pk else 0
        equipment = super().save(commit=False)
        if equipment.pk:
            equipment.available_quantity = self.cleaned_data["total_quantity"] - borrowed
        if commit:
            equipment.save()
            self.save_m2m()
        return equipment


class BorrowRecordForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ("student", "equipment", "quantity", "due_date")
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.order_by("last_name", "first_name")
        self.fields["equipment"].queryset = Equipment.objects.filter(available_quantity__gt=0).order_by("name")