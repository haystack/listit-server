import re

dows = ["mon", "monday", "lundi",
             "tues", "tue", "tuesday", "mardi",
             "wed", "wednesday", "weds", "mercredi",
             "thu", "thurs", "thur", "thursday", "jeudi",
             "fr", "fri", "friday", "vendredi",
             "sat", "saturday", "samedi",
             "sun", "sunday", "dimanche"];

month_exprs = ["jan","january","janvier"
               "feb","february","fevrier"
               "mar","march","mars",
               "apr","april","avril",
               "may","mai",
               "jun","june","juin",
               "aug","august","aout",
               "sept","september","septembre","sep",
               "oct","october","octobre",
               "nov","november","novembre",
               "dec","december","decembre"]


# 1-9,10,11,12
# in: jan 3rd, 2009  | aug 12, 2009 | sept 2 2009
full_mdy = [ "%s( )+\d{1,2}(nd|th|rd)?,?(( )+\d{2,4})?" % m for m in month_exprs ]
# lets in too many decimals 22.4 short_mdy = [ "\d{1,2}[/.-]\d{1,2}([/.-]\d{2,4})?" ]
#|(\d|1[0-2])[\-](\d|[0-3]\d)([\-]\d{2,4})?)|((\d|1[0-2])[.](\d|[0-3]\d)[.]\d{2,4})|((\d|1[0-2])/(\d|[0-3]\d)(/\d{2,4})?)" ]
## 9/23; 9/23/09; 9/23/2009;  23/9/2009 (european); 23-9 9-23 9/23 9/23/2009, 9.23.2009 but NOT 8.23
short_mdy = [ "((([0-3]\d)|\d)/(([0-3]\d)|\d)(/\d{2,4})?)|" + "((([0-3]\d)|\d)-(([0-3]\d)|\d)(-\d{2,4})?)|" +  "((\d|([0-3]\d))\.(\d|([0-3]\d))\.\d{2,4})"]

## 8:00pm or 8:00 or 8pm or 22:00 or 22:00h
time = ["((0?[1-9])|(1[012]))(:[0-5]\d)(\ ?[ap]m)|((0?[1-9])|(1[012]))(:[0-5]\d)|((0?[1-9])|(1[012]))(\ ?[ap]m)|(([01]?\d)|(2[0-3]))(:[0-5]\d)(h)?"]

## mon @ 4pm 
## not exactly right, since tues@22:33pm is valid
dow_exprs = [ ("(^|\s+)%s\s+(( )*(@|(at))( )*(((([012]?[1-9])|(1[012]))(:?[0-5]\d)?(\ ?[ap]m)?)))?" % d) for d in dows]  

all_ = dow_exprs + full_mdy + short_mdy + time

_re_cache = {}
intersects = lambda s1,s2: s1[0] < s2[1] and s1[1] > s2[0]
width = lambda span: span[1]-span[0]
maxidx = lambda l:  l.index( max(l) )

## max-span algorithm
def date_matches(s,ress=all_):
    import re
    global _re_cache
    starts = set([])    
    find_isect_with_starts = lambda span: [ x for x in starts if intersects(span,x) ]    
    for res in ress:
        exp = None
        if _re_cache.get(res,None):
            exp = _re_cache[res]
        else:
            exp = re.compile(res)
        hit = exp.search(s)
        while hit:
            span = hit.span()
            intersecting_spans = find_isect_with_starts(span)            
            spen = list(set([span] + intersecting_spans ))
            widest_span = spen[maxidx( [width(x) for x in spen ])]
            [starts.remove(i) for i in intersecting_spans if i in starts]
            starts.add(widest_span)            
            hit = exp.search(s,hit.end())
        pass
    print starts
    return starts

note_date_count = lambda s: {"date_time_exprs" : len(date_matches(s["contents"]))} ##reduce(plus, [ count_regex_matches(f,s) for f in all_ ])

