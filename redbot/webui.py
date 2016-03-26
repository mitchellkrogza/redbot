#!/usr/bin/env python

"""
A Web UI for RED, the Resource Expert Droid.
"""

import cPickle as pickle
import gzip
import locale
import os
from robotparser import RobotFileParser
import sys
import tempfile
from urlparse import urlsplit
import zlib

assert sys.version_info[0] == 2 and sys.version_info[1] >= 6, \
    "Please use Python 2.6 or greater"

import thor
from redbot.cache_file import CacheFile
from redbot.resource import HttpResource, RedFetcher, UA_STRING
from redbot.state import RedState
from redbot.formatter import *
from redbot.formatter import find_formatter, html
from redbot.formatter.html import e_url


### Configuration ##########################################################

# TODO: make language configurable/dynamic
lang = "en"
charset = "utf-8"

# Where to store exceptions; set to None to disable traceback logging
exception_dir = 'exceptions'

# how many seconds to allow it to run for
max_runtime = 60

# Where to keep files for future reference, when users save them. None
# to disable saving.
save_dir = '/var/state/redbot/'

# how long to store things when users save them, in days.
save_days = 30

# URI root for static assets (absolute or relative, but no trailing '/')
html.static_root = 'static'

# directory containing files to append to the front page; None to disable
html.extra_dir = "extra"

# show errors in the browser; boolean
debug = False  # DEBUG_CONTROL

# domains which we reject requests for when they're in the referer.
referer_spam_domains = ['www.youtube.com']

# log when total traffic is bigger than this (in bytes), so we can catch abuse
# None to disable; 0 to log all.
log_traffic = 1024 * 1024 * 8

RedFetcher.robot_cache_dir = "/var/state/robots-txt/" if not debug else False

### End configuration ######################################################


# HTML template for error bodies
error_template = u"""\

<p class="error">
 %s
</p>
"""

try:
    locale.setlocale(locale.LC_ALL, locale.normalize(lang))
except:
    locale.setlocale(locale.LC_ALL, '')


