import os
import ntpath
import fnmatch
import re

file_suffix = re.compile('-[0-9]+$')

def get_path_library(mode):
    if mode == 'win':
        return ntpath
    else:
        return os.path

def split_path(filepath, mode='win'):
    path = get_path_library(mode)
    if isinstance(filepath, list):
        filepath = path.join(*filepath)

    dirname = filepath
    path_split = []
    while True:
        dirname,leaf = path.split(dirname)
        if (leaf):
            path_split = [leaf] + path_split #Adds one element, at the beginning of the list
        else:
            path_split = [dirname] + path_split # Adds also the drive
            break

    return path_split

def absolute_path(filepath, mode='win'):
    path = get_path_library(mode)
    if isinstance(filepath, list):
        filepath = path.join(*filepath)
    path_split = split_path(filepath)

    return path.abspath(path.join(*path_split))


def find_files(startdir, pattern, mode='win'):
    path = get_path_library(mode)
    results = []
    for base, dirs, files in os.walk(startdir):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(absolute_path([base,f]) for f in goodfiles)
    return results

def clean_filename(filename, mode='win'):
    path = get_path_library(mode)
    bad_chars = ":/'"
    return ''.join('_' if c in bad_chars else c for c in filename)


# return info from a path such as dirname, extension, etc.
# if we specify a part (dirname, filename, rootname, extension) we get only that part
# else we get all these info as a dictionary
def extract_path_parts(f, part=None, mode='win'):
    path = get_path_library(mode)
    dirname,filename = path.split(f)
    rootname,extension = path.splitext(filename)
    path_parts = {}
    path_parts['dirname'] = dirname
    path_parts['filename'] = filename
    path_parts['rootname'] = rootname
    path_parts['extension'] = extension[1:]

    try:
        path_parts['suffix'] = file_suffix.search(rootname).group(0)
        path_parts['rootname_nosuffix'] = rootname[:-len(path_parts['suffix'])]
    except AttributeError:
        path_parts['suffix'] = None
        path_parts['rootname_nosuffix'] = path_parts['rootname']

    if part:
        return path_parts[part]
    else:
        return path_parts

def delete_file(f):
    os.remove(f)

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
