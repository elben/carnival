
# TODO maybe it's easier to use a real git repo as the test...
# 

class FakeRepo(object):
    def __init__(self):
        self._git = FakeGitCommand()

    def git(self):
        return self._git

class FakeGitCommand(object):
    def __init__(self):
        self.block_names = ['file1', 'file2']
        self.blocks = {
                'file1': 'Hello, how are you doing today?',
                'file2': 'I am doing fine, thanks!',}
        self.revs = {
                'file1': ['0' * 40, '1' * 40, '2' * 40],
                'file2': ['3' * 40, '4' * 40, '5' * 40],}
    
    #def show(*args, **kwargs):
    def rev_list(self, rev, block):
        f = open('test_rev_list.txt', 'r')
        contents = f.read()
        return contents
        
    def show(rev, **kwargs):
        r  = "1111111111111111111111111111111111111111\n"
        r += "1280285449\n\n"
        r += "collectorweb_tests.py\nconfig.py"
        return r

    def blame(Rev, *args, **kwargs):
        f = open('test_blame.txt', 'r')
        contents = f.read()
        return contents
