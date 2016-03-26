
import cgi

from mod_python import apache

from redbot.webui import RedWebUi
import thor


def mod_python_handler(r):
    """Run RED as a mod_python handler."""
    status_lookup = {
     100: apache.HTTP_CONTINUE                     ,
     101: apache.HTTP_SWITCHING_PROTOCOLS          ,
     102: apache.HTTP_PROCESSING                   ,
     200: apache.HTTP_OK                           ,
     201: apache.HTTP_CREATED                      ,
     202: apache.HTTP_ACCEPTED                     ,
     203: apache.HTTP_NON_AUTHORITATIVE            ,
     204: apache.HTTP_NO_CONTENT                   ,
     205: apache.HTTP_RESET_CONTENT                ,
     206: apache.HTTP_PARTIAL_CONTENT              ,
     207: apache.HTTP_MULTI_STATUS                 ,
     300: apache.HTTP_MULTIPLE_CHOICES             ,
     301: apache.HTTP_MOVED_PERMANENTLY            ,
     302: apache.HTTP_MOVED_TEMPORARILY            ,
     303: apache.HTTP_SEE_OTHER                    ,
     304: apache.HTTP_NOT_MODIFIED                 ,
     305: apache.HTTP_USE_PROXY                    ,
     307: apache.HTTP_TEMPORARY_REDIRECT           ,
     308: apache.HTTP_PERMANENT_REDIRECT           ,
     400: apache.HTTP_BAD_REQUEST                  ,
     401: apache.HTTP_UNAUTHORIZED                 ,
     402: apache.HTTP_PAYMENT_REQUIRED             ,
     403: apache.HTTP_FORBIDDEN                    ,
     404: apache.HTTP_NOT_FOUND                    ,
     405: apache.HTTP_METHOD_NOT_ALLOWED           ,
     406: apache.HTTP_NOT_ACCEPTABLE               ,
     407: apache.HTTP_PROXY_AUTHENTICATION_REQUIRED,
     408: apache.HTTP_REQUEST_TIME_OUT             ,
     409: apache.HTTP_CONFLICT                     ,
     410: apache.HTTP_GONE                         ,
     411: apache.HTTP_LENGTH_REQUIRED              ,
     412: apache.HTTP_PRECONDITION_FAILED          ,
     413: apache.HTTP_REQUEST_ENTITY_TOO_LARGE     ,
     414: apache.HTTP_REQUEST_URI_TOO_LARGE        ,
     415: apache.HTTP_UNSUPPORTED_MEDIA_TYPE       ,
     416: apache.HTTP_RANGE_NOT_SATISFIABLE        ,
     417: apache.HTTP_EXPECTATION_FAILED           ,
     422: apache.HTTP_UNPROCESSABLE_ENTITY         ,
     423: apache.HTTP_LOCKED                       ,
     424: apache.HTTP_FAILED_DEPENDENCY            ,
     426: apache.HTTP_UPGRADE_REQUIRED             ,
     500: apache.HTTP_INTERNAL_SERVER_ERROR        ,
     501: apache.HTTP_NOT_IMPLEMENTED              ,
     502: apache.HTTP_BAD_GATEWAY                  ,
     503: apache.HTTP_SERVICE_UNAVAILABLE          ,
     504: apache.HTTP_GATEWAY_TIME_OUT             ,
     505: apache.HTTP_VERSION_NOT_SUPPORTED        ,
     506: apache.HTTP_VARIANT_ALSO_VARIES          ,
     507: apache.HTTP_INSUFFICIENT_STORAGE         ,
     510: apache.HTTP_NOT_EXTENDED                 ,
    }

    r.content_type = "text/html"
    def response_start(code, phrase, hdrs):
        r.status = status_lookup.get(
            int(code),
            apache.HTTP_INTERNAL_SERVER_ERROR
        )
        for hdr in hdrs:
            r.headers_out[hdr[0]] = hdr[1]
    def response_done(trailers):
        thor.schedule(thor.stop)
    query_string = cgi.parse_qs(r.args or "")
    try:
        RedWebUi(r.unparsed_uri, r.method, query_string,
                 response_start, r.write, response_done)
        thor.run()
    except:
        except_handler_factory(r.write)()
    return apache.OK

