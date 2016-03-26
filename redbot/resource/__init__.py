#!/usr/bin/env python

"""
The Resource Expert Droid.

RED will examine a HTTP resource for problems and other interesting
characteristics, making a list of these observation notes available
for presentation to the user. It does so by potentially making a number
of requests to probe the resource's behaviour.

See webui.py for the Web front-end.
"""

from urlparse import urljoin

from redbot.resource.fetch import RedFetcher, UA_STRING
from redbot.formatter import f_num
from redbot.resource import active_check
from redbot.state import RedState


class HttpResource(RedFetcher):
    """
    Given a URI (optionally with method, request headers and body), as well
    as an optional status callback and list of body processors, examine the
    URI for issues and notable conditions, making any necessary additional
    requests.

    Note that this primary request negotiates for gzip content-encoding;
    see ConnegCheck.

    After processing the response-specific attributes of RedFetcher will be
    populated, as well as its notes; see that class for details.
    """
    def __init__(self, test_state, uri, method="GET", req_hdrs=None, req_body=None,
                status_cb=None, body_procs=None, descend=False):
        RedFetcher.__init__(self, test_state, None, uri, method, req_hdrs, req_body,
                            status_cb, body_procs)
        self.descend = descend
        self.response.set_link_procs([self.process_link])

    def done(self):
        """
        Response is available; perform further processing that's specific to
        the "main" response.
        """
        if self.response.complete:
            active_check.spawn_all(self)

    def process_link(self, base, link, tag, title):
        "Handle a link from content"
        if not self.test_state.links.has_key(tag):
            self.test_state.links[tag] = set()
        if self.descend and tag not in ['a'] and link not in self.test_state.links[tag]:
            linked_state = RedState()
            linked = HttpResource(
                linked_state,
                urljoin(base, link),
                req_hdrs=self.request.headers,
                status_cb=self.status_cb,
            )
            self.test_state.linked.append((linked_state, tag))
            self.add_task(linked.run)
        self.test_state.links[tag].add(link)
        if not self.response.base_uri:
            self.response.base_uri = base


if __name__ == "__main__":
    import sys
    from redbot.state import RedState
    def status_p(msg):
        'print the status message'
        print msg
    state = RedState()
    RED = HttpResource(state, sys.argv[1], status_cb=status_p)
    RED.run()
    print state.notes
