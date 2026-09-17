from django.conf import settings
from django.db import models


class TeamManager(models.Manager):
    def get_current(self):
        team_id = getattr(settings, "CURRENT_TEAM_ID", None)
        if team_id is None:
            raise self.model.DoesNotExist(
                "CURRENT_TEAM_ID must be set when no request context is available."
            )
        return self.get(pk=team_id)


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    objects = TeamManager()

    def __str__(self):
        return self.name


class TeamResource(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="resources")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
