#!/usr/bin/env python

from redbot.message import headers
from redbot.speak import Note, categories, levels
from redbot.syntax import rfc7231

class x_ua_compatible(headers.HttpHeader):
    canonical_name = u"X-UA-Compatible"
    reference = u"http://msdn.microsoft.com/en-us/library/cc288325(VS.85).aspx"
    syntax = rfc7231.parameter
    list_header = False
    deprecated = False
    valid_in_requests = False
    valid_in_responses = True

    def parse(self, field_value, add_note):
        try:
            attr, attr_value = field_value.split("=", 1)
        except ValueError:
            attr = field_value
            attr_value = None
        return attr, attr_value

    def evaluate(self, add_note):
        directives = {}
        warned = False
        attr, attr_value = self.value
        if directives.has_key(attr) and not warned:
            add_note(UA_COMPATIBLE_REPEAT)
            warned = True
        directives[attr] = attr_value
        add_note(UA_COMPATIBLE)



class UA_COMPATIBLE(Note):
    category = categories.GENERAL
    level = levels.INFO
    summary = u"%(response)s explicitly sets a rendering mode for Internet Explorer 8."
    text = u"""\
Internet Explorer 8 allows responses to explicitly set the rendering mode used for a given page
(known a the "compatibility mode").

See [Microsoft's documentation](http://msdn.microsoft.com/en-us/library/cc288325(VS.85).aspx) for
more information."""

class UA_COMPATIBLE_REPEAT(Note):
    category = categories.GENERAL
    level = levels.BAD
    summary = u"%(response)s has multiple X-UA-Compatible directives targeted at the same UA."
    text = u"""\
Internet Explorer 8 allows responses to explicitly set the rendering mode used for a page.

This response has more than one such directive targetted at one browser; this may cause
unpredictable results.

See [this blog entry](http://msdn.microsoft.com/en-us/library/cc288325(VS.85).aspx) for more
information."""



class BasicUACTest(headers.HeaderTest):
    name = 'X-UA-Compatible'
    inputs = ['foo=bar']
    expected_out = (u"foo", u"bar")
    expected_err = [UA_COMPATIBLE]
