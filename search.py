import git

class Search(object):
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path, odbt=git.GitDB)

    def authors(self, filename, rev="head"):
        """
        The author contribuations for a file at a rev.

        :return:
            A list of tuples, where each tuple contains
            (author, number of lines contributed).
        """

        """
        commit = self.repo.commit(rev)
        obj = commit/filename

        blames = self.repo.blame(rev, filename)

        if obj.type == "blob":
            repo.
        elif obj.type == "tree":
            pass

        """
        
        blame = self.repo.git.blame(filename, incremental=True)
        print blame

