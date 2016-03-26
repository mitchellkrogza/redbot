import cgi
import os
import sys
import tempfile

from redbot.webui import RedWebUi
import thor


def main():
    """Run RED as a CGI Script."""
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    base_uri = "%s://%s%s%s" % (
      os.environ.has_key('HTTPS') and "https" or "http",
      os.environ.get('HTTP_HOST'),
      os.environ.get('SCRIPT_NAME'),
      os.environ.get('PATH_INFO', '')
    )
    method = os.environ.get('REQUEST_METHOD')
    query_string = cgi.parse_qs(os.environ.get('QUERY_STRING', ""))

    def response_start(code, phrase, res_hdrs):
        sys.stdout.write("Status: %s %s\n" % (code, phrase))
        for k, v in res_hdrs:
            sys.stdout.write("%s: %s\n" % (k, v))
        sys.stdout.write("\n")
        return sys.stdout.write, thor.stop
    def response_done(trailers):
        thor.schedule(0, thor.stop)
    try:
        RedWebUi(base_uri, method, query_string,
                 response_start, sys.stdout.write, response_done)
        thor.run()
    except:
        except_handler_factory(sys.stdout.write)()


# adapted from cgitb.Hook
def except_handler_factory(out=None):
    if not out:
        out = sys.stdout.write

    def except_handler(etype=None, evalue=None, etb=None):
        """
        Log uncaught exceptions and display a friendly error.
        """
        if not etype or not evalue or not etb:
            etype, evalue, etb = sys.exc_info()
        import cgitb
        out(cgitb.reset())
        if exception_dir is None:
            out(error_template % """
    A problem has occurred, but it probably isn't your fault.
    """)
        else:
            import stat
            import traceback
            try:
                doc = cgitb.html((etype, evalue, etb), 5)
            except:                  # just in case something goes wrong
                doc = ''.join(traceback.format_exception(etype, evalue, etb))
            if debug:
                out(doc)
                return
            try:
                while etb.tb_next != None:
                    etb = etb.tb_next
                e_file = etb.tb_frame.f_code.co_filename
                e_line = etb.tb_frame.f_lineno
                ldir = os.path.join(exception_dir, os.path.split(e_file)[-1])
                if not os.path.exists(ldir):
                    os.umask(0000)
                    os.makedirs(ldir)
                (fd, path) = tempfile.mkstemp(
                    prefix="%s_" % e_line, suffix='.html', dir=ldir
                )
                fh = os.fdopen(fd, 'w')
                fh.write(doc)
                fh.close()
                os.chmod(path, stat.S_IROTH)
                out(error_template % """\
A problem has occurred, but it probably isn't your fault.
RED has remembered it, and we'll try to fix it soon.""")
            except:
                out(error_template % """\
A problem has occurred, but it probably isn't your fault.
RED tried to save it, but it couldn't! Oops.<br>
Please e-mail the information below to
<a href='mailto:red@redbot.org'>red@redbot.org</a>
and we'll look into it.""")
                out("<h3>Original Error</h3>")
                out("<pre>")
                out(''.join(traceback.format_exception(etype, evalue, etb)))
                out("</pre>")
                out("<h3>Write Error</h3>")
                out("<pre>")
                out(''.join(traceback.format_exc()))
                out("</pre>")
        sys.exit(1) # We're in an uncertain state, so we must die horribly.

    return except_handler


if __name__ == "__main__":
    if os.environ.has_key('GATEWAY_INTERFACE'):  # CGI
        main()
