from django.db import models

class Test(models.Model):
    pub_date = models.DateTimeField('date published')
