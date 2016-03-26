#!/usr/bin/env python

"""
Text Formatter for REDbot.
"""


from HTMLParser import HTMLParser
import operator
import re
import textwrap

import thor.http.error as httperr
import redbot.speak as rs

from redbot.formatter import Formatter

nl = u"\n"

# TODO: errors and status on stderr with CLI?

class BaseTextFormatter(Formatter):
    """
    Base class for text formatters."""
    media_type = "text/plain"

    note_categories = [
        rs.c.GENERAL, rs.c.SECURITY, rs.c.CONNECTION, rs.c.CONNEG,
        rs.c.CACHING, rs.c.VALIDATION, rs.c.RANGE
    ]

    link_order = [
          ('link', 'Head Links'),
          ('script', 'Script Links'),
          ('frame', 'Frame Links'),
          ('iframe', 'IFrame Links'),
          ('img', 'Image Links'),
    ]

    error_template = "Error: %s\n"

    def __init__(self, *args, **kw):
        Formatter.__init__(self, *args, **kw)
        self.verbose = False

    def start_output(self, test_uri, req_hdrs):
        pass

    def feed(self, state, chunk):
        pass

    def status(self, msg):
        pass

    def finish_output(self):
        "Fill in the template with RED's results."
        exchange_state = self.test_state.get_exchange(None)
        if exchange_state.response.complete:
            self.output(self.format_headers(exchange_state) + nl + nl)
            self.output(self.format_recommendations(exchange_state) + nl)
        else:
            if exchange_state.response.http_error == None:
                pass
            elif isinstance(exchange_state.response.http_error, httperr.HttpError):
                self.output(self.error_template % \
                            exchange_state.response.http_error.desc)
            else:
                raise AssertionError, "Unknown incomplete response error."

    def format_headers(self, exchange_state):
        out = [u"HTTP/%s %s %s" % (
                exchange_state.response.version, 
                exchange_state.response.status_code, 
                exchange_state.response.status_phrase
        )]
        return nl.join(out + [u"%s:%s" % h for h in exchange_state.response.headers])

    def format_recommendations(self, exchange_state):
        return "".join([self.format_recommendation(exchange_state, category) \
            for category in self.note_categories])

    def format_recommendation(self, exchange_state, category):
        notes = [note for note in exchange_state.notes if note.category == category]
        if not notes:
            return ""
        out = []
        if [note for note in notes]:
            out.append(u"* %s:" % category)
        for m in notes:
            out.append(
                u"  * %s" % (self.colorize(m.level, m.show_summary("en")))
            )
            if self.verbose:
                out.append('')
                out.extend('    ' + line for line in self.format_text(m))
                out.append('')
            smsgs = [note for note in getattr(m.subrequest, "notes", []) 
                     if note.level in [rs.l.BAD]]
            if smsgs:
                out.append("")
                for sm in smsgs:
                    out.append(
                        u"    * %s" %
                        (self.colorize(sm.level, sm.show_summary("en")))
                    )
                    if self.verbose:
                        out.append('')
                        out.extend('     ' + ln for ln in self.format_text(sm))
                        out.append('')
                out.append(nl)
        out.append(nl)
        return nl.join(out)

    def format_text(self, m):
        return textwrap.wrap(
            strip_tags(
                re.sub(
                    r"(?m)\s\s+", 
                    " ", 
                    m.show_text("en")
                )
            )
        )

    def colorize(self, level, string):
        if self.kw.get('tty_out', False):
            # info
            color_start = u"\033[0;32m"
            color_end   = u"\033[0;39m"
            if level == "good":
                color_start = u"\033[1;32m"
                color_end   = u"\033[0;39m"
            if level == "bad":
                color_start = u"\033[1;31m"
                color_end   = u"\033[0;39m"
            if level == "warning":
                color_start = u"\033[1;33m"
                color_end   = u"\033[0;39m"
            if level == "uri":
                color_start = u"\033[1;34m"
                color_end   = u"\033[0;39m"
            return color_start + string + color_end
        else:
            return string



class TextFormatter(BaseTextFormatter):
    """
    Format a RED object as text.
    """
    name = "txt"
    media_type = "text/plain"

    def __init__(self, *args, **kw):
        BaseTextFormatter.__init__(self, *args, **kw)

    def finish_output(self):
        BaseTextFormatter.finish_output(self)
        self.done()


class VerboseTextFormatter(TextFormatter):
    name = 'txt_verbose'

    def __init__(self, *args, **kw):
        TextFormatter.__init__(self, *args, **kw)
        self.verbose = True


class TextListFormatter(BaseTextFormatter):
    """
    Format multiple RED responses as a textual list.
    """
    name = "txt"
    media_type = "text/plain"
    can_multiple = True

    def __init__(self, *args, **kw):
        BaseTextFormatter.__init__(self, *args, **kw)

    def finish_output(self):
        "Fill in the template with RED's results."
        BaseTextFormatter.finish_output(self)
        sep = "=" * 78
        for hdr_tag, heading in self.link_order:
            droids = [d[0] for d in self.state.linked if d[1] == hdr_tag]
            self.output("%s\n%s (%d)\n%s\n" % (
                sep, heading, len(droids), sep
            ))
            if droids:
                droids.sort(key=operator.attrgetter('uri'))
                for droid in droids:
                    self.output(self.format_uri(droid) + nl + nl)
                    self.output(self.format_headers(droid) + nl + nl)
                    self.output(self.format_recommendations(droid) + nl + nl)
        self.done()

    def format_uri(self, state):
        return self.colorize("uri", state.request.uri)


class VerboseTextListFormatter(TextListFormatter):
    name = "txt_verbose"

    def __init__(self, *args, **kw):
        TextListFormatter.__init__(self, *args, **kw)
        self.verbose = True


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
