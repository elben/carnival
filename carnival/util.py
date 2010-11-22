import hashlib

def anonymize(message, algorithm='hash', salt=''):
    """
    Optional arguments:
        algorithm='hash'
        algorithm='simple'
        salt - the salt added to the hashing function
    """
    if algorithm == 'hash':
        m = hashlib.sha1()
        m.update(message)
        m.update(salt)
        crypted = m.hexdigest()
    elif algorithm == 'simple':
        crypted = message
    return crypted

def spin_lines_until(lines, i, until):
    while True:
        i += 1
        components = lines[i].split(" ")
        #print "Spinning until filename: " + lines[i]

        if components[0] == 'filename':
            i += 1
            break
    return i
