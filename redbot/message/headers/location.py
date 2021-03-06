#!/usr/bin/env python

import re
from urlparse import urljoin

from redbot.message import headers
from redbot.speak import Note, categories, levels
from redbot.syntax import rfc7231, rfc3986

class location(headers.HttpHeader):
    canonical_name = u"Location"
    description = u"""\
The `Location` header is used in `3xx` responses to redirect the recipient to a different location
to complete the request.

In `201 Created``` responses, it identifies a newly created resource."""
    reference = u"%s#header.location" % rfc7231.SPEC_URL
    syntax = rfc7231.Location
    list_header = False
    deprecated = False
    valid_in_requests = False
    valid_in_responses = True

    def parse(self, field_value, add_note):
        if self.message.status_code not in ["201", "300", "301", "302", "303", "305", "307", "308"]:
            add_note(LOCATION_UNDEFINED)
        if not re.match(r"^\s*%s\s*$" % rfc3986.URI, field_value, re.VERBOSE):
            add_note(LOCATION_NOT_ABSOLUTE, full_uri=urljoin(self.message.base_uri, field_value))
        return field_value



class LOCATION_UNDEFINED(Note):
    category = categories.GENERAL
    level = levels.WARN
    summary = u"%(response)s doesn't define any meaning for the Location header."
    text = u"""\
The `Location` header is used for specific purposes in HTTP; mostly to indicate the URI of another
resource (e.g., in redirection, or when a new resource is created).

In other status codes (such as this one) it doesn't have a defined meaning, so any use of it won't
be interoperable.

Sometimes `Location` is confused with `Content-Location`, which indicates a URI for the payload of
the message that it appears in."""

class LOCATION_NOT_ABSOLUTE(Note):
    category = categories.GENERAL
    level = levels.INFO
    summary = u"The Location header contains a relative URI."
    text = u"""\
`Location` was originally specified to contain an absolute, not relative, URI.

It is in the process of being updated, and most clients will work around this.

The correct absolute URI is (probably): `%(full_uri)s`"""


class LocationTest(headers.HeaderTest):
    name = 'Location'
    inputs = ['http://other.example.com/foo']
    expected_out = 'http://other.example.com/foo'
    expected_err = []
    def set_context(self, message):
        message.status_code = "300"
