from django.urls import path

from . import views

urlpatterns = [
    path("students/", views.students, name="students"),
    path("students/add/", views.student_create, name="student_create"),
    path("students/<int:pk>/edit/", views.student_update, name="student_update"),
    path("equipment/", views.equipment_list, name="equipment"),
    path("equipment/add/", views.equipment_create, name="equipment_create"),
    path("equipment/<int:pk>/edit/", views.equipment_update, name="equipment_update"),
    path("equipment/<int:pk>/delete/", views.equipment_delete, name="equipment_delete"),
    path("loans/", views.borrow_records, name="borrow_records"),
    path("loans/new/", views.borrow_create, name="borrow_create"),
    path("loans/<int:pk>/return/", views.borrow_return, name="borrow_return"),
    path("loans/<int:pk>/lost/", views.borrow_lost, name="borrow_lost"),
]