from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import BorrowRecord, Equipment, Student


class BorrowWorkflowTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", password="test-password", is_staff=True)
        self.student_user = User.objects.create_user(username="student", password="test-password")
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="ST-100",
            first_name="Alex",
            last_name="Rivera",
            course="Physical Education",
            year_level=1,
        )
        self.equipment = Equipment.objects.create(name="Volleyball", category="Ball", total_quantity=8)

    def test_checkout_and_return_update_available_stock(self):
        self.client.force_login(self.staff)
        response = self.client.post("/loans/new/", {
            "student": self.student.pk,
            "equipment": self.equipment.pk,
            "quantity": 3,
            "due_date": (timezone.localdate() + timedelta(days=7)).isoformat(),
        })

        self.assertRedirects(response, "/loans/")
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.available_quantity, 5)
        record = BorrowRecord.objects.get()

        response = self.client.post(f"/loans/{record.pk}/return/")

        self.assertRedirects(response, "/loans/")
        self.equipment.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(self.equipment.available_quantity, 8)
        self.assertEqual(record.status, BorrowRecord.Status.RETURNED)

    def test_students_can_only_see_their_own_borrow_records(self):
        other = Student.objects.create(
            student_id="ST-101", first_name="Sam", last_name="Lee", course="Science", year_level=2
        )
        record = BorrowRecord.objects.create(
            student=other,
            equipment=self.equipment,
            quantity=1,
            due_date=timezone.localdate() + timedelta(days=5),
        )
        self.client.force_login(self.student_user)

        response = self.client.get("/loans/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, record.student.student_id)

    def test_non_staff_cannot_open_student_directory(self):
        self.client.force_login(self.student_user)

        response = self.client.get("/students/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url.split("?", 1)[0], "/")

    def test_lost_equipment_reduces_total_stock(self):
        self.client.force_login(self.staff)
        record = BorrowRecord.objects.create(
            student=self.student,
            equipment=self.equipment,
            quantity=2,
            due_date=timezone.localdate() + timedelta(days=5),
        )
        self.equipment.available_quantity = 6
        self.equipment.save(update_fields=["available_quantity"])

        response = self.client.post(f"/loans/{record.pk}/lost/")

        self.assertRedirects(response, "/loans/")
        self.equipment.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(self.equipment.total_quantity, 6)
        self.assertEqual(self.equipment.available_quantity, 6)
        self.assertEqual(record.status, BorrowRecord.Status.LOST)