import git
import util

class Search(object):
    header_titles = ["author", "author-mail", "author-time", "author-tz",
                    "committer", "committer-mail", "committer-time", "committer-tz",
                    "summary", "previous", "filename", "\t"]
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path, odbt=git.GitDB)

        self.authors = []

    def score_all_commits(self, block):
        """
        Returns a hash of author to the contribution [0, 1] of the author for
        this particular block, using all commits of this block.

        In other words, we consider all lines of code the author has ever added
        in the past for this block.

        We normalize against the total number of line contributions ever,
        instead of the current total number of lines.

        TODO: what about lines of code the author has removed?
        """

        revs = self.rev_list(block)
        contributions, num_lines_total = self.lines_contributed_for_revs(block, revs)
        return self._score_author_contributions_(contributions, num_lines_total)

    def score_last_commit(self, block):
        """
        Implementation of Score_last_commit(author, block).

        Returns a hash of author to the contribution [0, 1] of the author
        for this particular block, using last commit of the block.
        """

        contributions, num_lines_total = self.lines_contributed(block)
        return self._score_author_contributions_(contributions, num_lines_total)

    def _score_author_contributions_(self, contributions,
            num_lines_total, *args):
        scores = {}
        for sha, data in contributions.items():
            person = data[0]
            num_lines = data[1]
            if scores.has_key(person):
                scores[data[0]] += float(data[1])
            else:
                scores[data[0]] = float(data[1])

        # Normalize.
        for k, v in scores.items():
            scores[k] = v/num_lines_total

        return scores

    def rev_list(self, block, rev='HEAD'):
        """
        Return list of revision hashes. Ordered from earliest to latest.
        """

        # We don't use the --all flag for git-rev-list. This is because the
        # --all flag will grab all references to the block, including "dangling"
        # references such as commit blobs that were thrown away.

        # We make the assumption that we don't want to use thrown-away code.
        revs = self.repo.git.rev_list(rev, block).split()
        revs.reverse()  # earliest commits first
        return revs

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
            person = Person(name, email)
            self.authors.append(person)
            return person
        return None

    def lines_contributed_for_revs(self, block, revs):
        """
        Given a block, return a dict {SHA => [Person, num lines]}.

        But 
        """
        contributions = {}  # {rev => [(Person, num lines contributed)]}
        shas = set()
        num_lines_total = 0
        for rev in revs:
            rev_contributions, num_lines_total = self.lines_contributed(block, rev)
            for sha, data in rev_contributions.items():
                if sha != rev:
                    continue

                #shas.add(sha)
                person = data[0]
                num_lines = data[1]
                contributions[rev] = [person, num_lines]
                num_lines_total += num_lines
        return contributions, num_lines_total


    def lines_contributed(self, block, rev="HEAD"):
        """
        Given a block, return a dict {SHA => [Person, num lines]}.

        This method only looks at the blame outputs produced by hash 'rev'.
        Past contributions that is overriden by later contributions is not seen.
        To see this data, use lines_contributed_for_revs().
        """

        contributions = {}      # {SHA => [Person, num lines]}
        shas = set()

        blamestr = self.repo.git.blame(rev, block, incremental=True)
        lines = blamestr.splitlines()

        num_lines_total = 0

        sha = None
        i = 0
        while i < len(lines):
            # We are at the first line of group or sub-group.
            sha, ln_orig, ln_final, ln_group = lines[i].split()
            ln_group = int(ln_group)

            num_lines_total += ln_group

            if sha not in shas:
                shas.add(sha)

                # We are at a new commit group. Figure out the author.
                author_name, author_email = None, None
                while not (author_name and author_email):
                    i += 1
                    components = lines[i].split(" ")
                    if components[0] == 'author':
                        author_name = " ".join(components[1:])
                    elif components[0] == 'author-mail':
                        author_email = " ".join(components[1:]).strip("<").strip(">")

                # Add line count to author.
                person = self.find_author(name=author_name, email=author_email,
                        add_author=True)
                if contributions.has_key(sha):
                    contributions[sha][1] += ln_group
                else:
                    contributions[sha] = [person, ln_group]
                
                # We got the data we want. Spin until we get to 'filename', which
                # marks the end of this sub-group.
                i = util.spin_lines_until(lines, i, 'filename')

                # We are now one line past 'filename'. The next line should contain
                # a SHA.
            else:
                # We are in an old sub-group, so update author's contributions.
                contributions[sha][1] += ln_group
                i = util.spin_lines_until(lines, i, 'filename')
        return contributions, num_lines_total

class Person(object):
    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __eq__(self, person):
        return self.name == person.name and self.email == person.email

    def __str__(self):
        return "Name: %s, Email: %s" % (self.name, self.email)

    def __repr__(self):
        return object.__repr__(self) + (" (Name: %s, Email: %s)" % (self.name, self.email))

class Block(object):
    """
    A Block is a git blob (file).
    """

    def __init__(self, filename):
        self.filename = filename

