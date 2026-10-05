from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class Student(models.Model):
    YEAR_LEVELS = [(year, f"Year {year}") for year in range(1, 7)]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="student_profile")
    student_id = models.CharField(max_length=24, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(blank=True)
    course = models.CharField(max_length=120)
    year_level = models.PositiveSmallIntegerField(choices=YEAR_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"


class Equipment(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    total_quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    available_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.CheckConstraint(
            condition=Q(available_quantity__lte=F("total_quantity")), name="available_not_above_total"
        )]

    def save(self, *args, **kwargs):
        if self._state.adding and self.available_quantity == 0:
            self.available_quantity = self.total_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BorrowRecord(models.Model):
    class Status(models.TextChoices):
        BORROWED = "borrowed", "Borrowed"
        RETURNED = "returned", "Returned"
        LOST = "lost", "Lost"

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="borrow_records")
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="borrow_records")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    borrowed_on = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_on = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BORROWED)

    class Meta:
        ordering = ["-borrowed_on"]
        constraints = [models.CheckConstraint(condition=Q(quantity__gte=1), name="borrow_quantity_at_least_one")]

    @property
    def is_overdue(self):
        from django.utils import timezone

        return self.status == self.Status.BORROWED and self.due_date < timezone.localdate()

    def __str__(self):
        return f"{self.student} / {self.equipment}"