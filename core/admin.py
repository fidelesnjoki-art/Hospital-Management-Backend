from django.contrib import admin

from .models import Appointment, Doctor, Profile, Slot


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'specialty')


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'date', 'start_time', 'is_booked')
    list_filter = ('doctor', 'date', 'is_booked')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date', 'status')
    list_filter = ('doctor', 'date', 'status')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'phone')
