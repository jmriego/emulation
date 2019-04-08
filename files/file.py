import os
import ntpath
import fnmatch
import re

file_suffix = re.compile('-[0-9]+$')


class File:
    def __init__(self, f, basedir='', mode='win'):
        path = ntpath if mode == 'win' else os.path
        self.mode = mode
        if isinstance(f, list):
            f = path.join(*f)

        self.basedir = basedir
        self.path = f
        self.dirname, self.filename = path.split(f)
        self.rootname, self.extension = path.splitext(self.filename)

        # remove dot from extension
        self.extension = self.extension[1:]

        try:
            # suffix is the -01 at the end of the file name
            self.suffix = file_suffix.search(self.rootname).group(0)
            self.rootname_nosuffix = self.rootname[:-len(self.suffix)]
        except AttributeError:
            self.suffix = None
            self.rootname_nosuffix = self.rootname

    @property
    def split_path(self):
        if not hasattr(self, '_split_path'):
            path = ntpath if self.mode == 'win' else os.path
            drive, head = path.splitdrive(self.path)
            normalized_path = path.normpath(head)
            self._split_path = normalized_path.split(path.sep)
            if drive:
                self._split_path[0] = drive + path.sep
            # dirname = self.path
            # path_split = []
            # while True:
            #     dirname,leaf = path.split(dirname)
            #     if (leaf):
            #         path_split = [leaf] + path_split #Adds one element, at the beginning of the list
            #     else:
            #         path_split = [dirname] + path_split # Adds also the drive
            #         break
            # self._split_path = path_split
        return self._split_path

    @property
    def absolute_dir(self):
        path = ntpath if self.mode == 'win' else os.path
        path_split = self.split_path
        return path.abspath(path.join(*path_split[:-1]))

    @property
    def absolute(self):
        path = ntpath if self.mode == 'win' else os.path
        path_split = self.split_path
        return path.abspath(path.join(self.basedir, *path_split))

    def __repr__(self):
        fmt = 'File({})'
        return fmt.format(self.path)

    def __str__(self):
        return unicode(self.absolute).encode('utf-8')

    def __unicode__(self):
        return self.absolute

    def delete(self):
        os.remove(self.absolute)


def find_files(startdir, pattern, mode='win', as_file=False):
    path = ntpath if mode == 'win' else os.path
    startdir = File(startdir).absolute
    results = []
    for base, dirs, files in os.walk(startdir):
        goodfiles = fnmatch.filter(files, pattern)
        if as_file:
            rel_dir = path.relpath(base, startdir)
            results.extend(File([rel_dir, f], basedir=startdir) for f in goodfiles)
        else:
            results.extend(File([base, f]).absolute for f in goodfiles)
    return results


# TODO better error exception solving
def rename_files(old_files, new_files):
    already_renamed_tmp = []
    for f in old_files:
        try:
            os.rename(f, f+'.tmp')
            already_renamed_tmp.append(f)
        except OSError:
            for f in already_renamed_tmp:
                os.rename(f+'.tmp', f)

    for old, new in zip(old_files, new_files):
        try:
            os.rename(old+'.tmp', new)
        except OSError:
            pass
