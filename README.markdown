# Carnival

Finding who knows what in a git repository.

# Abstract

Software projects are complex. They often contain large amounts of code spread
among many developers. Furthermore, every developer may work on diﬀerent
parts of the project, resulting in developers being experts on diﬀerent parts of
the project. If a developer has a question about a certain snippet of code, who
should the developer ask for help? We introduce a new problem: using the code
base, the history of the code base, and a snippet of code, can we ﬁnd and rank
the relevant experts?

We introduce a method for ﬁnding and ranking relevant experts. We then
discuss an experiment that reveals the strengths and weaknesses of our method
and of developers’ judgements. And ﬁnally, we discuss possible improvements.

# Installing

    $ python setup.py install

# Using

    from carnival import search

    repo = search.Search("/path/to/repository/")
    files = [’file1’, ’file2’]

    lastcommits = {}
    allcommits = {}
    allcommitstime = {}

    for f in files:
        lastcommits[f] = repo.score_last_commit(f)
        allcommits[f] = repo.score_all(f)
        allcommitstime[f] = repo.score_all_commits_over_time(f

