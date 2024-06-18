from django.db import models


from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):

        print(email, password)
        if not email:
            raise ValueError("Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    online_count = models.IntegerField(default=0)
    username = models.CharField(unique=True)
    last_seen = models.DateTimeField()
    show_last_seen = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering=["-last_seen"]
        
        
    def __str__(self):
        return self.email


class Room(models.Model):

    GROUP = "Group"
    PRIVATE = "Private"

    GROUP_TYPE = {
        GROUP: "Group",
        PRIVATE: "Private",
    }

    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    members = models.ManyToManyField(CustomUser, through="GroupMembers", related_name= "members")
    last_updated = models.DateTimeField()
    group_type = models.CharField(
        max_length=7,
        choices=GROUP_TYPE,
        default=GROUP
    )
    
    class Meta:
        ordering = ["-last_updated"]


class Message(models.Model):

    text = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(CustomUser, through="MessageReadBy", related_name="reader")
    reply = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
    forwarded_from = models.ForeignKey('self', null=True, on_delete=models.CASCADE, related_name="forwarded")
    edited = models.BooleanField(default=False)
    delete_for_me = models.BooleanField(default=False)
    
    class Meta:
        ordering=["-created_at"]

    def __str__(self):
        return str(self.id)


class MessageReadBy(models.Model):

    read_on = models.DateTimeField(auto_now_add=True)
    reader = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)


class GroupMembers(models.Model):

    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    joined_on = models.DateTimeField(auto_now_add=True)










