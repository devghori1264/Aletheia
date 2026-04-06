"""
User models for Aletheia accounts.

Provides custom user model with extended functionality.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """Custom manager for User model."""
    
    pass


class User(AbstractUser):
    """
    Custom user model for Aletheia.
    
    Extends Django's AbstractUser with additional fields and functionality.
    """
    
    objects = UserManager()
    
    class Meta:
        db_table = "aletheia_users"
        verbose_name = "user"
        verbose_name_plural = "users"
    
    def __str__(self) -> str:
        return self.username or self.email


__all__ = ["User", "UserManager"]
