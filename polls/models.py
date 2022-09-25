import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Question(models.Model):
    """Question model for creating questions."""
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    end_date = models.DateTimeField('ending date', null=True, blank=True, default=None)

    def was_published_recently(self):
        """Check that poll was published recently."""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def is_published(self):
        """Check that poll was published ."""
        now = timezone.now()
        if now >= self.pub_date:
            return True
        else:
            return False

    def can_vote(self):
        """Check that poll be voted."""
        now = timezone.now()
        if self.end_date is None:
            return now >= self.pub_date
        return self.end_date >= now >= self.pub_date

    def __str__(self):
        """Return question text."""
        return self.question_text


class Choice(models.Model):
    """Choice model for creating choices."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)

    @property
    def votes(self):
        return Vote.objects.filter(choice=self).count()

    def __str__(self):
        """Return choice text."""
        return self.choice_text


class Vote(models.Model):
    """Vote model for check authenticated user vote"""
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    @property
    def question(self):
        return self.choice.question