"""
A collection of notes that the RED can emit.

PLEASE NOTE: the summary field is automatically HTML escaped, so it can contain arbitrary text (as
long as it's unicode).

However, the longer text field IS NOT ESCAPED, and therefore all variables to be interpolated into
it need to be escaped to be safe for use in HTML.
"""

from cgi import escape as e_html
from markdown import markdown

class _Classifications:
    "Note classifications."
    GENERAL = u"General"
    SECURITY = u"Security"
    CONNEG = u"Content Negotiation"
    CACHING = u"Caching"
    VALIDATION = u"Validation"
    CONNECTION = u"Connection"
    RANGE = u"Partial Content"
c = _Classifications()

class _Levels:
    "Note levels."
    GOOD = u'good'
    WARN = u'warning'
    BAD = u'bad'
    INFO = u'info'
l = _Levels()

class Note:
    """
    A note about an HTTP resource, representation, or other component
    related to the URI under test.
    """
    category = None
    level = None
    summary = u""
    text = u""
    def __init__(self, subject, subrequest=None, vrs=None):
        self.subject = subject
        self.subrequest = subrequest
        self.vars = vrs or {}

    def __eq__(self, other):
        if self.__class__ == other.__class__ \
           and self.subject == other.subject \
           and self.show_summary('en') == other.show_summary('en'):
            return True
        else:
            return False

    def show_summary(self, lang):
        """
        Output a textual summary of the message as a Unicode string.
        
        Note that if it is displayed in an environment that needs 
        encoding (e.g., HTML), that is *NOT* done.
        """
        return self.summary % self.vars
        
    def show_text(self, lang):
        """
        Show the HTML text for the message as a Unicode string.
        
        The resulting string is already HTML-encoded.
        """
        return markdown(self.text % dict(
            [(k, e_html(unicode(v), True)) for k, v in self.vars.items()]
        ), output_format="html5")


response = {
    'this': u'This response',
    'conneg': u'The uncompressed response',
    'LM validation': u'The 304 response',
    'ETag validation': u'The 304 response',
    'range': u'The partial response',
}

