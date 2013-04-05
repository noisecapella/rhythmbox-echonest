def sanitize(s):
    # make work lowercase, remove spaces and otherwise scrunch so that
    # "The Yes" also matches "Yes", just in case both names exist in library
    s = s.lower().replace(" ", "").replace("'", "")
    if s[:4] == "the ":
        s = s[4:]
    return s

