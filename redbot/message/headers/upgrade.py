#!/usr/bin/env python

from redbot.message import headers
from redbot.speak import Note, categories, levels
from redbot.syntax import rfc7230

class upgrade(headers.HttpHeader):
    canonical_name = u"Upgrade"
    description = u"""\
The `Upgrade` header allows the client to specify what additional communication
protocols it supports and would like to use if the server finds it appropriate
to switch protocols. Servers use it to confirm upgrade to a specific
protocol."""
    reference = u"%s#header.upgrade" % rfc7230.SPEC_URL
    syntax = rfc7230.Upgrade
    list_header = True
    deprecated = False
    valid_in_requests = True
    valid_in_responses = True
