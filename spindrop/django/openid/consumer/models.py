from django.db import models

class Nonce(models.Model):
    """
    This is derived from Django-OpenID http://code.google.com/p/django-openid/
    by Simon Willison
    """
    server_url      = models.CharField(max_length=128)
    timestamp       = models.IntegerField()
    salt            = models.CharField(max_length=40)

    class Meta:
        unique_together = (("server_url", "timestamp", "salt"),)
    
class Association(models.Model):
    """
    This is derived from Django-OpenID http://code.google.com/p/django-openid/
    by Simon Willison
    """
    
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255) # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)
    def __str__(self):
        return "Association: %s, %s" % (self.server_url, self.handle)
