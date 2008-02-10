from django.conf import settings
from django.core.urlresolvers import get_callable
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect


from spindrop.django.openid import util
from spindrop.django.openid.util import DjangoOpenIDStore, getViewURL

from openid.consumer import consumer
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import sreg

def getConsumer(request):
    """
    Get a Consumer object to perform OpenID authentication.
    """
    return consumer.Consumer(request.session, DjangoOpenIDStore())


def begin(request):
    """
    Begin the OpenID process:
    * render and process form
    * show errors
    """
    form_template = 'openid/login.html'
 
    if request.POST:
        openid_url = request.POST['openid_url']
        c          = getConsumer(request)
        error      = None
        
        try:
            auth_request = c.begin(openid_url)
        except DiscoveryFailure, e:
            error = "Open ID error: %s" % str(e)
            return render_to_response(form_template, {"openid_error": error})
        sreg_request = sreg.SRegRequest(optional=['email', 'nickname'])
        auth_request.addExtension(sreg_request)
        trust_root = getViewURL(request, begin)
        return_to  = getViewURL(request, finish)
        url        = auth_request.redirectURL(trust_root, return_to)
        return HttpResponseRedirect(url)
   
    return render_to_response(form_template, context_instance=RequestContext(request))


 
def finish(request):
    """
    Finish the OpenID authentication process.  Invoke the OpenID
    library with the response from the OpenID server and render a page
    detailing the result.
    """

    request_args = util.normalDict(request.GET)

    if request.method == 'POST':
        request_args.update(util.normalDict(request.POST))
        
    result = {} 
    
    if request_args:
        c = getConsumer(request)

        # Get a response object indicating the result of the OpenID
        # protocol.
        return_to = util.getViewURL(request, finish)
        response  = c.complete(request_args, return_to)

        # Get a Simple Registration response object if response
        # information was included in the OpenID response.
        sreg_response = {}
        if response.status == consumer.SUCCESS:
            sreg_response = sreg.SRegResponse.fromSuccessResponse(response)

        # Map different consumer status codes to template contexts.
        results = {
            consumer.CANCEL:
            {'message': 'OpenID authentication cancelled.'},

            consumer.FAILURE:
            {'error': 'OpenID authentication failed.'},

            consumer.SUCCESS:
            {
                'url': response.getDisplayIdentifier(),
                'sreg': sreg_response.items()
            },
        }

        result = results[response.status]

        if isinstance(response, consumer.FailureResponse):
            # In a real application, this information should be
            # written to a log for debugging/tracking OpenID
            # authentication failures. In general, the messages are
            # not user-friendly, but intended for developers.
            result['failure_reason'] = response.message
        else:
            if settings.OPENID_SUCCESS:
                view = get_callable(settings.OPENID_SUCCESS)
                return view(request, result)
        
    return render_to_response("openid/results.html", result, context_instance=RequestContext(request))
