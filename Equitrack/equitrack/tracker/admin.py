from django.contrib import admin

from .models import BorrowRecord, Equipment, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "last_name", "first_name", "course", "year_level")
    search_fields = ("student_id", "first_name", "last_name", "course")
    list_filter = ("year_level", "course")


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "available_quantity", "total_quantity")
    search_fields = ("name", "category")
    list_filter = ("category",)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "equipment", "quantity", "borrowed_on", "due_date", "status")
    search_fields = ("student__student_id", "student__first_name", "student__last_name", "equipment__name")
    list_filter = ("status", "due_date")