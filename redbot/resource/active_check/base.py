#!/usr/bin/env python

"""
Subrequests to do things like range requests, content negotiation checks,
and validation.

This is the base class for all subrequests.
"""


from redbot.resource.fetch import RedFetcher


class SubRequest(RedFetcher):
    """
    Base class for a subrequest of a "main" HttpResource, made to perform
    additional behavioural tests on the resource.
    """
    def __init__(self, base_resource, name):
        self.base = base_resource
        RedFetcher.__init__(
            self, 
            self.base.test_state,
            name,
            self.base.request.uri, 
            self.base.request.method, 
            self.modify_req_hdrs(list(self.base.request.headers)),
            self.base.request.payload, 
            self.base.status_cb, 
            []
        )
        self.add_note = self.base.exchange_state.add_note
    
    def modify_req_hdrs(self, req_hdrs):
        """
        Usually overridden; modifies the request's headers.
        """
        return req_hdrs
        
    def check_missing_hdrs(self, hdrs, note, subreq_type):
        """
        See if the listed headers are missing in the subrequest; if so,
        set the specified note.
        """
        missing_hdrs = []
        for hdr in hdrs:
            if self.base.response.parsed_headers.has_key(hdr) \
            and not self.response.parsed_headers.has_key(hdr):
                missing_hdrs.append(hdr)
        if missing_hdrs:
            self.add_note('headers', note,
                missing_hdrs=", ".join(missing_hdrs),
                subreq_type=subreq_type
            )

    def preflight(self):
        "Check to see if we need to make this request, by examining base_resource."
        raise NotImplementedError