from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, timedelta
from core.models import Doctor, Slot, Profile


class Command(BaseCommand):
    help = "Seed demo doctors, slots, and an admin account for HospitalMS"

    def _normalize_username(self, name):
        base = name.strip().lower()
        base = base.replace('.', '')
        base = base.replace(' ', '_')
        base = ''.join(ch for ch in base if ch.isalnum() or ch == '_')
        return base or 'doctor'

    def _realistic_names_for_specialty(self, specialty):
        specialty_names = {
            'General Practice': ['Dr. Amara Okafor', 'Dr. Kevin Kibet', 'Dr. Nancy Muthoni'],
            'Pediatrics': ['Dr. Wanjiru Kamau', 'Dr. Sarah Njeri', 'Dr. Peter Kibet'],
            'Cardiology': ['Dr. Daniel Mwangi', 'Dr. Grace Wanjiru', 'Dr. Peter Kiplagat'],
            'Dermatology': ['Dr. Leah Otieno', 'Dr. Joan Wambui', 'Dr. Brian Mugo'],
            'Gynecology': ['Dr. Grace Kiptoo', 'Dr. Hellen Akinyi', 'Dr. Faith Mumo'],
            'Dentistry': ['Dr. Otieno Ochieng', 'Dr. Amina Yusuf', 'Dr. Brian Njoroge', 'Dr. Kelvin Mutua', 'Dr. Esther Kimani'],
            'Dentist': ['Dr. Alice Mwangi', 'Dr. Brian Otieno', 'Dr. Catherine Njoroge', 'Dr. Daniel Kariuki'],
            'General Medicine': ['Dr. Jaden Afrika', 'Dr. Rare Tryph', 'Dr. Kayla Omollo', 'Dr. Triple G'],
            'Physical Therapy': ['Dr. Omollo Opil', 'Dr. Rose Wairimu', 'Dr. Martin Muriithi'],
            'Neurology': ['Dr. Mercy Wambui', 'Dr. Isaac Chege', 'Dr. Ann Wanjiku'],
        }
        return specialty_names.get(specialty, ['Dr. Alice Mwangi', 'Dr. Brian Otieno', 'Dr. Catherine Njoroge', 'Dr. Daniel Kariuki'])

    def _get_unique_realistic_name(self, specialty, used_names=None):
        used_names = set(used_names or [])
        for candidate in self._realistic_names_for_specialty(specialty):
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate

        first_names = ['Alice', 'Brian', 'Catherine', 'Daniel', 'Esther', 'Faith', 'Grace', 'Henry', 'Irene', 'John']
        last_names = ['Mwangi', 'Njoroge', 'Otieno', 'Kiptoo', 'Kariuki', 'Wambui', 'Wanjiku', 'Kibet', 'Mugo', 'Muriithi']
        counter = 0
        while True:
            candidate = f"Dr. {first_names[counter % len(first_names)]} {last_names[(counter // len(first_names)) % len(last_names)]}"
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            counter += 1

    def _looks_like_placeholder_name(self, name):
        lowered = (name or '').lower()
        return any(token in lowered for token in ['extra', 'specialist', 'placeholder', 'cardiologist'])

    def _placeholder_replacement_name(self, name):
        replacements = {
            'dr afrika': 'Dr. Asha Mugo',
            'jaden afrika': 'Dr. Jaden Waweru',
            'rare tryph': 'Dr. Ruth Nyambura',
            'kayla omollo': 'Dr. Kayla Njeri',
            'triple g': 'Dr. Titus Gachanja',
            'omollo opil': 'Dr. Paul Omondi',
        }
        return replacements.get((name or '').strip().lower())

    def handle(self, *args, **options):
        today = timezone.localdate()

        doctors_data = [
            {"name": "Dr. Amara Okafor", "specialty": "General Practice"},
            {"name": "Dr. Wanjiru Kamau", "specialty": "Pediatrics"},
            {"name": "Dr. Daniel Mwangi", "specialty": "Cardiology"},
            {"name": "Dr. Leah Otieno", "specialty": "Dermatology"},
            {"name": "Dr. Grace Kiptoo", "specialty": "Gynecology"},
            {"name": "Dr. Otieno Ochieng", "specialty": "Dentistry"},
            {"name": "Dr. Amina Yusuf", "specialty": "Dentistry"},
            {"name": "Dr. Brian Njoroge", "specialty": "Dentistry"},
            {"name": "Dr. Faith Mumo", "specialty": "Dentistry"},
            {"name": "Dr. Kelvin Mutua", "specialty": "Dentistry"},
        ]

        doctors = []
        for data in doctors_data:
            doctor, created = Doctor.objects.get_or_create(
                name=data["name"], defaults={"specialty": data["specialty"]}
            )
            doctors.append(doctor)
        # Ensure each specialty has at least 5 doctors. Collect specialties from
        # the seed list and existing doctors.
        seed_specialties = {d["specialty"] for d in doctors_data}
        existing_specialties = set(Doctor.objects.exclude(specialty='').values_list('specialty', flat=True))
        specialties = list(seed_specialties | existing_specialties)

        existing_names = set(Doctor.objects.exclude(name='').values_list('name', flat=True))
        for doctor in Doctor.objects.all():
            replacement_name = self._placeholder_replacement_name(doctor.name)
            if replacement_name:
                if replacement_name not in existing_names:
                    doctor.name = replacement_name
                    doctor.save(update_fields=['name'])
                    existing_names.add(replacement_name)
                continue

            if self._looks_like_placeholder_name(doctor.name):
                new_name = self._get_unique_realistic_name(doctor.specialty or 'General Practice', existing_names - {doctor.name})
                doctor.name = new_name
                doctor.save(update_fields=['name'])
                existing_names.add(new_name)

        for specialty in specialties:
            count = Doctor.objects.filter(specialty=specialty).count()
            needed = max(0, 5 - count)
            for _ in range(needed):
                name = self._get_unique_realistic_name(specialty, existing_names)
                existing_names.add(name)
                doctor, created = Doctor.objects.get_or_create(name=name, defaults={"specialty": specialty})
                if created:
                    self.stdout.write(f"Created doctor to fill specialty {specialty}: {doctor.name}")

        # Normalize and ensure each doctor has a unique, name-based username and a Profile
        for doctor in Doctor.objects.order_by('id'):
            base_username = self._normalize_username(doctor.name)

            # Find or create a user for this doctor, ensuring username uniqueness.
            existing_user = doctor.user

            # Determine a unique username that either reuses the existing one (if owned),
            # or finds a free variant based on the name.
            username = base_username
            counter = 1
            while True:
                conflict_qs = User.objects.filter(username=username)
                if existing_user:
                    # Allow the existing linked user to keep their username if it's the same
                    conflict = conflict_qs.exclude(pk=existing_user.pk).exists()
                else:
                    conflict = conflict_qs.exists()

                if not conflict:
                    break
                username = f"{base_username}_{counter}"
                counter += 1

            if existing_user:
                if existing_user.username != username:
                    existing_user.username = username
                    existing_user.save(update_fields=["username"])
                user = existing_user
            else:
                user, user_created = User.objects.get_or_create(username=username)
                if user_created:
                    user.set_password("12345678")
                    user.save(update_fields=["password"])

            # Ensure password is set to the demo password
            if not user.check_password("12345678"):
                user.set_password("12345678")
                user.save(update_fields=["password"])

            # Link user to doctor if not already linked
            if not doctor.user_id or doctor.user_id != user.id:
                doctor.user = user
                doctor.save(update_fields=["user"])

            # Ensure doctor specialty is set
            if not doctor.specialty:
                # Assign a specialty in round-robin from the known specialties
                doctor.specialty = specialties[doctor.id % len(specialties)]
                doctor.save(update_fields=["specialty"])

            # Create profile if missing
            if not Profile.objects.filter(user=user).exists():
                Profile.objects.create(user=user, role="doctor", phone="")

            self.stdout.write(f"Ensured doctor account: {doctor.name} ({user.username}/12345678) - {doctor.specialty}")

        # Include doctors that were created outside this command as well, so every
        # doctor shown to patients has bookable availability.
        doctors = Doctor.objects.order_by('name')
        days_to_seed = 30
        start_hour = 9
        slots_created = 0
        for day_offset in range(days_to_seed):
            slot_date = today + timedelta(days=day_offset)
            for doctor in doctors:
                for hour in range(start_hour, start_hour + 6):
                    _, created = Slot.objects.get_or_create(
                        doctor=doctor,
                        date=slot_date,
                        start_time=time(hour=hour),
                        defaults={"is_booked": False},
                    )
                    slots_created += created
        self.stdout.write(
            f"Seeded {slots_created} available slots for {doctors.count()} doctors "
            f"over the next {days_to_seed} days."
        )

        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_user(
                username="admin", password="adminpass123"
            )
            Profile.objects.create(user=admin_user, role="admin", phone="")
            self.stdout.write("Created admin account: admin / adminpass123")
        else:
            self.stdout.write("Admin account admin already exists")

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
