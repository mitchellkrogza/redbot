#!/usr/bin/env python

from redbot.message import headers
from redbot.speak import Note, categories, levels
from redbot.syntax import rfc7233

class content_range(headers.HttpHeader):
    canonical_name = u"Content-Range"
    description = u"""\
The `Content-Range` header is sent with a partial body to specify where in the full body the
partial body should be applied."""
    reference = u"%s#header.content_range" % rfc7233.SPEC_URL
    syntax = rfc7233.Content_Range
    list_header = False
    deprecated = False
    valid_in_requests = False
    valid_in_responses = True

    def parse(self, field_value, add_note):
        # #53: check syntax, values?
        if self.message.status_code not in ["206", "416"]:
            add_note(CONTENT_RANGE_MEANINGLESS)
        return field_value


class CONTENT_RANGE_MEANINGLESS(Note):
    category = categories.RANGE
    level = levels.WARN
    summary = u"%(response)s shouldn't have a Content-Range header."
    text = u"""\
HTTP only defines meaning for the `Content-Range` header in responses with a `206 Partial Content`
or `416 Requested Range Not Satisfiable` status code.

Putting a `Content-Range` header in this response may confuse caches and clients."""



class ContentRangeTest(headers.HeaderTest):
    name = 'Content-Range'
    inputs = ['bytes 1-100/200']
    expected_out = 'bytes 1-100/200'
    expected_err = []
    def set_context(self, message):
        message.status_code = "206"
