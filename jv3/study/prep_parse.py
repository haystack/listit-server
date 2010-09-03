
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

KEY_CAPTURE_GROUP = 1 # assumes nth capture group contains the key
special_breaks = [ re.compile('(^|\s)(\w+):') ]
special_preps_re  = [ re.compile('(^|\s)(%s)(\s|$)' % p) for p in special_preps ] + special_breaks

def nonemin(a,b):
    if a is None: return b
    if b is None: return a
    return min(a,b)

def find_next_special_prep_idx(s):
    starts = [x.start() for x in [pre.search(s) for pre in special_preps_re] if x is not None]
    if len(starts) == 0: return None
    return min(starts)

def prep_parse(text):
    prep_bindings = {}
    for c in text.lower().strip().split('\n'):
        for pre in special_preps_re:
            search = pre.search(c)
            while search is not None:
                cpos,keyend = search.start(),search.end()
                val_end = keyend + 1 + nonemin(find_up_to_N_words_out(c[keyend+1:]), find_next_special_prep_idx(c[keyend+1:]))
                key = search.groups()[KEY_CAPTURE_GROUP] 
                val = c[keyend:val_end].strip()
                if len(val) > 0:   prep_bindings[key] = prep_bindings.get(key,[]) + [val]
                search = pre.search(c,cpos + 1)
            pass
    return prep_bindings

def try_some_notes(notes):
    for n in notes:
        print "-----------------------\n%s\n%s" % (prep_parse(n.contents),n.contents[:100])

# def verb_zero(note,tagger):
#     import nltk, nltk.corpus
#     # POS = ["CC","CD","DT","EX","FW","IN","JJ","LS","MD","NN","NNS","NNP","NNPS","PDT","POS","PRP","PRP$","RB","RBR","RBS","RP","SYM","TO","UH","VB","VBD","VBG","VBN","VBP","VBZ","WDT","WP","WP$","WRB"]
#     # VERBS = ["BE", "VB","VBD","VBG","VBN","VBP","VBZ"]
#     pos_tags = tagger.tag(nltk.word_tokenize(note.contents.lower()))
#     print pos_tags
#     print note.contents
#     print "-------"
#     return pos_tags[0] in VERBS if len(pos_tags) > 0 else False

# def verb_zero(text,tagger):
#     import nltk, nltk.corpus
#     # POS = ["CC","CD","DT","EX","FW","IN","JJ","LS","MD","NN","NNS","NNP","NNPS","PDT","POS","PRP","PRP$","RB","RBR","RBS","RP","SYM","TO","UH","VB","VBD","VBG","VBN","VBP","VBZ","WDT","WP","WP$","WRB"]
#     VERBS = ["BE", "VB","VBD","VBG","VBN","VBP","VBZ"]
#     pos_tags = tagger.tag(nltk.word_tokenize(text.lower()))
#     # print pos_tags
#     # print "-------"
#     return pos_tags[0][1] in VERBS if len(pos_tags) > 0 else False


def is_todo(text, tagger=None):
    import nltk,nltk.corpus
    VERBS = ["BE", "VB","VBD","VBG","VBN","VBP","VBZ"]
    if tagger is None:
        tagger = nltk.UnigramTagger( nltk.corpus.conll2000.tagged_sents() )
    pos_tags = tagger.tag(nltk.word_tokenize(text.lower()))
    # print pos_tags
    if len(pos_tags) == 0 : return False
    if pos_tags[0][1] in VERBS:
        return 'VERB TODO'
    if len([x[1] for x in pos_tags if x[1] in VERBS]) == 0:
        return 'IMPLICIT TODO (NO VERBS)'
    
    return False
    

def backoff_tagger(tagged_sents, tagger_classes, backoff=None):
    if not backoff:
        backoff = tagger_classes[0](tagged_sents)
        del tagger_classes[0]

    for cls in tagger_classes:
        tagger = cls(tagged_sents, backoff=backoff)
        backoff = tagger

    return backoff

