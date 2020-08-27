from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from fixpol.models import Impact, Criteria

# Create your models here.


class Profile(models.Model):
    """A profile holds the location and impact areas."""
    class Meta:
        app_label = 'users'

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')

    location = models.ForeignKey('fixpol.Location', null=True,
                                 related_name='profiles', on_delete=models.SET_NULL)

    impacts = models.ManyToManyField(Impact)

    criteria = models.ForeignKey('fixpol.Criteria', null=True,
                                 related_name='profiles', on_delete=models.SET_NULL)

    def __str__(self):
        """Return a string representation of the model."""
        return f'{self.user.username}'

    def set_criteria(self):
        """Create or update criteria record for this profile."""

        crit = self.criteria
        if crit:
            crit.location = self.location
            selected = self.impacts.all()
            for impact in Impact.objects.all():
                if impact in selected:
                    crit.impacts.add(impact)
                else:
                    crit.impacts.remove(impact)
        else:
            crit = Criteria(location=self.location)
            crit.save()
            for impact in self.impacts.all():
                crit.impacts.add(impact)

        crit.set_text()
        crit.save()
        self.criteria = crit
        self.save()

        return self


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
