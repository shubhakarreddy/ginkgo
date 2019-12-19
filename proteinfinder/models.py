from django.db import models

class Samples(models.Model):
    sample_id = models.CharField(max_length=100, unique=True)
    last_used = models.DateTimeField()

# Create your models here.
class Proteins(models.Model):
    sample = models.ForeignKey(Samples, on_delete=models.CASCADE)
    protein_id = models.CharField(max_length=100, unique=True)
    protein_seq = models.TextField(default='')
    start_pos = models.IntegerField()
    end_pos = models.IntegerField()

class Status(models.TextChoices):
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    NO_MATCH = 'NO MATCHES FOUND'

class Searches(models.Model):
    cookie_id = models.CharField(max_length=100, default='', db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)
    dna_seq = models.TextField(default='')
    sample_id = models.CharField(max_length=100)
    protein_id = models.CharField(max_length=100)
    protein_pos = models.IntegerField(default=-1)
