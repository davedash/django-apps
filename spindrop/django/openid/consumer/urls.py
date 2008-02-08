from django.conf.urls.defaults import *

urlpatterns = patterns('spindrop.django.openid.consumer.views',
    (r'^$', 'begin'),
    (r'^finish/$', 'finish'),
)
