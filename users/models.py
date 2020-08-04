from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from fixpol.models import Location, Impact

# Create your models here.
class Profile(models.Model):
    class Meta:
        app_label = 'users'
    """A profile holds the location and impact areas."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, 
        related_name='profile')

    loc = models.ForeignKey('fixpol.Location', null=True,
        related_name='profloc', on_delete=models.SET_NULL)

    areas = models.ManyToManyField(Impact)

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
