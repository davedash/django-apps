import time, base64, md5

from urlparse import urljoin

from django.core.urlresolvers import reverse as reverseURL

from openid.association import Association as OIDAssociation
from openid.store import nonce
from openid.store.interface import OpenIDStore

from consumer.models import Association, Nonce
from django.conf import settings

class DjangoOpenIDStore(OpenIDStore):
    """
    This is derived from Django-OpenID http://code.google.com/p/django-openid/
    by Simon Willison
    """
    def __init__(self):
        self.max_nonce_age = 6 * 60 * 60 # Six hours
    
    def storeAssociation(self, server_url, association):
        assoc = Association(
            server_url = server_url,
            handle = association.handle,
            secret = base64.encodestring(association.secret),
            issued = association.issued,
            lifetime = association.issued,
            assoc_type = association.assoc_type
        )
        assoc.save()
    
    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = Association.objects.filter(
                server_url = server_url, handle = handle
            )
        else:
            assocs = Association.objects.filter(
                server_url = server_url
            )
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, base64.decodestring(assoc.secret), assoc.issued,
                assoc.lifetime, assoc.assoc_type
            )
            if association.getExpiresIn() == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]
    
    def removeAssociation(self, server_url, handle):
        assocs = list(Association.objects.filter(
            server_url = server_url, handle = handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist
    
    
    def useNonce(self, server_url, timestamp, salt):
        """Called when using a nonce.

        This method should return C{True} if the nonce has not been
        used before, and store it for a while to make sure nobody
        tries to use the same value again.  If the nonce has already
        been used or the timestamp is not current, return C{False}.

        You may use L{openid.store.nonce.SKEW} for your timestamp window.

        @change: In earlier versions, round-trip nonces were used and
           a nonce was only valid if it had been previously stored
           with C{storeNonce}.  Version 2.0 uses one-way nonces,
           requiring a different implementation here that does not
           depend on a C{storeNonce} call.  (C{storeNonce} is no
           longer part of the interface.)

        @param server_url: The URL of the server from which the nonce
            originated.

        @type server_url: C{str}

        @param timestamp: The time that the nonce was created (to the
            nearest second), in seconds since January 1 1970 UTC.
        @type timestamp: C{int}

        @param salt: A random string that makes two nonces from the
            same server issued during the same second unique.
        @type salt: str

        @return: Whether or not the nonce was valid.

        @rtype: C{bool}
        """
        
        if abs(timestamp - time.time()) > nonce.SKEW:
            return False

        try:
            n = Nonce(timestamp=timestamp, server_url=server_url, salt=salt)
            n.save()
        except:
            # The key uniqueness check failed
            return False

        return True
        
        
    def getAuthKey(self):
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        return md5.new(settings.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]
    
    def isDumb(self):
        return False

   

def getViewURL(req, view_name_or_obj, args = None, kwargs=None):
    relative_url                           = reverseURL(view_name_or_obj, args=args, kwargs=kwargs)
    full_path                              = settings.get('LOGIN_HOST', '') + relative_url

    return urljoin(getBaseURL(req), full_path)


def getBaseURL(req):
    """
    Given a Django web request object, returns the OpenID 'trust root'
    for that request; namely, the absolute URL to the site root which
    is serving the Django request.  The trust root will include the
    proper scheme and authority.  It will lack a port if the port is
    standard (80, 443).
    """
    
    name = req.META['HTTP_HOST']
    
    try:
        name = name[:name.index(':')]
    except:
        pass

    try:
        port = int(req.META['SERVER_PORT'])
    except:
        port = 80

    proto = req.META['SERVER_PROTOCOL']

    if 'HTTPS' in proto:
        proto = 'https'
    else:
        proto = 'http'

    if port in [80, 443] or not port:
        port = ''
    else:
        port = ':%s' % (port,)

    url = "%s://%s%s/" % (proto, name, port)
    return url


def normalDict(request_data):
    """
    Converts a django request MutliValueDict (e.g., request.GET,
    request.POST) into a standard python dict whose values are the
    first value from each of the MultiValueDict's value lists.  This
    avoids the OpenID library's refusal to deal with dicts whose
    values are lists, because in OpenID, each key in the query arg set
    can have at most one value.
    """
    return dict((k, v) for k, v in request_data.iteritems())

def normalize_openid(openid):
    """
    Once upon a time davedash.livejournal.com was the OpenID not 
    http://davedash.livejournal.com/
    
    This function will convert the latter to the former.
    """
    
    if openid.startswith("http://"):
        openid = openid.replace("http://", "", 1)
    
    return openid.rstrip('/')