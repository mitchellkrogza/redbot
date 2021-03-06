#!/usr/bin/env python


from redbot.message import headers
from redbot.speak import Note, categories, levels
from redbot.syntax import rfc7232

class last_modified(headers.HttpHeader):
    canonical_name = u"Last-Modified"
    description = u"""\
The `Last-Modified` header indicates the time that the origin server believes the
representation was last modified."""
    reference = u"%s#header.last_modified" % rfc7232.SPEC_URL
    syntax = False # rfc7232.Last_Modified
    list_header = False
    deprecated = False
    valid_in_requests = False
    valid_in_responses = True

    def parse(self, field_value, add_note):
        try:
            date = headers.parse_date(field_value, add_note)
        except ValueError:
            raise
        return date


class BasicLMTest(headers.HeaderTest):
    name = 'Last-Modified'
    inputs = ['Mon, 04 Jul 2011 09:08:06 GMT']
    expected_out = 1309770486
    expected_err = []

class BadLMTest(headers.HeaderTest):
    name = 'Last-Modified'
    inputs = ['0']
    expected_out = None
    expected_err = [headers.BAD_DATE_SYNTAX]

class BlankLMTest(headers.HeaderTest):
    name = 'Last-Modified'
    inputs = ['']
    expected_out = None
    expected_err = [headers.BAD_DATE_SYNTAX]