class URI_TOO_LONG(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The URI is very long (%(uri_len)s characters)."
    text = u"""\
Long URIs aren't supported by some implementations, including proxies. A reasonable upper size
limit is 8192 characters."""

class URI_BAD_SYNTAX(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The URI's syntax isn't valid."
    text = u"""\
This isn't a valid URI. Look for illegal characters and other problems; see
[RFC3986](http://www.ietf.org/rfc/rfc3986.txt) for more information."""

class REQUEST_HDR_IN_RESPONSE(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u'"%(field_name)s" is a request header.'
    text = u"""\
%(field_name)s is only defined to have meaning in requests; in responses, it doesn't have any
meaning, so RED has ignored it."""

class RESPONSE_HDR_IN_REQUEST(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u'"%(field_name)s" is a request header.'
    text = u"""\
%(field_name)s is only defined to have meaning in responses; in requests, it doesn't have any
meaning, so RED has ignored it."""

class FIELD_NAME_BAD_SYNTAX(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u'"%(field_name)s" is not a valid header field-name.'
    text = u"""\
Header names are limited to the TOKEN production in HTTP; i.e., they can't contain parenthesis,
angle brackes (<>), ampersands (@), commas, semicolons, colons, backslashes (\\), forward
slashes (/), quotes, square brackets ([]), question marks, equals signs (=), curly brackets ({})
spaces or tabs."""

class HEADER_BLOCK_TOO_LARGE(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"%(response)s's headers are very large (%(header_block_size)s)."
    text = u"""\
Some implementations have limits on the total size of headers that they'll accept. For example,
Squid's default configuration limits header blocks to 20k."""

class HEADER_TOO_LARGE(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The %(header_name)s header is very large (%(header_size)s)."
    text = u"""\
Some implementations limit the size of any single header line."""

class HEADER_NAME_ENCODING(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(header_name)s header's name contains non-ASCII characters."
    text = u"""\
HTTP header field-names can only contain ASCII characters. RED has detected (and possibly removed)
non-ASCII characters in this header name."""

class HEADER_VALUE_ENCODING(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The %(header_name)s header's value contains non-ASCII characters."
    text = u"""\
HTTP headers use the ISO-8859-1 character set, but in most cases are pure ASCII (a subset of this
encoding).

This header has non-ASCII characters, which RED has interpreted as being encoded in
ISO-8859-1. If another encoding is used (e.g., UTF-8), the results may be unpredictable."""

class HEADER_DEPRECATED(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The %(header_name)s header is deprecated."
    text = u"""\
This header field is no longer recommended for use, because of interoperability problems and/or
lack of use. See [its documentation](%(ref)s) for more information."""

class SINGLE_HEADER_REPEAT(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"Only one %(field_name)s header is allowed in a response."
    text = u"""\
This header is designed to only occur once in a message. When it occurs more than once, a receiver
needs to choose the one to use, which can lead to interoperability problems, since different
implementations may make different choices.

For the purposes of its tests, RED uses the last instance of the header that is present; other
implementations may behave differently."""

class BODY_NOT_ALLOWED(Note):
    category = c.CONNECTION
    level = l.BAD
    summary = u"%(response)s is not allowed to have a body."
    text = u"""\
HTTP defines a few special situations where a response does not allow a body. This includes 101,
204 and 304 responses, as well as responses to the `HEAD` method.

%(response)s had a body, despite it being disallowed. Clients receiving it may treat the body as
the next response in the connection, leading to interoperability and security issues."""

class BAD_SYNTAX(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(field_name)s header's syntax isn't valid."
    text = u"""\
The value for this header doesn't conform to its specified syntax; see [its
definition](%(ref_uri)s) for more information."""

# Specific headers

class BAD_CC_SYNTAX(Note):
    category = c.CACHING
    level = l.BAD
    summary = u"The %(bad_cc_attr)s Cache-Control directive's syntax is incorrect."
    text = u"This value must be an integer."

class AGE_NOT_INT(Note):
    category = c.CACHING
    level = l.BAD
    summary = u"The Age header's value should be an integer."
    text = u"""\
The `Age` header indicates the age of the response; i.e., how long it has been cached
since it was generated. The value given was not an integer, so it is not a valid age."""

class AGE_NEGATIVE(Note):
    category = c.CACHING
    level = l.BAD
    summary = u"The Age headers' value must be a positive integer."
    text = u"""\
The `Age` header indicates the age of the response; i.e., how long it has been cached
since it was generated. The value given was negative, so it is not a valid age."""

class BAD_CHUNK(Note):
    category = c.CONNECTION
    level = l.BAD
    summary = u"%(response)s had chunked encoding errors."
    text = u"""\
The response indicates it uses HTTP chunked encoding, but there was a problem decoding the
chunking.

A valid chunk looks something like this:

`[chunk-size in hex]\\r\\n[chunk-data]\\r\\n`

However, the chunk sent started like this:

`%(chunk_sample)s`

This is a serious problem, because HTTP uses chunking to delimit one response from the next one;
incorrect chunking can lead to interoperability and security problems.

This issue is often caused by sending an integer chunk size instead of one in hex, or by sending
`Transfer-Encoding: chunked` without actually chunking the response body."""

class BAD_GZIP(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"%(response)s was compressed using GZip, but the header wasn't \
valid."
    text = u"""\
GZip-compressed responses have a header that contains metadata. %(response)s's header wasn't valid;
the error encountered was "`%(gzip_error)s`"."""

class BAD_ZLIB(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"%(response)s was compressed using GZip, but the data was corrupt."
    text = u"""\
GZip-compressed responses use zlib compression to reduce the number of bytes transferred on the
wire. However, this response could not be decompressed; the error encountered was
"`%(zlib_error)s`".

%(ok_zlib_len)s bytes were decompressed successfully before this; the erroneous chunk starts with
"`%(chunk_sample)s`"."""

class ENCODING_UNWANTED(Note):
    category = c.CONNEG
    level = l.WARN
    summary = u"%(response)s contained unwanted content-codings."
    text = u"""\
%(response)s's `Content-Encoding` header indicates it has content-codings applied
(`%(unwanted_codings)s`) that RED didn't ask for.

Normally, clients ask for the encodings they want in the `Accept-Encoding` request header. Using
encodings that the client doesn't explicitly request can lead to interoperability problems."""

class TRANSFER_CODING_IDENTITY(Note):
    category = c.CONNECTION
    level = l.INFO
    summary = u"The identity transfer-coding isn't necessary."
    text = u"""\
HTTP defines _transfer-codings_ as a hop-by-hop encoding of the message body. The `identity`
tranfer-coding was defined as the absence of encoding; it doesn't do anything, so it's necessary.

You can remove this token to save a few bytes."""

class TRANSFER_CODING_UNWANTED(Note):
    category = c.CONNECTION
    level = l.BAD
    summary = u"%(response)s has unsupported transfer-coding."
    text = u"""\
%(response)s's `Transfer-Encoding` header indicates it has transfer-codings applied, but RED didn't
ask for it (or them) to be.

They are: `%(unwanted_codings)s`

Normally, clients ask for the encodings they want in the `TE` request header. Using codings that
the client doesn't explicitly request can lead to interoperability problems."""

class TRANSFER_CODING_PARAM(Note):
    category = c.CONNECTION
    level = l.WARN
    summary = u"%(response)s had parameters on its transfer-codings."
    text = u"""\
HTTP allows transfer-codings in the `Transfer-Encoding` header to have optional parameters, but it
doesn't define what they mean.

%(response)s has encodings with such paramters; although they're technically allowed, they may
cause interoperability problems. They should be removed."""

class BAD_DATE_SYNTAX(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(field_name)s header's value isn't a valid date."
    text = u"""\
HTTP dates have very specific syntax, and sending an invalid date can cause a number of problems,
especially around caching. Common problems include sending "1 May" instead of "01 May" (the month
is a fixed-width field), and sending a date in a timezone other than GMT. See [the HTTP
specification](http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.3) for more
information."""

class LM_FUTURE(Note):
    category = c.CACHING
    level = l.BAD
    summary = u"The Last-Modified time is in the future."
    text = u"""\
The `Last-Modified` header indicates the last point in time that the resource has changed.
%(response)s's `Last-Modified` time is in the future, which doesn't have any defined meaning in
HTTP."""

class LM_PRESENT(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"The resource last changed %(last_modified_string)s."
    text = u"""\
The `Last-Modified` header indicates the last point in time that the resource has changed. It is
used in HTTP for validating cached responses, and for calculating heuristic freshness in caches.

This resource last changed %(last_modified_string)s."""

class CONTENT_TRANSFER_ENCODING(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The Content-Transfer-Encoding header isn't necessary in HTTP."
    text = u"""\
`Content-Transfer-Encoding` is a MIME header, not a HTTP header; it's only used when HTTP messages
are moved over MIME-based protocols (e.g., SMTP), which is uncommon.

You can safely remove this header.
    """

class MIME_VERSION(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The MIME-Version header isn't necessary in HTTP."
    text = u"""\
`MIME_Version` is a MIME header, not a HTTP header; it's only used when HTTP messages are moved
over MIME-based protocols (e.g., SMTP), which is uncommon.

You can safely remove this header.
    """

class PRAGMA_NO_CACHE(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"Pragma: no-cache is a request directive, not a response \
directive."
    text = u"""\
`Pragma` is a very old request header that is sometimes used as a response header, even though this
is not specified behaviour. `Cache-Control: no-cache` is more appropriate."""

class PRAGMA_OTHER(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"""\
The Pragma header is being used in an undefined way."""
    text = u"""\
HTTP only defines `Pragma: no-cache`; other uses of this header are deprecated."""

class VIA_PRESENT(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"One or more intermediaries are present."
    text = u"""\
The `Via` header indicates that one or more intermediaries are present between RED and the origin
server for the resource.

This may indicate that a proxy is in between RED and the server, or that the server uses a "reverse
proxy" or CDN in front of it.

There field has three space-separated components; first, the HTTP version of the message that the
intermediary received, then the identity of the intermediary (usually but not always its hostname),
and then optionally a product identifier or comment (usually used to identify the software being
used)."""

class LOCATION_UNDEFINED(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"%(response)s doesn't define any meaning for the Location header."
    text = u"""\
The `Location` header is used for specific purposes in HTTP; mostly to indicate the URI of another
resource (e.g., in redirection, or when a new resource is created).

In other status codes (such as this one) it doesn't have a defined meaning, so any use of it won't
be interoperable.

Sometimes `Location` is confused with `Content-Location`, which indicates a URI for the payload of
the message that it appears in."""

class LOCATION_NOT_ABSOLUTE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The Location header contains a relative URI."
    text = u"""\
`Location` was originally specified to contain an absolute, not relative, URI.

It is in the process of being updated, and most clients will work around this.

The correct absolute URI is (probably): `%(full_uri)s`"""

class CONTENT_TYPE_OPTIONS(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s instructs Internet Explorer not to 'sniff' its \
media type."
    text = u"""\
Many Web browers "sniff" the media type of responses to figure out whether they're HTML, RSS or
another format, no matter what the `Content-Type` header says.

This header instructs Microsoft's Internet Explorer not to do this, but to always respect the
Content-Type header. It probably won't have any effect in other clients.

See [this blog entry](http://bit.ly/t1UHW2) for more information about this header."""

class CONTENT_TYPE_OPTIONS_UNKNOWN(Note):
    category = c.SECURITY
    level = l.WARN
    summary = u"%(response)s contains an X-Content-Type-Options header with an unknown value."
    text = u"""\
Only one value is currently defined for this header, `nosniff`. Using other values here won't
necessarily cause problems, but they probably won't have any effect either.

See [this blog entry](http://bit.ly/t1UHW2) for more information about this header."""

class DOWNLOAD_OPTIONS(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s can't be directly opened directly by Internet Explorer when downloaded."
    text = u"""\
When the `X-Download-Options` header is present with the value `noopen`, Internet Explorer users
are prevented from directly opening a file download; instead, they must first save the file
locally. When the locally saved file is later opened, it no longer executes in the security context
of your site, helping to prevent script injection.

This header probably won't have any effect in other clients.

See [this blog article](http://bit.ly/sfuxWE) for more details."""

class DOWNLOAD_OPTIONS_UNKNOWN(Note):
    category = c.SECURITY
    level = l.WARN
    summary = u"%(response)s contains an X-Download-Options header with an unknown value."
    text = u"""\
Only one value is currently defined for this header, `noopen`. Using other values here won't
necessarily cause problems, but they probably won't have any effect either.

See [this blog article](http://bit.ly/sfuxWE) for more details."""

class FRAME_OPTIONS_DENY(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s prevents some browsers from rendering it if it will be contained within a frame."
    text = u"""\
The `X-Frame-Options` response header controls how IE8 handles HTML frames; the `DENY` value
prevents this content from being rendered within a frame, which defends against certain types of
attacks.

See [this blog entry](http://bit.ly/v5Bh5Q) for more information.
     """

class FRAME_OPTIONS_SAMEORIGIN(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s prevents some browsers from rendering it if it will be contained within a frame on another site."
    text = u"""\
The `X-Frame-Options` response header controls how IE8 handles HTML frames; the `DENY` value
prevents this content from being rendered within a frame on another site, which defends against
certain types of attacks.

Currently this is supported by IE8 and Safari 4.

See [this blog entry](http://bit.ly/v5Bh5Q) for more information.
     """

class FRAME_OPTIONS_UNKNOWN(Note):
    category = c.SECURITY
    level = l.WARN
    summary = u"%(response)s contains an X-Frame-Options header with an unknown value."
    text = u"""\
Only two values are currently defined for this header, `DENY` and `SAMEORIGIN`. Using other values
here won't necessarily cause problems, but they probably won't have any effect either.

See [this blog entry](http://bit.ly/v5Bh5Q) for more information.
     """

class SMART_TAG_NO_WORK(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The %(field_name)s header doesn't have any effect on smart tags."
    text = u"""\
This header doesn't have any effect on Microsoft Smart Tags, except in certain beta versions of
IE6. To turn them off, you'll need to make changes in the HTML content it"""

class UA_COMPATIBLE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"%(response)s explicitly sets a rendering mode for Internet Explorer 8."
    text = u"""\
Internet Explorer 8 allows responses to explicitly set the rendering mode used for a given page
(known a the "compatibility mode").

See [Microsoft's documentation](http://msdn.microsoft.com/en-us/library/cc288325(VS.85).aspx) for
more information."""

class UA_COMPATIBLE_REPEAT(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"%(response)s has multiple X-UA-Compatible directives targeted at the same UA."
    text = u"""\
Internet Explorer 8 allows responses to explicitly set the rendering mode used for a page.

This response has more than one such directive targetted at one browser; this may cause
unpredictable results.

See [this blog entry](http://msdn.microsoft.com/en-us/library/cc288325(VS.85).aspx) for more
information."""

class XSS_PROTECTION_ON(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s enables XSS filtering in IE8+."
    text = u"""\
Recent versions of Internet Explorer have built-in Cross-Site Scripting (XSS) attack protection;
they try to automatically filter requests that fit a particular profile.

%(response)s has explicitly enabled this protection. If IE detects a Cross-site scripting attack,
it will "sanitise" the page to prevent the attack. In other words, the page will still render.

This header probably won't have any effect on other clients.

See [this blog entry](http://bit.ly/tJbICH) for more information."""


class XSS_PROTECTION_OFF(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s disables XSS filtering in IE8+."
    text = u"""\
Recent versions of Internet Explorer have built-in Cross-Site Scripting (XSS) attack protection;
they try to automatically filter requests that fit a particular profile.

%(response)s has explicitly disabled this protection. In some scenarios, this is useful to do, if
the protection interferes with the application.

This header probably won't have any effect on other clients.

See [this blog entry](http://bit.ly/tJbICH) for more information."""

class XSS_PROTECTION_BLOCK(Note):
    category = c.SECURITY
    level = l.INFO
    summary = u"%(response)s blocks XSS attacks in IE8+."
    text = u"""\
Recent versions of Internet Explorer have built-in Cross-Site Scripting (XSS) attack protection;
they try to automatically filter requests that fit a particular profile.

Usually, IE will rewrite the attacking HTML, so that the attack is neutralised, but the content can
still be seen. %(response)s instructs IE to not show such pages at all, but rather to display an
error.

This header probably won't have any effect on other clients.

See [this blog entry](http://bit.ly/tJbICH) for more information."""


### Ranges

class RANGE_SUBREQ_PROBLEM(Note):
    category = c.RANGE
    level = l.BAD
    summary = u"There was a problem checking for Partial Content support."
    text = u"""\
When RED tried to check the resource for partial content support, there was a problem:

`%(problem)s`

Trying again might fix it."""

class UNKNOWN_RANGE(Note):
    category = c.RANGE
    level = l.WARN
    summary = u"%(response)s advertises support for non-standard range-units."
    text = u"""\
The `Accept-Ranges` response header tells clients what `range-unit`s a resource is willing to
process in future requests. HTTP only defines two: `bytes` and `none`.

Clients who don't know about the non-standard range-unit will not be able to use it."""

class RANGE_CORRECT(Note):
    category = c.RANGE
    level = l.GOOD
    summary = u"A ranged request returned the correct partial content."
    text = u"""\
This resource advertises support for ranged requests with `Accept-Ranges`; that is, it allows
clients to specify that only part of it should be sent. RED has tested this by requesting part of
this response, which was returned correctly."""

class RANGE_INCORRECT(Note):
    category = c.RANGE
    level = l.BAD
    summary = u'A ranged request returned partial content, but it was incorrect.'
    text = u"""\
This resource advertises support for ranged requests with `Accept-Ranges`; that is, it allows
clients to specify that only part of the response should be sent. RED has tested this by requesting
part of this response, but the partial response doesn't correspond with the full response retrieved
at the same time. This could indicate that the range implementation isn't working properly.

RED sent:
    `Range: %(range)s`

RED expected %(range_expected_bytes)s bytes:
    `%(range_expected).100s`

RED received %(range_received_bytes)s bytes:
    `%(range_received).100s`

_(showing samples of up to 100 characters)_"""

class RANGE_CHANGED(Note):
    category = c.RANGE
    level = l.WARN
    summary = u"A ranged request returned another representation."
    text = u"""\
A new representation was retrieved when checking support of ranged request. This is not an error,
it just indicates that RED cannot draw any conclusion at this time."""

class RANGE_FULL(Note):
    category = c.RANGE
    level = l.WARN
    summary = u"A ranged request returned the full rather than partial content."
    text = u"""\
This resource advertises support for ranged requests with `Accept-Ranges`; that is, it allows
clients to specify that only part of the response should be sent. RED has tested this by requesting
part of this response, but the entire response was returned. In other words, although the resource
advertises support for partial content, it doesn't appear to actually do so."""

class RANGE_STATUS(Note):
    category = c.RANGE
    level = l.INFO
    summary = u"A ranged request returned a %(range_status)s status."
    text = u"""\
This resource advertises support for ranged requests; that is, it allows clients to specify that
only part of the response should be sent. RED has tested this by requesting part of this response,
but a %(enc_range_status)s response code was returned, which RED was not expecting."""

class RANGE_NEG_MISMATCH(Note):
    category = c.RANGE
    level = l.BAD
    summary = u"Partial responses don't have the same support for compression that full ones do."
    text = u"""\
This resource supports ranged requests and also supports negotiation for gzip compression, but
doesn't support compression for both full and partial responses.

This can cause problems for clients when they compare the partial and full responses, since the
partial response is expressed as a byte range, and compression changes the bytes."""

class MISSING_HDRS_206(Note):
    category = c.VALIDATION
    level = l.WARN
    summary = u"The %(subreq_type)s response is missing required headers."
    text = u"""\
HTTP requires `206 Parital Content` responses to have certain headers, if they are also present in
a normal (e.g., `200 OK` response).

%(response)s is missing the following headers: `%(missing_hdrs)s`.

This can affect cache operation; because the headers are missing, caches might remove them from
their stored copies."""

### Body

class CL_CORRECT(Note):
    category = c.GENERAL
    level = l.GOOD
    summary = u'The Content-Length header is correct.'
    text = u"""\
`Content-Length` is used by HTTP to delimit messages; that is, to mark the end of one message and
the beginning of the next. RED has checked the length of the body and found the `Content-Length` to
be correct."""

class CL_INCORRECT(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"%(response)s's Content-Length header is incorrect."
    text = u"""\
`Content-Length` is used by HTTP to delimit messages; that is, to mark the end of one message and
the beginning of the next. RED has checked the length of the body and found the `Content-Length` is
not correct. This can cause problems not only with connection handling, but also caching, since an
incomplete response is considered uncacheable.

The actual body size sent was %(body_length)s bytes."""

class CMD5_CORRECT(Note):
    category = c.GENERAL
    level = l.GOOD
    summary = u'The Content-MD5 header is correct.'
    text = u"""\
`Content-MD5` is a hash of the body, and can be used to ensure integrity of the response. RED has
checked its value and found it to be correct."""

class CMD5_INCORRECT(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u'The Content-MD5 header is incorrect.'
    text = u"""\
`Content-MD5` is a hash of the body, and can be used to ensure integrity of the response. RED has
checked its value and found it to be incorrect; i.e., the given `Content-MD5` does not match what
RED thinks it should be (%(calc_md5)s)."""

### Conneg

class CONNEG_SUBREQ_PROBLEM(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"There was a problem checking for Content Negotiation support."
    text = u"""\
When RED tried to check the resource for content negotiation support, there was a problem:

`%(problem)s`

Trying again might fix it."""

class CONNEG_GZIP_GOOD(Note):
    category = c.CONNEG
    level = l.GOOD
    summary = u'Content negotiation for gzip compression is supported, saving %(savings)s%%.'
    text = u"""\
HTTP supports compression of responses by negotiating for `Content-Encoding`. When RED asked for a
compressed response, the resource provided one, saving %(savings)s%% of its original size (from
%(orig_size)s to %(gzip_size)s bytes).

The compressed response's headers are displayed."""

class CONNEG_GZIP_BAD(Note):
    category = c.CONNEG
    level = l.WARN
    summary = u'Content negotiation for gzip compression makes the response %(savings)s%% larger.'
    text = u"""\
HTTP supports compression of responses by negotiating for `Content-Encoding`. When RED asked for a
compressed response, the resource provided one, but it was %(savings)s%% _larger_ than the original
response; from %(orig_size)s to %(gzip_size)s bytes.

Often, this happens when the uncompressed response is very small, or can't be compressed more;
since gzip compression has some overhead, it can make the response larger. Turning compression
**off** for this resource may slightly improve response times and save bandwidth.

The compressed response's headers are displayed."""

class CONNEG_NO_GZIP(Note):
    category = c.CONNEG
    level = l.INFO
    summary = u'Content negotiation for gzip compression isn\'t supported.'
    text = u"""\
HTTP supports compression of responses by negotiating for `Content-Encoding`. When RED asked for a
compressed response, the resource did not provide one."""

class CONNEG_NO_VARY(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"The resource negotiates responses, but doesn't send an appropriate Vary header."
    text = u"""\
All content negotiated responses need to have a `Vary` header that reflects the header(s) used to
select the response.

This resource supports the `gzip` content encoding, so all responses' `Vary` header needs to contain
`Accept-Encoding`, the request header used."""

class CONNEG_GZIP_WITHOUT_ASKING(Note):
    category = c.CONNEG
    level = l.WARN
    summary = u"A gzip-compressed response was sent when it wasn't asked for."
    text = u"""\
HTTP supports compression of responses by negotiating for `Content-Encoding`. Even though RED
didn't ask for a compressed response, the resource provided one anyway.

It could be that the response is always compressed, but doing so can break clients that aren't
expecting a compressed response."""

class VARY_INCONSISTENT(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"The resource doesn't send Vary consistently."
    text = u"""\
HTTP requires that the `Vary` response header be sent consistently for all responses if they change
based upon different aspects of the request.

This resource has both compressed and uncompressed variants available, negotiated by the
`Accept-Encoding` request header, but it sends different Vary headers for each;

* "`%(conneg_vary)s`" when the response is compressed, and
* "`%(no_conneg_vary)s`" when it is not.

This can cause problems for downstream caches, because they cannot consistently determine what the
cache key for a given URI is."""

class VARY_STATUS_MISMATCH(Note):
    category = c.CONNEG
    level = l.WARN
    summary = u"The response status is different when content negotiation happens."
    text = u"""\
When content negotiation is used, the response status shouldn't change between negotiated and
non-negotiated responses.

When RED send asked for a negotiated response, it got a `%(neg_status)s` status code; when it
didn't, it got `%(noneg_status)s`.

RED hasn't checked other aspects of content negotiation because of this."""
    
class VARY_HEADER_MISMATCH(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"The %(header)s header is different when content negotiation happens."
    text = u"""\
When content negotiation is used, the %(header)s response header shouldn't change between
negotiated and non-negotiated responses."""

class VARY_BODY_MISMATCH(Note):
    category = c.CONNEG
    level = l.INFO
    summary = u"The response body is different when content negotiation happens."
    text = u"""\
When content negotiation is used, the response body typically shouldn't change between negotiated
and non-negotiated responses.

There might be legitimate reasons for this; e.g., because different servers handled the two
requests. However, RED's output may be skewed as a result."""

class VARY_ETAG_DOESNT_CHANGE(Note):
    category = c.CONNEG
    level = l.BAD
    summary = u"The ETag doesn't change between negotiated representations."
    text = u"""\
HTTP requires that the `ETag`s for two different responses associated with the same URI be
different as well, to help caches and other receivers disambiguate them.

This resource, however, sent the same strong ETag for both its compressed and uncompressed versions
(negotiated by `Accept-Encoding`). This can cause interoperability problems, especially with caches.

Please note that some versions of the Apache HTTP Server sometimes send the same ETag for both
compressed and uncompressed versions of a ressource. This is a [known
bug](https://issues.apache.org/bugzilla/show_bug.cgi?id=39727)."""

### Clock

class DATE_CORRECT(Note):
    category = c.GENERAL
    level = l.GOOD
    summary = u"The server's clock is correct."
    text = u"""\
HTTP's caching model assumes reasonable synchronisation between clocks on the server and client;
using RED's local clock, the server's clock appears to be well-synchronised."""

class DATE_INCORRECT(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The server's clock is %(clock_skew_string)s."
    text = u"""\
Using RED's local clock, the server's clock does not appear to be well-synchronised.

HTTP's caching model assumes reasonable synchronisation between clocks on the server and client;
clock skew can cause responses that should be cacheable to be considered uncacheable (especially if
their freshness lifetime is short).

Ask your server administrator to synchronise the clock, e.g., using
[NTP](http://en.wikipedia.org/wiki/Network_Time_Protocol Network Time Protocol).
    
Apparent clock skew can also be caused by caching the response without adjusting the `Age` header;
e.g., in a reverse proxy or Content Delivery network. See [this
paper](http://www2.research.att.com/~edith/Papers/HTML/usits01/index.html) for more information. """

class AGE_PENALTY(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"It appears that the Date header has been changed by an intermediary."
    text = u"""\
It appears that this response has been cached by a reverse proxy or Content Delivery Network,
because the `Age` header is present, but the `Date` header is more recent than it indicates.

Generally, reverse proxies should either omit the `Age` header (if they have another means of
determining how fresh the response is), or leave the `Date` header alone (i.e., act as a normal
HTTP cache).

See [this paper](http://j.mp/S7lPL4) for more information."""

class DATE_CLOCKLESS(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"%(response)s doesn't have a Date header."
    text = u"""\
Although HTTP allowes a server not to send a `Date` header if it doesn't have a local clock, this
can make calculation of the response's age inexact."""

class DATE_CLOCKLESS_BAD_HDR(Note):
    category = c.CACHING
    level = l.BAD
    summary = u"Responses without a Date aren't allowed to have Expires or Last-Modified values."
    text = u"""\
Because both the `Expires` and `Last-Modified` headers are date-based, it's necessary to know when
the message was generated for them to be useful; otherwise, clock drift, transit times between
nodes as well as caching could skew their application."""

### Caching

class METHOD_UNCACHEABLE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"Responses to the %(method)s method can't be stored by caches."
    text = u"""\
"""

class CC_MISCAP(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"The %(cc)s Cache-Control directive appears to have incorrect \
capitalisation."
    text = u"""\
Cache-Control directive names are case-sensitive, and will not be recognised by most
implementations if the capitalisation is wrong.

Did you mean to use %(cc_lower)s instead of %(cc)s?"""

class CC_DUP(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"The %(cc)s Cache-Control directive appears more than once."
    text = u"""\
The %(cc)s Cache-Control directive is only defined to appear once; it is used more than once here,
so implementations may use different instances (e.g., the first, or the last), making their
behaviour unpredictable."""

class NO_STORE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s can't be stored by a cache."
    text = u"""\
The `Cache-Control: no-store` directive indicates that this response can't be stored by a cache."""

class PRIVATE_CC(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s only allows a private cache to store it."
    text = u"""\
The `Cache-Control: private` directive indicates that the response can only be stored by caches
that are specific to a single user; for example, a browser cache. Shared caches, such as those in
proxies, cannot store it."""

class PRIVATE_AUTH(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s only allows a private cache to store it."
    text = u"""\
Because the request was authenticated and this response doesn't contain a `Cache-Control: public`
directive, this response can only be stored by caches that are specific to a single user; for
example, a browser cache. Shared caches, such as those in proxies, cannot store it."""

class STOREABLE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"""\
%(response)s allows all caches to store it."""
    text = u"""\
A cache can store this response; it may or may not be able to use it to satisfy a particular
request."""

class NO_CACHE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s cannot be served from cache without validation."
    text = u"""\
The `Cache-Control: no-cache` directive means that while caches **can** store this
response, they cannot use it to satisfy a request unless it has been validated (either with an
`If-None-Match` or `If-Modified-Since` conditional) for that request."""

class NO_CACHE_NO_VALIDATOR(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s cannot be served from cache without validation."
    text = u"""\
The `Cache-Control: no-cache` directive means that while caches **can** store this response, they
cannot use it to satisfy a request unless it has been validated (either with an `If-None-Match` or
`If-Modified-Since` conditional) for that request.

%(response)s doesn't have a `Last-Modified` or `ETag` header, so it effectively can't be used by a
cache."""

class VARY_ASTERISK(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"Vary: * effectively makes this response uncacheable."
    text = u"""\
`Vary *` indicates that responses for this resource vary by some aspect that can't (or won't) be
described by the server. This makes this response effectively uncacheable."""

class VARY_USER_AGENT(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"Vary: User-Agent can cause cache inefficiency."
    text = u"""\
Sending `Vary: User-Agent` requires caches to store a separate copy of the response for every
`User-Agent` request header they see.

Since there are so many different `User-Agent`s, this can "bloat" caches with many copies of the
same thing, or cause them to give up on storing these responses at all.

Consider having different URIs for the various versions of your content instead; this will give
finer control over caching without sacrificing efficiency."""

class VARY_HOST(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"Vary: Host is not necessary."
    text = u"""\
Some servers (e.g., [Apache](http://httpd.apache.org/) with
[mod_rewrite](http://httpd.apache.org/docs/2.4/mod/mod_rewrite.html)) will send `Host` in the
`Vary` header, in the belief that since it affects how the server selects what to send back, this
is necessary.

This is not the case; HTTP specifies that the URI is the basis of the cache key, and the URI
incorporates the `Host` header.

The presence of `Vary: Host` may make some caches not store an otherwise cacheable response (since
some cache implementations will not store anything that has a `Vary` header)."""

class VARY_COMPLEX(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"This resource varies in %(vary_count)s ways."
    text = u"""\
The `Vary` mechanism allows a resource to describe the dimensions that its responses vary, or
change, over; each listed header is another dimension.

Varying by too many dimensions makes using this information impractical."""

class PUBLIC(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"Cache-Control: public is rarely necessary."
    text = u"""\
The `Cache-Control: public` directive makes a response cacheable even when the request had an
`Authorization` header (i.e., HTTP authentication was in use).

Therefore, HTTP-authenticated (NOT cookie-authenticated) resources _may_ have use for `public` to
improve cacheability, if used judiciously.

However, other responses **do not need to contain `public`**; it does not make the
response "more cacheable", and only makes the response headers larger."""

class CURRENT_AGE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s has been cached for %(age)s."
    text = u"""\
The `Age` header indicates the age of the response; i.e., how long it has been cached since it was
generated. HTTP takes this as well as any apparent clock skew into account in computing how old the
response already is."""

class FRESHNESS_FRESH(Note):
    category = c.CACHING
    level = l.GOOD
    summary = u"%(response)s is fresh until %(freshness_left)s from now."
    text = u"""\
A response can be considered fresh when its age (here, %(current_age)s) is less than its freshness
lifetime (in this case, %(freshness_lifetime)s)."""

class FRESHNESS_STALE_CACHE(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"%(response)s has been served stale by a cache."
    text = u"""\
An HTTP response is stale when its age (here, %(current_age)s) is equal to or exceeds its freshness
lifetime (in this case, %(freshness_lifetime)s).

HTTP allows caches to use stale responses to satisfy requests only under exceptional circumstances;
e.g., when they lose contact with the origin server. Either that has happened here, or the cache
has ignored the response's freshness directives."""

class FRESHNESS_STALE_ALREADY(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s is already stale."
    text = u"""\
A cache considers a HTTP response stale when its age (here, %(current_age)s) is equal to or exceeds
its freshness lifetime (in this case, %(freshness_lifetime)s).

HTTP allows caches to use stale responses to satisfy requests only under exceptional circumstances;
e.g., when they lose contact with the origin server."""

class FRESHNESS_HEURISTIC(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"%(response)s allows a cache to assign its own freshness lifetime."
    text = u"""\
When responses with certain status codes don't have explicit freshness information (like a `
Cache-Control: max-age` directive, or `Expires` header), caches are allowed to estimate how fresh
it is using a heuristic.

Usually, but not always, this is done using the `Last-Modified` header. For example, if your
response was last modified a week ago, a cache might decide to consider the response fresh for a
day.

Consider adding a `Cache-Control` header; otherwise, it may be cached for longer or shorter than
you'd like."""

class FRESHNESS_NONE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s can only be served by a cache under exceptional circumstances."
    text = u"""\
%(response)s doesn't have explicit freshness information (like a ` Cache-Control: max-age`
directive, or `Expires` header), and this status code doesn't allow caches to calculate their own.

Therefore, while caches may be allowed to store it, they can't use it, except in unusual
cirucumstances, such a when the origin server can't be contacted.

This behaviour can be prevented by using the `Cache-Control: must-revalidate` response directive.

Note that many caches will not store the response at all, because it is not generally useful to do
so."""

class FRESH_SERVABLE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s may still be served by a cache once it becomes stale."
    text = u"""\
HTTP allows stale responses to be served under some circumstances; for example, if the origin
server can't be contacted, a stale response can be used (even if it doesn't have explicit freshness
information).

This behaviour can be prevented by using the `Cache-Control: must-revalidate` response directive."""

class STALE_SERVABLE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s might be served by a cache, even though it is stale."
    text = u"""\
HTTP allows stale responses to be served under some circumstances; for example, if the origin
server can't be contacted, a stale response can be used (even if it doesn't have explicit freshness
information).

This behaviour can be prevented by using the `Cache-Control: must-revalidate` response directive."""

class FRESH_MUST_REVALIDATE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s cannot be served by a cache once it becomes stale."
    text = u"""\
The `Cache-Control: must-revalidate` directive forbids caches from using stale responses to satisfy
requests.

For example, caches often use stale responses when they cannot connect to the origin server; when
this directive is present, they will return an error rather than a stale response."""

class STALE_MUST_REVALIDATE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s cannot be served by a cache, because it is stale."
    text = u"""\
The `Cache-Control: must-revalidate` directive forbids caches from using stale responses to satisfy
requests.

For example, caches often use stale responses when they cannot connect to the origin server; when
this directive is present, they will return an error rather than a stale response."""

class FRESH_PROXY_REVALIDATE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s cannot be served by a shared cache once it becomes stale."
    text = u"""\
The presence of the `Cache-Control: proxy-revalidate` and/or `s-maxage` directives forbids shared
caches (e.g., proxy caches) from using stale responses to satisfy requests.

For example, caches often use stale responses when they cannot connect to the origin server; when
this directive is present, they will return an error rather than a stale response.

These directives do not affect private caches; for example, those in browsers."""

class STALE_PROXY_REVALIDATE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s cannot be served by a shared cache, because it is stale."
    text = u"""\
The presence of the `Cache-Control: proxy-revalidate` and/or `s-maxage` directives forbids shared
caches (e.g., proxy caches) from using stale responses to satisfy requests.

For example, caches often use stale responses when they cannot connect to the origin server; when
this directive is present, they will return an error rather than a stale response.

These directives do not affect private caches; for example, those in browsers."""

class CHECK_SINGLE(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"Only one of the pre-check and post-check Cache-Control directives is present."
    text = u"""\
Microsoft Internet Explorer implements two `Cache-Control` extensions, `pre-check` and
`post-check`, to give more control over how its cache stores responses.

%(response)s uses only one of these directives; as a result, Internet Explorer will ignore the
directive, since it requires both to be present.

See [this blog entry](http://bit.ly/rzT0um) for more information.
     """

class CHECK_NOT_INTEGER(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"One of the pre-check/post-check Cache-Control directives has a non-integer value."
    text = u"""\
Microsoft Internet Explorer implements two `Cache-Control` extensions, `pre-check` and
`post-check`, to give more control over how its cache stores responses.

Their values are required to be integers, but here at least one is not. As a result, Internet
Explorer will ignore the directive.

See [this blog entry](http://bit.ly/rzT0um) for more information."""

class CHECK_ALL_ZERO(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"The pre-check and post-check Cache-Control directives are both '0'."
    text = u"""\
Microsoft Internet Explorer implements two `Cache-Control` extensions, `pre-check` and
`post-check`, to give more control over how its cache stores responses.

%(response)s gives a value of "0" for both; as a result, Internet Explorer will ignore the
directive, since it requires both to be present.

In other words, setting these to zero has **no effect** (besides wasting bandwidth),
and may trigger bugs in some beta versions of IE.

See [this blog entry](http://bit.ly/rzT0um) for more information."""

class CHECK_POST_BIGGER(Note):
    category = c.CACHING
    level = l.WARN
    summary = u"The post-check Cache-control directive's value is larger than pre-check's."
    text = u"""\
Microsoft Internet Explorer implements two `Cache-Control` extensions, `pre-check` and
`post-check`, to give more control over how its cache stores responses.

%(response)s assigns a higher value to `post-check` than to `pre-check`; this means that Internet
Explorer will treat `post-check` as if its value is the same as `pre-check`'s.

See [this blog entry](http://bit.ly/rzT0um) for more information."""

class CHECK_POST_ZERO(Note):
    category = c.CACHING
    level = l.BAD
    summary = u"The post-check Cache-control directive's value is '0'."
    text = u"""\
Microsoft Internet Explorer implements two `Cache-Control` extensions, `pre-check` and
`post-check`, to give more control over how its cache stores responses.

%(response)s assigns a value of "0" to `post-check`, which means that Internet Explorer will reload
the content as soon as it enters the browser cache, effectively **doubling the load on the server**.

See [this blog entry](http://bit.ly/rzT0um) for more information."""

class CHECK_POST_PRE(Note):
    category = c.CACHING
    level = l.INFO
    summary = u"%(response)s may be refreshed in the background by Internet Explorer."
    text = u"""\
Microsoft Internet Explorer implements two `Cache-Control` extensions, `pre-check` and
`post-check`, to give more control over how its cache stores responses.

Once it has been cached for more than %(post_check)s seconds, a new request will result in the
cached response being served while it is refreshed in the background. However, if it has been
cached for more than %(pre_check)s seconds, the browser will download a fresh response before
showing it to the user.

Note that these directives do not have any effect on other clients or caches.

See [this blog entry](http://bit.ly/rzT0um) for more information."""


### General Validation

class NO_DATE_304(Note):
    category = c.VALIDATION
    level = l.WARN
    summary = u"304 responses need to have a Date header."
    text = u"""\
HTTP requires `304 Not Modified` responses to have a `Date` header in all but the most unusual
circumstances."""

class MISSING_HDRS_304(Note):
    category = c.VALIDATION
    level = l.WARN
    summary = u"The %(subreq_type)s response is missing required headers."
    text = u"""\
HTTP requires `304 Not Modified` responses to have certain headers, if they are also present in a
normal (e.g., `200 OK` response).

%(response)s is missing the following headers: `%(missing_hdrs)s`.

This can affect cache operation; because the headers are missing, caches might remove them from
their cached copies."""

### ETag Validation

class ETAG_SUBREQ_PROBLEM(Note):
    category = c.VALIDATION
    level = l.BAD
    summary = u"There was a problem checking for ETag validation support."
    text = u"""\
When RED tried to check the resource for ETag validation support, there was a problem:

`%(problem)s`

Trying again might fix it."""
    
class INM_304(Note):
    category = c.VALIDATION
    level = l.GOOD
    summary = u"If-None-Match conditional requests are supported."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has an `ETag`, clients should be able to use an `If-None-Match` request header
for validation. RED has done this and found that the resource sends a `304 Not Modified` response,
indicating that it supports `ETag` validation."""

class INM_FULL(Note):
    category = c.VALIDATION
    level = l.WARN
    summary = u"An If-None-Match conditional request returned the full content \
unchanged."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has an `ETag`, clients should be able to use an `If-None-Match` request header
for validation.

RED has done this and found that the resource sends the same, full response even though it hadn't
changed, indicating that it doesn't support `ETag` validation."""

class INM_DUP_ETAG_WEAK(Note):
    category = c.VALIDATION
    level = l.INFO
    summary = u"During validation, the ETag didn't change, even though the response body did."
    text = u"""\
`ETag`s are supposed to uniquely identify the response representation; if the content changes, so
should the ETag.

However, HTTP allows reuse of an `ETag` if it's "weak", as long as the server is OK with the two
different responses being considered as interchangeable by clients.

For example, if a small detail of a Web page changes, and it doesn't affect the overall meaning of
the page, you can use the same weak `ETag` to identify both versions.

If the changes are important, a different `ETag` should be used."""
    
class INM_DUP_ETAG_STRONG(Note):
    category = c.VALIDATION
    level = l.BAD
    summary = u"During validation, the ETag didn't change, even though the response body did."
    text = u"""\
`ETag`s are supposed to uniquely identify the response representation; if the content changes, so
should the ETag.

Here, the same `ETag` was used for two different responses during validation, which means that
downstream clients and caches might confuse them.

If the changes between the two versions aren't important, and they can be used interchangeably, a
"weak" ETag should be used; to do that, just prepend `W/`, to make it `W/%(etag)s`. Otherwise, a
different `ETag` needs to be used."""

class INM_UNKNOWN(Note):
    category = c.VALIDATION
    level = l.INFO
    summary = u"An If-None-Match conditional request returned the full content, but it had changed."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has an `ETag`, clients should be able to use an `If-None-Match` request header
for validation.

RED has done this, but the response changed between the original request and the validating
request, so RED can't tell whether or not `ETag` validation is supported."""

class INM_STATUS(Note):
    category = c.VALIDATION
    level = l.INFO
    summary = u"An If-None-Match conditional request returned a %(inm_status)s status."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has an `ETag`, clients should be able to use an `If-None-Match` request header
for validation. RED has done this, but the response had a %(enc_inm_status)s status code, so RED
can't tell whether or not `ETag` validation is supported."""

### Last-Modified Validation

class LM_SUBREQ_PROBLEM(Note):
    category = c.VALIDATION
    level = l.BAD
    summary = u"There was a problem checking for Last-Modified validation support."
    text = u"""\
When RED tried to check the resource for Last-Modified validation support, there was a problem:

`%(problem)s`

Trying again might fix it."""

class IMS_304(Note):
    category = c.VALIDATION
    level = l.GOOD
    summary = u"If-Modified-Since conditional requests are supported."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has a `Last-Modified` header, clients should be able to use an
`If-Modified-Since` request header for validation.

RED has done this and found that the resource sends a `304 Not Modified` response, indicating that
it supports `Last-Modified` validation."""

class IMS_FULL(Note):
    category = c.VALIDATION
    level = l.WARN
    summary = u"An If-Modified-Since conditional request returned the full content unchanged."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has a `Last-Modified` header, clients should be able to use an
`If-Modified-Since` request header for validation.

RED has done this and found that the resource sends a full response even though it hadn't changed,
indicating that it doesn't support `Last-Modified` validation."""

class IMS_UNKNOWN(Note):
    category = c.VALIDATION
    level = l.INFO
    summary = u"An If-Modified-Since conditional request returned the full content, but it had changed."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has a `Last-Modified` header, clients should be able to use an
`If-Modified-Since` request header for validation.

RED has done this, but the response changed between the original request and the validating
request, so RED can't tell whether or not `Last-Modified` validation is supported."""

class IMS_STATUS(Note):
    category = c.VALIDATION
    level = l.INFO
    summary = u"An If-Modified-Since conditional request returned a %(ims_status)s status."
    text = u"""\
HTTP allows clients to make conditional requests to see if a copy that they hold is still valid.
Since this response has a `Last-Modified` header, clients should be able to use an
`If-Modified-Since` request header for validation.

RED has done this, but the response had a %(enc_ims_status)s status code, so RED can't tell whether
or not `Last-Modified` validation is supported."""

### Status checks

class UNEXPECTED_CONTINUE(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"A 100 Continue response was sent when it wasn't asked for."
    text = u"""\
HTTP allows clients to ask a server if a request with a body (e.g., uploading a large file) will
succeed before sending it, using a mechanism called "Expect/continue".

When used, the client sends an `Expect: 100-continue`, in the request headers, and if the server is
willing to process it, it will send a `100 Continue` status code to indicate that the request
should continue.

This response has a `100 Continue` status code, but RED did not ask for it (with the `Expect`
request header). Sending this status code without it being requested can cause interoperability
problems."""

class UPGRADE_NOT_REQUESTED(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The protocol was upgraded without being requested."
    text = u"""\
HTTP defines the `Upgrade` header as a means of negotiating a change of protocol; i.e., it allows
you to switch the protocol on a given connection from HTTP to something else.

However, it must be first requested by the client; this response contains an `Upgrade` header, even
though RED did not ask for it.

Trying to upgrade the connection without the client's participation obviously won't work."""

class CREATED_SAFE_METHOD(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"A new resource was created in response to a safe request."
    text = u"""\
The `201 Created` status code indicates that processing the request had the side effect of creating
a new resource.

However, the request method that RED used (%(method)s) is defined as a "safe" method; that is, it
should not have any side effects.

Creating resources as a side effect of a safe method can have unintended consequences; for example,
search engine spiders and similar automated agents often follow links, and intermediaries sometimes
re-try safe methods when they fail."""

class CREATED_WITHOUT_LOCATION(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"A new resource was created without its location being sent."
    text = u"""\
The `201 Created` status code indicates that processing the request had the side effect of creating
a new resource.

HTTP specifies that the URL of the new resource is to be indicated in the `Location` header, but it
isn't present in this response."""

class CONTENT_RANGE_MEANINGLESS(Note):
    category = c.RANGE
    level = l.WARN
    summary = u"%(response)s shouldn't have a Content-Range header."
    text = u"""\
HTTP only defines meaning for the `Content-Range` header in responses with a `206 Partial Content`
or `416 Requested Range Not Satisfiable` status code.

Putting a `Content-Range` header in this response may confuse caches and clients."""

class PARTIAL_WITHOUT_RANGE(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"%(response)s doesn't have a Content-Range header."
    text = u"""\
The `206 Partial Response` status code indicates that the response body is only partial.

However, for a response to be partial, it needs to have a `Content-Range` header to indicate what
part of the full response it carries. This response does not have one, and as a result clients
won't be able to process it."""

class PARTIAL_NOT_REQUESTED(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"A partial response was sent when it wasn't requested."
    text = u"""\
The `206 Partial Response` status code indicates that the response body is only partial.

However, the client needs to ask for it with the `Range` header.

RED did not request a partial response; sending one without the client requesting it leads to
interoperability problems."""

class REDIRECT_WITHOUT_LOCATION(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"Redirects need to have a Location header."
    text = u"""\
The %(status)s status code redirects users to another URI. The `Location` header is used to convey
this URI, but a valid one isn't present in this response."""

class STATUS_DEPRECATED(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(status)s status code is deprecated."
    text = u"""\
When a status code is deprecated, it should not be used, because its meaning is not well-defined
enough to ensure interoperability."""

class STATUS_RESERVED(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(status)s status code is reserved."
    text = u"""\
Reserved status codes can only be used by future, standard protocol extensions; they are not for
private use."""

class STATUS_NONSTANDARD(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"%(status)s is not a standard HTTP status code."
    text = u"""\
Non-standard status codes are not well-defined and interoperable. Instead of defining your own
status code, you should reuse one of the more generic ones; for example, 400 for a client-side
problem, or 500 for a server-side problem."""

class STATUS_BAD_REQUEST(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The server didn't understand the request."
    text = u"""\
 """

class STATUS_FORBIDDEN(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The server has forbidden this request."
    text = u"""\
 """

class STATUS_NOT_FOUND(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The resource could not be found."
    text = u"""\
The server couldn't find any resource to serve for the
     given URI."""

class STATUS_NOT_ACCEPTABLE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The resource could not be found."
    text = u"""\
"""

class STATUS_CONFLICT(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The request conflicted with the state of the resource."
    text = u"""\
 """

class STATUS_GONE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The resource is gone."
    text = u"""\
The server previously had a resource at the given URI, but it is no longer there."""

class STATUS_REQUEST_ENTITY_TOO_LARGE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The request body was too large for the server."
    text = u"""\
The server rejected the request because the request body sent was too large."""

class STATUS_URI_TOO_LONG(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The server won't accept a URI this long %(uri_len)s."
    text = u"""\
The %(status)s status code means that the server can't or won't accept a request-uri this long."""

class STATUS_UNSUPPORTED_MEDIA_TYPE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The resource doesn't support this media type in requests."
    text = u"""\
 """

class STATUS_INTERNAL_SERVICE_ERROR(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"There was a general server error."
    text = u"""\
 """

class STATUS_NOT_IMPLEMENTED(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The server doesn't implement the request method."
    text = u"""\
 """

class STATUS_BAD_GATEWAY(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"An intermediary encountered an error."
    text = u"""\
 """

class STATUS_SERVICE_UNAVAILABLE(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"The server is temporarily unavailable."
    text = u"""\
 """

class STATUS_GATEWAY_TIMEOUT(Note):
    category = c.GENERAL
    level = l.INFO
    summary = u"An intermediary timed out."
    text = u"""\
 """

class STATUS_VERSION_NOT_SUPPORTED(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The request HTTP version isn't supported."
    text = u"""\
 """

class PARAM_STAR_QUOTED(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The '%(param)s' parameter's value cannot be quoted."
    text = u"""\
Parameter values that end in '*' have a specific format, defined in
[RFC5987](http://tools.ietf.org/html/rfc5987), to allow non-ASCII text.

The `%(param)s` parameter on the `%(field_name)s` header has double-quotes around it, which is not
valid."""

class PARAM_STAR_ERROR(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(param)s parameter's value is invalid."
    text = u"""\
Parameter values that end in '*' have a specific format, defined in
[RFC5987](http://tools.ietf.org/html/rfc5987), to allow non-ASCII text.
 
 The `%(param)s` parameter on the `%(field_name)s` header is not valid; it needs to have three
parts, separated by single quotes (')."""

class PARAM_STAR_BAD(Note):
    category = c.GENERAL
    level = l.BAD
    summary = u"The %(param)s* parameter isn't allowed on the %(field_name)s header."
    text = u"""\
Parameter values that end in '*' are reserved for non-ascii text, as explained in
[RFC5987](http://tools.ietf.org/html/rfc5987).

The `%(param)s` parameter on the `%(field_name)s` does not allow this; you should use %(param)s
without the "*" on the end (and without the associated encoding).

RED ignores the content of this parameter. 
     """

class PARAM_STAR_NOCHARSET(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The %(param)s parameter's value doesn't define an encoding."
    text = u"""\
Parameter values that end in '*' have a specific format, defined in
[RFC5987](http://tools.ietf.org/html/rfc5987), to allow non-ASCII text.

The `%(param)s` parameter on the `%(field_name)s` header doesn't declare its character encoding,
which means that recipients can't understand it. It should be `UTF-8`."""

class PARAM_STAR_CHARSET(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The %(param)s parameter's value uses an encoding other than UTF-8."
    text = u"""\
Parameter values that end in '*' have a specific format, defined in
[RFC5987](http://tools.ietf.org/html/rfc5987), to allow non-ASCII text.
 
The `%(param)s` parameter on the `%(field_name)s` header uses the `'%(enc)s` encoding, which has
interoperability issues on some browsers. It should be `UTF-8`."""

class PARAM_REPEATS(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The '%(param)s' parameter repeats in the %(field_name)s header."
    text = u"""\
Parameters on the %(field_name)s header should not repeat; implementations may handle them
differently."""

class PARAM_SINGLE_QUOTED(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The '%(param)s' parameter on the %(field_name)s header is single-quoted."
    text = u"""\
The `%(param)s`'s value on the %(field_name)s header start and ends with a single quote (').
However, single quotes don't mean anything there.

This means that the value will be interpreted as `%(param_val)s`, **not**
`%(param_val_unquoted)s`. If you intend the latter, drop the single quotes."""

class DISPOSITION_UNKNOWN(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The '%(disposition)s' Content-Disposition isn't known."
    text = u"""\
The `Content-Disposition` header has two widely-known values; `inline` and `attachment`.
`%(disposition)s` isn't recognised, and most implementations will default to handling it like
`attachment`."""

class DISPOSITION_OMITS_FILENAME(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The Content-Disposition header doesn't have a 'filename' parameter."
    text = u"""\
The `Content-Disposition` header suggests a filename for clients to use when saving the file
locally.

It should always contain a `filename` parameter, even when the `filename*` parameter is used to
carry an internationalised filename, so that browsers can fall back to an ASCII-only filename."""

class DISPOSITION_FILENAME_PERCENT(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The 'filename' parameter on the Content-Disposition header contains a '%%' character."
    text = u"""\
The `Content-Disposition` header suggests a filename for clients to use when saving the file
locally, using the `filename` parameter.

[RFC6266](http://tools.ietf.org/html/rfc6266) specifies how to carry non-ASCII characters in this
parameter. However, historically some (but not all) browsers have also decoded %%-encoded
characters in the `filename` parameter, which means that they'll be treated differently depending
on the browser you're using.

As a result, it's not interoperable to use percent characters in the `filename` parameter. Use the
correct encoding in the `filename*` parameter instead."""

class DISPOSITION_FILENAME_PATH_CHAR(Note):
    category = c.GENERAL
    level = l.WARN
    summary = u"The filename in the Content-Disposition header contains a path character."
    text = u"""\
The `Content-Disposition` header suggests a filename for clients to use when saving the file
locally, using the `filename` and `filename*` parameters.

One of these parameters contains a path character ("\" or "/"), used to navigate between
directories on common operating systems.

Because this can be used to attach the browser's host operating system (e.g., by saving a file to a
system directory), browsers will usually ignore these parameters, or remove path information.

You should remove these characters."""
    
class LINK_REV(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The 'rev' parameter on the Link header is deprecated."
    text = u"""\
The `Link` header, defined by [RFC5988](http://tools.ietf.org/html/rfc5988#section-5), uses the
`rel` parameter to communicate the type of a link. `rev` is deprecated by that specification
because it is often confusing.

Use `rel` and an appropriate relation."""

class LINK_BAD_ANCHOR(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The 'anchor' parameter on the %(link)s Link header isn't a URI."
    text = u"""\
The `Link` header, defined by [RFC5988](http://tools.ietf.org/html/rfc5988#section-5), uses the
`anchor` parameter to define the context URI for the link.

This parameter can be an absolute or relative URI; however, `%(anchor)s` is neither."""

class SET_COOKIE_NO_VAL(Note):
    category = c.GENERAL
    level=l.BAD
    summary = u"%(response)s has a Set-Cookie header that can't be parsed."
    text = u"""\
This `Set-Cookie` header can't be parsed into a name and a value; it must start with a `name=value`
structure.

Browsers will ignore this cookie."""

class SET_COOKIE_NO_NAME(Note):
    category = c.GENERAL
    level=l.BAD
    summary = u"%(response)s has a Set-Cookie header without a cookie-name."
    text = u"""\
This `Set-Cookie` header has an empty name; there needs to be a name before the `=`.

Browsers will ignore this cookie."""

class SET_COOKIE_BAD_DATE(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The %(cookie_name)s Set-Cookie header has an invalid Expires \
date."
    text = u"""\
The `expires` date on this `Set-Cookie` header isn't valid; see
[RFC6265](http://tools.ietf.org/html/rfc6265) for details of the correct format."""

class SET_COOKIE_EMPTY_MAX_AGE(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The %(cookie_name)s Set-Cookie header has an empty Max-Age."
    text = u"""\
The `max-age` parameter on this `Set-Cookie` header doesn't have a value.

Browsers will ignore the `max-age` value as a result."""

class SET_COOKIE_LEADING_ZERO_MAX_AGE(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The %(cookie_name)s Set-Cookie header has a Max-Age with a leading zero."
    text = u"""\
The `max-age` parameter on this `Set-Cookie` header has a leading zero.

Browsers will ignore the `max-age` value as a result."""

class SET_COOKIE_NON_DIGIT_MAX_AGE(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The %(cookie_name)s Set-Cookie header has a non-numeric Max-Age."
    text = u"""\
The `max-age` parameter on this `Set-Cookie` header isn't numeric.


Browsers will ignore the `max-age` value as a result."""

class SET_COOKIE_EMPTY_DOMAIN(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The %(cookie_name)s Set-Cookie header has an empty domain."
    text = u"""\
The `domain` parameter on this `Set-Cookie` header is empty.

Browsers will probably ignore it as a result."""

class SET_COOKIE_UNKNOWN_ATTRIBUTE(Note):
    category = c.GENERAL
    level=l.WARN
    summary = u"The %(cookie_name)s Set-Cookie header has an unknown attribute, '%(attribute)s'."
    text = u"""\
This `Set-Cookie` header has an extra parameter, "%(attribute)s".

Browsers will ignore it.
     """


if __name__ == '__main__':
    # do a sanity check on all of the defined messages
    import re, types
    for n, v in locals().items():
        if type(v) is types.ClassType and issubclass(v, Note) \
          and n != "Note":
            print "checking", n
            assert v.category in c.__class__.__dict__.values(), n
            assert v.level in l.__class__.__dict__.values(), n
            assert type(v.summary) is types.UnicodeType, n
            assert v.summary != "", n
            assert not re.search("\s{2,}", v.summary), n
            assert type(v.text) is types.UnicodeType, n
    #        assert v.text != "", n
