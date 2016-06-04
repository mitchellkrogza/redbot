#!/usr/bin/env python

import redbot.speak as rs

description = u"""\
The `Connection` header allows senders to specify which headers are hop-by-hop; that is, those that
are not forwarded by intermediaries.

It also indicates options that are desired for this particular connection; e.g., `close` means that
it should not be reused."""

reference = u"%s#header.connection" % rs.rfc7230