class RedWebUi(object):
    """
    A Web UI for RED.
    """
    def __init__(self, ui_uri, method, query_args, response_start, response_body, response_done):
        self.ui_uri = ui_uri
        self.response_start = response_start
        self.response_body = response_body
        self._response_done = response_done

        test_uri = self.qs_arg(query_args, 'uri', '', True)
        req_hdrs = [tuple(rh.decode(charset, 'replace').split(":", 1))
                    for rh in query_args.get("req_hdr", [])
                    if rh.find(":") > 0
        ]
        output_format = self.qs_arg(query_args, 'format', 'html', True)
        check_type = self.qs_arg(query_args, 'request')
        test_id = self.qs_arg(query_args, 'id')
        descend = self.qs_arg(query_args, 'descend', False)

        self.start = thor.time()
        self.timeout = thor.schedule(max_runtime, self.timeoutError)
        
        if method == "POST" and self.qs_arg(query_args, 'save', False) and save_dir and test_id:
            self.save_test(test_id, descend)
        elif test_id:
            self.load_saved_test(test_id, test_uri, output_format, check_type, descend)
        elif test_uri:
            self.run_test(test_uri, req_hdrs, output_format, check_type, descend)
        else:
            self.show_landing(test_uri, req_hdrs)

    @staticmethod
    def qs_arg(query_args, name, default=None, decode=False):
        arg = query_args.get(name, [default])[0]
        if decode and arg != None:
            return arg.decode(charset, 'replace')
        else:
            return arg

    def save_test(self, test_id, descend):
        """Save a previously run test_id by touching its save file."""
        try:
            # touch the save file so it isn't deleted.
            os.utime(
                os.path.join(save_dir, test_id),
                (
                    thor.time(),
                    thor.time() + (save_days * 24 * 60 * 60)
                )
            )
            location = "?id=%s" % test_id
            if descend:
                location = "%s&descend=True" % location
            self.response_start(
                "303", "See Other", [
                ("Location", location)
            ])
            self.response_body("Redirecting to the saved test page...")
        except (OSError, IOError):
            self.response_start(
                "500", "Internal Server Error", [
                ("Content-Type", "text/html; charset=%s" % charset),
            ])
            # TODO: better error message (through formatter?)
            self.response_body(
                error_template % "Sorry, I couldn't save that."
            )
        self.response_done([])

    def load_saved_test(self, test_id, test_uri, output_format, check_type, descend):
        """Load a saved test by test_id."""
        try:
            fd = gzip.open(os.path.join(
                save_dir, os.path.basename(test_id)
            ))
            mtime = os.fstat(fd.fileno()).st_mtime
        except (OSError, IOError, TypeError, zlib.error):
            self.response_start(
                "404", "Not Found", [
                ("Content-Type", "text/html; charset=%s" % charset),
                ("Cache-Control", "max-age=600, must-revalidate")
            ])
            # TODO: better error page (through formatter?)
            self.response_body(error_template %
                "I'm sorry, I can't find that saved response."
            )
            self.response_done([])
            return
        is_saved = mtime > thor.time()
        try:
            test_state = pickle.load(fd)
        except (pickle.PickleError, IOError, EOFError):
            self.response_start(
                "500", "Internal Server Error", [
                ("Content-Type", "text/html; charset=%s" % charset),
                ("Cache-Control", "max-age=600, must-revalidate")
            ])
            self.response_body(error_template %
                "I'm sorry, I had a problem loading that response."
            )
            self.response_done([])
            return
        finally:
            fd.close()

        formatter = find_formatter(output_format, 'html', descend)(
            self.ui_uri, test_state, check_type, lang,
            self.output, allow_save=(not is_saved), is_saved=True,
            test_id=test_id
        )
        self.response_start(
            "200", "OK", [
            ("Content-Type", "%s; charset=%s" % (
                formatter.media_type, charset)),
            ("Cache-Control", "max-age=3600, must-revalidate")
        ])
        exchange_state = test_state.get_exchange(check_type)
        formatter.start_output(exchange_state.request.uri, exchange_state.request.headers)
        formatter.finish_output()
        self.response_done([])

    def run_test(self, test_uri, req_hdrs, output_format, check_type, descend):
        """Test a URI."""
        if save_dir and os.path.exists(save_dir):
            try:
                fd, path = tempfile.mkstemp(prefix='', dir=save_dir)
                test_id = os.path.split(path)[1]
            except (OSError, IOError): # Don't try to store it.
                test_id = None
        else:
            test_id = None

        test_state = RedState()

        formatter = find_formatter(output_format, 'html', descend)(
            self.ui_uri, test_state, check_type, lang,
            self.output, allow_save=test_id, is_saved=False,
            test_id=test_id, descend=descend
        )

        referers = []
        for hdr, value in req_hdrs:
            if hdr.lower() == 'referer':
                referers.append(value)
        referer_error = None
        if len(referers) > 1:
            referer_error = "Multiple referers not allowed."
        if referers and urlsplit(referers[0]).hostname in referer_spam_domains:
            referer_error = "Referer not allowed."
        if referer_error:
            self.response_start(
                "403", "Forbidden", [
                ("Content-Type", "%s; charset=%s" % (
                    formatter.media_type, charset)),
                ("Cache-Control", "max-age=360, must-revalidate")
            ])
            formatter.start_output(test_uri, req_hdrs)
            self.output(error_template % referer_error)
            self.response_done([])
            return

        if not self.robots_precheck(test_uri):
            self.response_start(
                "502", "Gateway Error", [
                ("Content-Type", "%s; charset=%s" % (formatter.media_type, charset)),
                ("Cache-Control", "max-age=60, must-revalidate")
            ])
            formatter.start_output(test_uri, req_hdrs)
            self.output(error_template % "Forbidden by robots.txt.")
            self.response_done([])
            return

        self.response_start(
            "200", "OK", [
            ("Content-Type", "%s; charset=%s" % (
                formatter.media_type, charset)),
            ("Cache-Control", "max-age=60, must-revalidate")
        ])

        resource = HttpResource(
            test_state,
            test_uri,
            req_hdrs=req_hdrs,
            status_cb=formatter.status,
            body_procs=[formatter.feed],
            descend=descend
        )
        formatter.start_output(test_uri, req_hdrs)

        def done():
            formatter.finish_output()
            self.response_done([])
            if test_id:
                try:
                    tmp_file = gzip.open(path, 'w')
                    pickle.dump(test_state, tmp_file)
                    tmp_file.close()
                except (IOError, zlib.error, pickle.PickleError):
                    pass # we don't cry if we can't store it.
            ti = sum([i.transfer_in for i,t in test_state.linked], test_state.transfer_in)
            to = sum([i.transfer_out for i,t in test_state.linked], test_state.transfer_out)
            if ti + to > log_traffic:
                sys.stderr.write("%iK in %iK out for <%s> (descend %s)" % (
                    ti / 1024,
                    to / 1024,
                    e_url(test_uri),
                    str(descend)
                ))

        resource.run(done)

    def show_landing(self, test_uri, req_hdrs):
        """Show the landing page."""
        formatter = html.BaseHtmlFormatter(
            self.ui_uri, RedState(), None,
            lang, self.output, is_blank=True
        )
        self.response_start(
            "200", "OK", [
            ("Content-Type", "%s; charset=%s" % (
                formatter.media_type, charset)
            ),
            ("Cache-Control", "max-age=300")
        ])
        formatter.start_output(test_uri, req_hdrs)
        formatter.finish_output()
        self.response_done([])

    def robots_precheck(self, iri):
        """
        If we have the robots.txt file available, check it to see if the
        request is permissible.
        
        This does not fetch robots.txt.
        """
        
        fetcher = RedFetcher(RedState(), 'robot', iri)
        uri = fetcher.request.uri
        robots_txt = fetcher.fetch_robots_txt(uri, lambda a:a, network=False)
        if robots_txt == "":
            return True
        checker = RobotFileParser()
        checker.parse(robots_txt.splitlines())
        return checker.can_fetch(UA_STRING.encode('utf-8'), uri)

    def output(self, chunk):
        self.response_body(chunk.encode(charset, 'replace'))

    def timeoutError(self):
        """ Max runtime reached."""
        self.output(error_template % ("RED timeout."))
        self.response_done([])

    def response_done(self, trailers):
        if self.timeout:
            self.timeout.delete()
            self.timeout = None
        self._response_done(trailers)