word_patterns = [
    (r'^-?[0-9]+(.[0-9]+)?$', 'CD'),
    (r'.*ould$', 'MD'),
    (r'.*ing$', 'VBG'),
    (r'.*ed$', 'VBD'),
    (r'.*ness$', 'NN'),
    (r'.*ment$', 'NN'),
    (r'.*ful$', 'JJ'),
    (r'.*ious$', 'JJ'),
    (r'.*ble$', 'JJ'),
    (r'.*ic$', 'JJ'),
    (r'.*ive$', 'JJ'),
    (r'.*ic$', 'JJ'),
    (r'.*est$', 'JJ'),
    (r'^a$', 'PREP'),
]


def get_brill(train_sents=None):
    import nltk, nltk.tag
    from nltk.tag import brill
    
    if train_sents is None :  train_sents = nltk.corpus.conll2000.tagged_sents() + nltk.corpus.brown.tagged_sents()

    raubt_tagger = backoff_tagger(train_sents, [nltk.tag.AffixTagger,nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger], backoff=nltk.tag.RegexpTagger(word_patterns))

    templates = [
        brill.SymmetricProximateTokensTemplate(brill.ProximateTagsRule, (1,1)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateTagsRule, (2,2)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateTagsRule, (1,2)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateTagsRule, (1,3)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateWordsRule, (1,1)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateWordsRule, (2,2)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateWordsRule, (1,2)),
        brill.SymmetricProximateTokensTemplate(brill.ProximateWordsRule, (1,3)),
        brill.ProximateTokensTemplate(brill.ProximateTagsRule, (-1, -1), (1,1)),
        brill.ProximateTokensTemplate(brill.ProximateWordsRule, (-1, -1), (1,1))
        ]
    
    trainer = brill.FastBrillTaggerTrainer(raubt_tagger, templates)
    braubt_tagger = trainer.train(train_sents, max_rules=100, min_score=3)
    return braubt_tagger

def get_taggers(train_sents):
    ubta_tagger = backoff_tagger(train_sents, [nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger, nltk.tag.AffixTagger])
    ubat_tagger = backoff_tagger(train_sents, [nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.AffixTagger, nltk.tag.TrigramTagger])
    uabt_tagger = backoff_tagger(train_sents, [nltk.tag.UnigramTagger, nltk.tag.AffixTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger])
    aubt_tagger = backoff_tagger(train_sents, [nltk.tag.AffixTagger, nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger])    
    return { "aubtr_tagger" : nltk.tag.RegexpTagger(word_patterns, backoff=aubt_tagger),    
             "raubt_tagger" : backoff_tagger(train_sents, [nltk.tag.AffixTagger, nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger], backoff=nltk.tag.RegexpTagger(word_patterns)),
             "ubt_tagger" : backoff_tagger(train_sents, [nltk.tag.UnigramTagger, nltk.tag.BigramTagger, nltk.tag.TrigramTagger]),
             "utb_tagger" : backoff_tagger(train_sents, [nltk.tag.UnigramTagger, nltk.tag.TrigramTagger, nltk.tag.BigramTagger]), 
             "but_tagger" : backoff_tagger(train_sents, [nltk.tag.BigramTagger, nltk.tag.UnigramTagger, nltk.tag.TrigramTagger]),
             "btu_tagger" : backoff_tagger(train_sents, [nltk.tag.BigramTagger, nltk.tag.TrigramTagger, nltk.tag.UnigramTagger]),
             "tub_tagger" : backoff_tagger(train_sents, [nltk.tag.TrigramTagger, nltk.tag.UnigramTagger, nltk.tag.BigramTagger]),
             "tbu_tagger" : backoff_tagger(train_sents, [nltk.tag.TrigramTagger, nltk.tag.BigramTagger, nltk.tag.UnigramTagger])
             }
             
    
    

