def spin_lines_until(lines, i, until):
    while True:
        i += 1
        components = lines[i].split(" ")
        #print "Spinning until filename: " + lines[i]

        if components[0] == 'filename':
            i += 1
            break
    return i
