from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('GUEST', 'Guest'),
        ('RECEPTIONIST', 'Receptionist'),
        ('ACCOUNTANT', 'Accountant'),
        ('CHEF', 'Chef / Kitchen Lead'),
        ('STORES_MANAGER', 'Stores / Inventory Manager'),
        ('MANAGER', 'General Manager'),
        ('EXECUTIVE', 'Executive / Board'),
    )
    
    # Remove default username field
    username = None 
    
    # Automatically manages +260 and international entries cleanly
    phone_number = PhoneNumberField(unique=True, region="ZM", help_text="Enter number (e.g., +260...)")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='GUEST')
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.phone_number} ({self.get_role_display()})"

