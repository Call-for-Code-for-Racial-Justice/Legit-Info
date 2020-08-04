from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Location(models.Model):
    """A location helps filter which legislation to look at."""
    desc = models.CharField(max_length=80)
    shortname = models.CharField(max_length=20)
    hierarchy = models.CharField(max_length=200)
    govlevel = models.CharField(max_length=80)
    parent = models.ForeignKey('self', null=True, 
            related_name='child', on_delete=models.PROTECT)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.desc

class Impact(models.Model):
    """A location helps filter which legislation to look at."""
    text = models.CharField(max_length=80)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text

class Profile(models.Model):
    """A profile holds the location and impact areas."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, 
        related_name='profile')

    location = models.ForeignKey('Location', null=True,
        related_name='location', on_delete=models.SET_NULL)

    impacts = models.ManyToManyField(Impact)

    def __str__(self):
        """Return a string representation of the model."""
        return f'{self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()




