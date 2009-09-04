
def is_english(s):
    try:
        le = s.encode('utf-8','ignore')
        return s == le
    except:
        pass
    return False
    
