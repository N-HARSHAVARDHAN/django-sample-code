from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    banner_pic = models.ImageField(upload_to='banner/', blank=True,null=True)
    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    following = models.ManyToManyField('self',symmetrical = False , related_name = 'followers', blank = True)