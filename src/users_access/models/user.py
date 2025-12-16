import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.db import models


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('staff', 'Staff'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    first_name = models.CharField(max_length=255, null=False, db_index=True)
    last_name = models.CharField(max_length=255, null=False, db_index=True)
    email = models.EmailField(max_length=255, unique=True, null=False, db_index=True)
    password = models.CharField(max_length=255, null=False)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    # User Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', db_index=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    login_count = models.PositiveIntegerField(default=0, db_index=True)

    # Avatar
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

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
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f" {self.first_name} {self.last_name} - ({self.email})"

    class Meta:
        db_table = 'users'
