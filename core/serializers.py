from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Appointment, Doctor, Profile, Slot


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    role = serializers.ChoiceField(choices=['patient', 'doctor'], default='patient')
    phone = serializers.CharField(required=False, allow_blank=True)
    doctor_name = serializers.CharField(required=False, max_length=255)
    specialty = serializers.CharField(required=False, allow_blank=True, max_length=255)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'phone', 'doctor_name', 'specialty', 'full_name')

    def validate(self, attrs):
        if attrs.get('role') == 'doctor' and not attrs.get('doctor_name'):
            raise serializers.ValidationError({'doctor_name': 'This field is required for doctors.'})
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'patient')
        phone = validated_data.pop('phone', '')
        doctor_name = validated_data.pop('doctor_name', '')
        specialty = validated_data.pop('specialty', '')
        full_name = validated_data.pop('full_name', '')
        email = validated_data.get('email', '')
        username = validated_data.pop('username', '') or email.split('@')[0] or 'patient'
        base_username, suffix = username, 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{suffix}'
            suffix += 1
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            first_name=full_name,
        )
        Profile.objects.create(user=user, role=role, phone=phone)
        if role == 'doctor':
            Doctor.objects.create(user=user, name=doctor_name, specialty=specialty)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('id', 'username', 'email', 'full_name', 'role', 'phone')

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


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
