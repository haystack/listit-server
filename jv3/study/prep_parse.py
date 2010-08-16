
# tasty parser based on prepositions 
# by emax

import re

def find_up_to_N_words_out(s,N=3):
    starts = 0
    word = re.compile('\w+(\s|$)')
    for i in range(N):
        next = word.search(s,starts)
        if next is None: return len(s)
        starts = next.end() + 1
    return starts - 1

# from wikipedia
english_prepositions = ["aboard","about","above","absent","across","after","against","along","alongside","amid","amidst","among","amongst","around","as","aside","astride","at","athwart","atop","barring","before","behind","below","beneath","beside","besides","between","betwixt","beyond","but","by","circa","concerning","despite","down","during","except","excluding","failing","following","for","from","given","in","including","inside","into","like","mid","midst","minus","near","next","of","off","on","onto","opposite","out","outside","over","pace","past","per","plus","pro","qua","regarding","round","save","since","than","through", "thru","throughout","till","times","to","toward","towards","under","underneath","unlike","until","up","upon","versus","vs.","via","with","within","without"]

special_preps = ["@","at","about","after","before","by","around","during","for","from","in","into","near","on","past","per","since","thru","through","over","until","till","to","under","via","with","w/"]
special_preps_re  = [ re.compile('(^|\s)%s(\s|$)' % p) for p in special_preps ]

def nonemin(a,b):
    if a is None: return b
    if b is None: return a
    return min(a,b)

def find_next_special_prep_idx(s):
    starts = [x.start() for x in [pre.search(s) for pre in special_preps_re] if x is not None]
    if len(starts) == 0: return None
    return min(starts)

def parse(text):
    prep_bindings = {}
    for c in text.lower().strip().split('\n'):
        for pre in special_preps_re:
            search = pre.search(c)
            while search is not None:
                cpos,keyend = search.start(),search.end()
                val_end = keyend + 1 + nonemin(find_up_to_N_words_out(c[keyend+1:]), find_next_special_prep_idx(c[keyend+1:]))
                key = c[cpos:keyend].strip()
                val = c[keyend:val_end].strip()
                if len(val) > 0:   prep_bindings[key] = prep_bindings.get(key,[]) + [val]
                search = pre.search(c,cpos + 1)
            pass
    return prep_bindings
