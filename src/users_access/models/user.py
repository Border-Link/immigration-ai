import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.contrib.auth.models import BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager required for Django auth backends.
    ModelBackend expects `_default_manager.get_by_natural_key(...)`.
    """

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    User model - Authentication and authorization only.
    PII data is stored in UserProfile model for GDPR compliance.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('reviewer', 'Reviewer'),  # Added reviewer role from spec
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    
    # Authentication
    email = models.EmailField(max_length=255, unique=True, null=False, db_index=True)
    password = models.CharField(max_length=255, null=False)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    # User Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', db_index=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False, db_index=True)
    login_count = models.PositiveIntegerField(default=0, db_index=True)
    
    # Reviewer assignment tracking (from implementation spec)
    last_assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Last time reviewer was assigned a review (for round-robin assignment)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # User Groups & Permissions
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='custom_user_group',
        related_query_name='user',
        db_index=True
    )

    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='custom_user_permissions',
        related_query_name='user',
        db_index=True
    )

    USERNAME_FIELD = 'email'
    objects = UserManager()

    def __str__(self):
        return f"User ({self.email})"