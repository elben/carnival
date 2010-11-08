import git
import util
import math
import time

class Search(object):
    header_titles = ["author", "author-mail", "author-time", "author-tz",
                    "committer", "committer-mail", "committer-time", "committer-tz",
                    "summary", "previous", "filename", "\t"]
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path, odbt=git.GitDB)

        self.authors = []

    def aging_exp(self, days, lmb=0.005):
        """
        """
        return math.exp(-days*lmb)

    def aging_linear(self, days, lmb=0.5):
        """
        """

    def datetime(self, rev):
        """
        Given an object hash, return the unix time that object was created.
        """

        # The format documentation can be found at "man git-show". %H is the
        # commit hash and %at is the author-date in unix time.
        show = self.repo.git.show(rev, format="%H%n%at", name_only=True)
        lines = show.splitlines()
        return int(lines[1])

    def datetimes(self, revs):
        """
        Given a list of revisions, return a dict {commit hash: unix time}

        git show --format="commit: %H%nauthor-date: %at" --name-only e22109ebd4b5cf1e0efbef2f6ecc5f257efc24be
        """
        datetimes = {}
        for rev in revs:
            datetimes[rev] = self.datetime(rev)
        return datetimes

    def days_since(self, rev):
        now = time.time()
        then = self.datetime(rev)
        diff = float(now - then)
        return diff / 60 / 60 / 24

    def score_all_commits_over_time(self, block):
        """
        Returns a dict of author to the contribution [0, 1] of the author for
        this particular block, using all commits of this block with
        consideration to the temporal dimension.
        """

        revs = self.rev_list(block)
        datetimes = self.datetimes(revs)
        contributions, num_lines_total = self.lines_contributed_for_revs(block, revs)
        return self._score_author_contributions(contributions, aging='exp')

    def score_all_commits(self, block):
        """
        Implementation of Score_{AllCommits}(author, block).

        Returns a dict of author to the contribution [0, 1] of the author for
        this particular block, using all commits of this block.

        In other words, we consider all lines of code the author has ever added
        in the past for this block.

        We normalize against the total number of line contributions ever,
        instead of the current total number of lines.

        TODO: what about lines of code the author has removed?
        """

        revs = self.rev_list(block)
        contributions, num_lines_total = self.lines_contributed_for_revs(block, revs)
        return self._score_author_contributions(contributions)

    def score_last_commit(self, block):
        """
        Implementation of Score_{LastCommit}(author, block).

        Returns a dict of author to the contribution [0, 1] of the author
        for this particular block, using last commit of the block.
        """

        contributions, num_lines_total = self.lines_contributed(block)
        return self._score_author_contributions(contributions)

    def _score_author_contributions(self, contributions, aging=None,
            normalize=True):
        """
        Takes a dict {commit hash: {...}} and inverses it to a dict
        {Person: score}. 
        
        A person may show up multiple times in contributions, but this function
        will squish all of that into one person.
        """

        scores = {}
        total_score = 0
        for sha, data in contributions.items():
            person = data['person']
            num_lines = data['num_lines']

            score = float(num_lines)
            if aging == 'exp':
                score *= self.aging_exp(self.days_since(sha))
            elif aging == 'linear':
                score *= 1 # TODO implement

            total_score += score
            if person in scores:
                scores[person] += score
            else:
                scores[person] = score

        if normalize:
            for k, v in scores.items():
                scores[k] = v/total_score

        return scores

    def rev_list(self, block, rev='HEAD'):
        """
        Return list of commit hashes. Ordered from earliest to latest.
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
        Given a block, return a dict of commit hashes to the author and author's
        contribution for each revision in revs:

            {commit hash: {
                'author': Person
                'num_lines': integer}}

        Each commit hash has exactly one author. This is different from
        lines_contributed, which may contain more than one authors.
        """
        contributions = {}  # {rev: [(Person, num lines contributed)]}
        shas = set()
        num_lines_total = 0
        for rev in revs:
            rev_contributions, num_lines_rev = self.lines_contributed(block, rev)
            for sha, data in rev_contributions.items():
                if sha != rev:
                    continue

                #shas.add(sha)
                person = data['person']
                num_lines = data['num_lines']
                if rev in contributions:
                    contributions[rev]['num_lines'] += num_lines
                else:
                    contributions[rev] = {'person': person,
                            'num_lines': num_lines}
                num_lines_total += num_lines
        return contributions, num_lines_total


    def lines_contributed(self, block, rev="HEAD"):
        """
        Given a block, return a dict of commit hashes to the author and author's
        contribution:

            {commit hash: {
                'author': Person
                'num_lines': integer}}

        This method only looks at the blame outputs produced by commit hash 'rev'.
        Past contributions that is overriden by later contributions is not seen.
        To see this data, use lines_contributed_for_revs().
        """

        contributions = {}      # {commit hash: [Person, num lines]}
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
                if sha in contributions:
                    contributions[sha]['num_lines'] += ln_group
                else:
                    contributions[sha] = {'person': person,
                            'num_lines': ln_group}
                
                # We got the data we want. Spin until we get to 'filename', which
                # marks the end of this sub-group.
                i = util.spin_lines_until(lines, i, 'filename')

                # We are now one line past 'filename'. The next line should contain
                # a SHA.
            else:
                # We are in an old sub-group, so update author's contributions.
                contributions[sha]['num_lines'] += ln_group
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

