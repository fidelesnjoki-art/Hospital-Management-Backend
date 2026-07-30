from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Appointment, Doctor, Profile, Slot


class AccountSettingsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Profile
        fields = ('username', 'email', 'phone', 'current_password', 'new_password')

    def validate(self, attrs):
        current_password, new_password = attrs.get('current_password'), attrs.get('new_password')
        if bool(current_password) != bool(new_password):
            raise serializers.ValidationError('Provide both current_password and new_password to change your password.')
        if new_password and not self.instance.user.check_password(current_password):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save(update_fields=['phone'])
        if 'email' in user_data:
            instance.user.email = user_data['email']
        if new_password:
            instance.user.set_password(new_password)
        if user_data or new_password:
            instance.user.save()
        return instance


class DoctorSerializer(serializers.ModelSerializer):
    available_slots = serializers.IntegerField(read_only=True)

    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialty', 'bio', 'photo_url', 'available_slots')


class SlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)

    class Meta:
        model = Slot
        fields = ('id', 'doctor', 'doctor_name', 'date', 'start_time', 'is_booked')


class BookAppointmentSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField()

    def validate_slot_id(self, value):
        if not Slot.objects.filter(id=value).exists():
            raise serializers.ValidationError('Slot not found.')
        return value


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    patient_username = serializers.CharField(source='patient.username', read_only=True)
    scheduled_time = serializers.TimeField(source='slot.start_time', read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = ('id', 'doctor', 'doctor_name', 'patient', 'patient_username', 'date', 'scheduled_time',
                  'status', 'diagnosis', 'treatment', 'created_at', 'completed_at')
        read_only_fields = ('id', 'patient', 'status', 'diagnosis', 'treatment', 'created_at', 'completed_at')


class UpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['pending', 'confirmed', 'completed', 'cancelled'])


class DiagnosisSerializer(serializers.Serializer):
    diagnosis = serializers.CharField(allow_blank=True)


class TreatmentSerializer(serializers.Serializer):
    treatment = serializers.CharField(allow_blank=False)
    diagnosis = serializers.CharField(required=False, allow_blank=True)
