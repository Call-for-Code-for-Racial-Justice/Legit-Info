from django.db import models

# Create your models here.
class Location(models.Model):
    """A location helps filter which legislation to look at."""
    desc = models.CharField(max_length=80)
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