def d(s):
    dm = list(date_matches(s))
    for d in dm:
        print s[d[0]:d[1]]

        # "(?n:^(?=\d)((?<month>(0?[13578])|1[02]|(0?[469]|11)(?!.31)|0?2(?(.29)(?=.29.((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|(16|[2468][048]|[3579][26])00))|(?!.3[01])))(?<sep>[-./])(?<day>0?[1-9]|[12]\d|3[01])\k<sep>(?<year>(1[6-9]|[2-9]\d)\d{2})(?(?=\x20\d)\x20|$))?(?<time>((0?[1-9]|1[012])(:[0-5]\d){0,2}(?i:\x20[AP]M))|([01]\d|2[0-3])(:[0-5]\d){1,2})?$)"

        # # in:         
        # "((((0[1-9])|([1-2][0-9])|(3[0-1]))|([1-9]))\x2F(((0[1-9])|(1[0-2]))|([1-9]))\x2F(([0-9]{2})|(((19)|([2]([0]{1})))([0-9]{2}))))",

        # # in : 11/24/0004 11:59 PM | 2.29.2008 | 02:50:10 ; out: 12/33/1020 | 2/29/2005 | 13:00 AM
        # "((^(10|12|0?[13578])([/])(3[01]|[12][0-9]|0?[1-9])([/])((1[8-9]\d{2})|([2-9]\d{3}))$)|(^(11|0?[469])([/])(30|[12][0-9]|0?[1-9])([/])((1[8-9]\d{2})|([2-9]\d{3}))$)|(^(0?2)([/])(2[0-8]|1[0-9]|0?[1-9])([/])((1[8-9]\d{2})|([2-9]\d{3}))$)|(^(0?2)([/])(29)([/])([2468][048]00)$)|(^(0?2)([/])(29)([/])([3579][26]00)$)|(^(0?2)([/])(29)([/])([1][89][0][48])$)|(^(0?2)([/])(29)([/])([2-9][0-9][0][48])$)|(^(0?2)([/])(29)([/])([1][89][2468][048])$)|(^(0?2)([/])(29)([/])([2-9][0-9][2468][048])$)|(^(0?2)([/])(29)([/])([1][89][13579][26])$)|(^(0?2)([/])(29)([/])([2-9][0-9][13579][26])$))",
                
        # # in:  31/12/2003 11:59:59 PM | 29-2-2004 | 01:45:02
        # # out: 12/31/2003 | 29.02.2005 | 13:30 PM
        # "(?=\d)(?:(?:31(?!.(?:0?[2469]|11))|(?:30|29)(?!.0?2)|29(?=.0?2.(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00)))(?:\x20|$))|(?:2[0-8]|1\d|0?[1-9]))([-./])(?:1[012]|0?[1-9])\1(?:1[6-9]|[2-9]\d)?\d\d(?:(?=\x20\d)\x20|$))?(((0?[1-9]|1[012])(:[0-5]\d){0,2}(\x20[AP]M))|([01]\d|2[0-3])(:[0-5]\d){1,2})?",
        
        # ## yy/mm/dd
        # "(?:(?:(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00)))(\/|-|\.)(?:0?2\1(?:29)))|(?:(?:(?:1[6-9]|[2-9]\d)?\d{2})(\/|-|\.)(?:(?:(?:0?[13578]|1[02])\2(?:31))|(?:(?:0?[1,3-9]|1[0-2])\2(29|30))|(?:(?:0?[1-9])|(?:1[0-2]))\2(?:0?[1-9]|1\d|2[0-8]))))",

        # ## 8am | 8 am | 8:00 am
        # ## 8a | 8 a | 8:00 a
        # "([0-9]|[0-1][0-9]|[2][0-3]):([0-5][0-9])(\s{0,1})(AM|PM|am|pm|aM|Am|pM|Pm{2,2})$)|(^([0-9]|[1][0-9]|[2][0-3])(\s{0,1})(AM|PM|am|pm|aM|Am|pM|Pm{2,2})",


        

        

        




             
             
             
             
             
             
             
