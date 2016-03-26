import cgi
import os
from optparse import OptionParser
import sys
from urlparse import urlsplit

from redbot.webui import RedWebUi
from redbot import __version__
import thor

print "* Thor", thor.__version__

def main(host, port, static_dir):
    """Run RED as a standalone Web server."""

    # load static files
    static_files = {}
    def static_walker(arg, dirname, names):
        for name in names:
            try:
                path = os.path.join(dirname, name)
                if os.path.isdir(path):
                    continue
                uri = os.path.relpath(path, static_dir)
                static_files["/static/%s" % uri] = open(path).read()
            except IOError:
                sys.stderr.write(
                  "* Problem loading %s\n" % path
                )
    os.path.walk(static_dir, static_walker, "")

    def red_handler(x):
        @thor.events.on(x)
        def request_start(method, uri, req_hdrs):
            p_uri = urlsplit(uri)
            if static_files.has_key(p_uri.path):
                x.response_start("200", "OK", []) # TODO: headers
                x.response_body(static_files[p_uri.path])
                x.response_done([])
            elif p_uri.path == "/":
                query_string = cgi.parse_qs(p_uri.query)
                try:
                    RedWebUi('/', method, query_string,
                             x.response_start,
                             x.response_body,
                             x.response_done
                            )
                except RuntimeError:
                    raise
                    sys.stderr.write("""

*** FATAL ERROR
RED has encountered a fatal error which it really, really can't recover from
in standalone server mode. Details follow.

""")
                    except_handler_factory(sys.stderr.write)()
                    sys.stderr.write("\n")
                    thor.stop()
                    sys.exit(1)
            else:
                x.response_start("404", "Not Found", [])
                x.response_done([])

    server = thor.http.HttpServer(host, port)
    server.on('exchange', red_handler)

    try:
        thor.run()
    except KeyboardInterrupt:
        sys.stderr.write("Stopping...\n")
        thor.stop()
    # TODO: logging
    # TODO: extra resources

def standalone_monitor (host, port, static_dir):
    """Fork a process as a standalone Web server and watch it."""
    from multiprocessing import Process
    while True:
        p = Process(target=standalone_main, args=(host, port, static_dir))
        sys.stderr.write("* Starting RED server...\n")
        p.start()
        p.join()
        # TODO: listen to socket and drop privs


if __name__ == "__main__":
    # standalone server
    usage = "Usage: %prog [options] port static_dir"
    version = "RED version %s" % __version__
    option_parser = OptionParser(usage=usage, version=version)
    (options, args) = option_parser.parse_args()
    if len(args) < 2:
        option_parser.error(
            "Please specify a port and a static directory."
        )
    try:
        port = int(args[0])
    except ValueError:
        option_parser.error(
            "Port is not an integer."
        )

    static_dir = args[1]
    sys.stderr.write(
        "Starting standalone server on PID %s...\n" % os.getpid() + \
        "http://localhost:%s/\n" % port
    )

#   import pdb
#   pdb.run('standalone_main("", port, static_dir)')
    main("", port, static_dir)
#   standalone_monitor("", port, static_dir)
