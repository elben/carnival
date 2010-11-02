import git

class Search(object):
    header_titles = ["author", "author-mail", "author-time", "author-tz",
                    "committer", "committer-mail", "committer-time", "committer-tz",
                    "summary", "previous", "filename", "\t"]
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path, odbt=git.GitDB)

        self.authors = []

    def find_author(self, name=None, email=None, add_author=False):
        """
        Find author with given name and/or email. If author does not exist,
        add the author if add_author is True.
        """

        for author in self.authors:
            if name and email and author.name == name and author.email == email:
                return author
            elif name and author.name == name:
                return author
            elif author.name == email:
                return author
        if add_author:
            self.authors.push(Person(name, email))
        return None

    def score_last_commit(author, block):
        # Git blame.
        pass

    def lines_contributed(self, block):
        """
        Given a block, return a hash {author: num lines contributed}.
        """

        contributions = {}

        blamestr = self.repo.git.blame(block, porcelain=True)
        lines = blamestr.splitlines()

        num_lines_total = 0

        sha = None
        i = 0
        while i < len(lines):
            # We are at the first line of a group.
            print "At line with content: " + lines[i]
            sha, ln_orig, ln_final, ln_group = lines[i].split()
            ln_group = int(ln_group)
            num_lines_total += ln_group

            # Figure out author.
            author_name = None
            author_email = None
            while not author_name:
                # TODO We see 'author' before we see 'author-mail', but
                # 'author-mail' does not exist. Find way to check if
                # 'author-mail' exists even after finding 'author'
                i += 1
                components = lines[i].split(" ")
                print "Finding authors: " + lines[i]
                if components[0] == 'author':
                    author_name = " ".join(components[1:])
                elif components[0] == 'author-mail':
                    author_email = " ".join(components[1:]).strip("<").strip(">")
                print "Author name: %s \t Author email: %s" % (author_name, author_email)

            # Add line count to author.
            person = self.find_author(name=author_name, email=author_email)
            if contributions.has_key(person):
                contributions[person] += ln_group
            else:
                contributions[person] = 0
            
            # We got the data we want. So spin through lines until we get to a
            # new group.
            spin = True
            while spin:
                i += 1
                components = lines[i].split(" ")
                print "Spinning: " + lines[i]
                if (Search.header_titles.count(components[0]) == 0 and
                        len(components) == 4):
                    # a SHA header for a new group, so quit spinning and leave
                    # this line as the current line (because it contains the
                    # SHA).
                    spin = False

        

class Person(object):
    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __eq__(self, person):
        return self.name == person.name and self.email == person.email

class Block(object):
    """
    A Block is a git blob (file).
    """

    def __init__(self, filename):
        self.filename = filename

