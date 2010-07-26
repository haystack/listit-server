import re

def grabUrls(text):
    """Given a text string, returns all the urls we can find in it."""
    return url_re.findall(text)


urls = '(?: %s)' % '|'.join("""http telnet gopher file wais
ftp""".split())
ltrs = r'\w'
gunk = r'/#~:.?+=&%@!\-'
punc = r'.:?\-'
any = "%(ltrs)s%(gunk)s%(punc)s" % { 'ltrs' : ltrs,
                                     'gunk' : gunk,
                                     'punc' : punc }

url = r"""
    \b                            # start at word boundary
        %(urls)s    :             # need resource and a colon
        [%(any)s]  +?             # followed by one or more
                                  #  of any valid character, but
                                  #  be conservative and take only
                                  #  what you need to....
    (?=                           # look-ahead non-consumptive assertion
            [%(punc)s]*           # either 0 or more punctuation
            (?:   [^%(any)s]      #  followed by a non-url char
                |                 #   or end of the string
                  $
            )
    )
    """ % {'urls' : urls,
           'any' : any,
           'punc' : punc }

url_re = re.compile(url, re.VERBOSE | re.MULTILINE)


def _test():
    sample = """hello world, this is an url:
                http://python.org.  Can you find it?"""
    match = url_re.search(sample)
    print "Here's what we found: '%s'" % match.group(0)

if __name__ == '__main__':
    _test()

