import uuid
from django.db import models
from .user import User



class PasswordReset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(User, related_name='password_reset_user', on_delete=models.CASCADE, db_index=True)
    reset_counter = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'password_resets'
        ordering = ['-created_at']

    def __str__(self):
        return self.user.email if self.user else 'None'
