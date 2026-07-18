# GU Functions Library (C) Alexander Guryev, 2026 | https://alexguryev.com

from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
import shutil
import threading
import uuid
import zipfile

__version__ = "1.9.0"  # maj:arch.changes . min:new functionality . tuning:fixes,tuning

_ILLEGAL_FILENAME_CHARS = "/ \"\'\\,.;:#$!?@%*"

# #########################################################################
# ############################## MISC UTILS ###############################
# #########################################################################

def conclear():  # clear console log
    print("\033[H\033[J", end="", flush=True)


# #########################################################################
def conlog(s_in):  # colored console print / ^X = color code / ~ = reset color
    colors = {
        "R": "\033[91m",  # red
        "G": "\033[32m",  # green / 92 = bright
        "B": "\033[94m",  # blue
        "C": "\033[36m",  # cyan / 96 = bright
        "M": "\033[95m",  # magenta
        "Y": "\033[93m",  # yellow
        "N": "\033[33m",  # brown
        "P": "\033[35m",  # purple
        "A": "\033[90m",  # gray
        "W": "\033[97m",  # white
        "U": "\033[4m"    # underline
    }
    colored_text = ""
    i = 0
    s = str(s_in)
    while i < len(s):
        char = s[i]
        if char == "^":  # color marker
            i += 1
            if i < len(s):
                next_char = s[i]
                colored_text += colors.get(next_char, next_char)
        elif char == "~":  # color reset
            colored_text += "\033[0m"
        else:
            colored_text += char
        i += 1
    print(colored_text)


# #########################################################################
def conlog_arr(arr):  # print list of arr.elems
    print(f"\n{json.dumps(arr, indent=2, ensure_ascii=False)}\n")


# #########################################################################
def arr_unify(arr_in):  # remove duplicates from array (preserve order)
    seen = set()
    return [x for x in arr_in if not (x in seen or seen.add(x))]


# #########################################################################
def split_list_into_chunks(lst, n):  # split list into chunks of size n
    return [lst[i:i + n] for i in range(0, len(lst), n)]


# #########################################################################
def get_key_by_value(dictionary, target_value):  # get dict key from value
    return next((k for k, v in dictionary.items() if v == target_value), None)


# #########################################################################
# ############################ STRING UTILS ###############################
# #########################################################################

def get_datetime_str(dateonly=False, timeonly=False, filesafe=True, utcplus=3): # filesafe: "YYYY_MM_DD_HH_MM_SS" / "YYYY_MM_DD" / "HH_MM_SS"  ,   not-filesafe: "YYYY_MM_DD / HH:MM:SS"
    # https://strftime.org/
    now = datetime.now(timezone(timedelta(hours=utcplus)))  # UTC + utcplus
    if dateonly:
        return now.strftime("%Y_%m_%d" if filesafe else "%Y/%m/%d")
    if timeonly:
        return now.strftime("%H_%M_%S" if filesafe else "%H:%M:%S")
    return now.strftime("%Y_%m_%d_%H_%M_%S" if filesafe else "%Y/%m/%d | %H:%M:%S")


# #########################################################################
def sec_to_hms(s):  # seconds to hh:mm:ss (always HH:MM:SS, works for >24h)
    s = int(s)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


# #########################################################################
def safe_string(s_in, forfile=True): # make string safe for filename or prompt?
    s_out = s_in
    if forfile:
        chars = " ,;:#$~?@%*^&<>{}" # filename-safe
    else:
        chars = ";#$?%" # prompt-safe

    fix = any(c in s_in for c in chars) # detect fact of illegal chars

    if forfile:
        s1 = s_out.replace("\\", "/")
        if s1 != s_out:
            fix = True
            s_out = s1
    for c in chars:
        s_out = s_out.replace(c, "_" if forfile else " ")

    return s_out, fix


# #########################################################################
def check_arr_elem_in_str(arr, s): # check if any array element presents as substring in S
    return any(a in s for a in arr)


# #########################################################################
def strlist_to_str(strlist): # join list of strings with comma separator
    return ", ".join(strlist)


# #########################################################################
def int_2_str_z(i, zeros=1): # convert int to str w/leading zeros
    return str(i).zfill(zeros)


# #########################################################################
def illeg_in_name(s_in): # does string contain illegal for filenames
    return any(c in s_in for c in _ILLEGAL_FILENAME_CHARS)


# #########################################################################
def legalize_name(s_in, CutNum=False): # cut .### number from name
    try:
        head, tail = s_in.rsplit(".", 1)
        if tail.isnumeric() and CutNum:
            s_out = head
        else:
            s_out = s_in
    except Exception: s_out = s_in

    for ch in _ILLEGAL_FILENAME_CHARS:
        if ch in s_out:
            s_out = s_out.replace(ch, "_")

    return s_out


# #########################################################################
def camelcase_name(s_in): # recreate name in CamelCaseNotation
    s_out = s_in
    # convert all separators to space
    s_out = s_out.replace("_", " ")
    s_out = s_out.replace(".", " ")
    slst = s_out.split(" ") # split by space
    s_out = ""
    for s in slst:
        if len(s) > 0:
            s1 = s[0]
            s2 = s[1:]
            s_out += s1.upper() + s2 # manual capitalize to keep existing CamelCase

    return s_out


# #########################################################################
def get_str_tail_number(s_in): # get the number from tail of string
    i = len(s_in)-1
    if i < 0:
        return 0

    s = []
    while i >= 0: # get digits from tail
        if s_in[i].isdigit():
            s.append(s_in[i])
        else:
            break
        i -= 1

    if not s:
        return 0
    return int("".join(s[::-1])) # reversed string


# #########################################################################
def unique_shortid(length=8): # create 1..32-char uuid-string
    return uuid.uuid4().hex[:(length if (length > 0 and length <= 32) else 8)]


# #########################################################################
# ############################# FILE UTILS ################################
# #########################################################################

def get_filenameext(fpath): # return tuple (name, ext)
    return os.path.splitext(os.path.basename(fpath))


# #########################################################################
def get_pathsplit(fpath): # return tuple (dir, name, ext)
    dir = os.path.dirname(fpath)
    name, ext = os.path.splitext(os.path.basename(fpath))
    return dir, name, ext


# #########################################################################
def get_filedir(fpath):
    return fpath if os.path.isdir(fpath) else os.path.dirname(fpath)


# #########################################################################
def make_unique_filename(given_path, digits=5, reserve=False): # unique-numbered filename from a full path / reserve: atomically create the file to avoid TOCTOU races
    if not os.path.exists(given_path):
        if not reserve:
            return given_path
        fdir0 = os.path.dirname(os.path.normpath(given_path))
        if fdir0:
            os.makedirs(fdir0, exist_ok=True)
        try: # try to reserve given_path itself first (no numbering needed if nobody raced us)
            fd = os.open(given_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return given_path
        except FileExistsError:
            pass # someone else created it concurrently -> fall through to numbered reservation below

    # else make a new name
    if digits < 1: digits = 1 # clamp lower

    fpath = os.path.normpath(given_path)
    fdir = os.path.dirname(fpath)
    fname, fext = get_filenameext(fpath)
    if fdir:
        os.makedirs(fdir, exist_ok=True)

    #find existing files by template <name>_#####<.ext>
    pattern = fr"^.+?_[0-9]{{{digits}}}\.[a-zA-Z0-9]+$"
    prefix = f"{fname.lower()}_"
    match_files = []
    try:
        for f in os.listdir(fdir):
            if re.match(pattern, f):
                if f.lower().endswith(fext.lower()) and f.lower().startswith(prefix):
                    match_files.append(f)
    except Exception: pass

    num = 1
    if match_files: # some found -> pick max parsed int, not lexicographic max
        nums = []
        for f in match_files:
            n, e = os.path.splitext(f)
            nums.append(int(n[len(n)-digits:]))
        num = max(nums) + 1

    while True:
        new_path = os.path.join(fdir, f"{fname}_{str(num).zfill(digits)}{fext}") #insert formatted num string

        if not reserve:
            return new_path

        try: # atomic exclusive create -> guarantees uniqueness under concurrency (works on Windows and POSIX)
            fd = os.open(new_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return new_path
        except FileExistsError:
            num += 1 # taken (maybe by a name the scan above cannot see) -> advance, never rescan or we may never converge


# #########################################################################
def is_media_file(path):  # check media extensions
    ext = os.path.splitext(str(path))[1].lower()
    return ext in {".png", ".jpg", ".wav", ".mp3", ".mp4"}


# #########################################################################
def calc_SHA256(file_path):  # calculate hash 256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


# #########################################################################
_datelog_lock = threading.Lock() # serializes concurrent write_datelog() calls from multiple threads


# #########################################################################
def write_datelog(rootpath, text, indent=0, max_bytes=0): # write logfile @ current date / path to log, message, indent level / max_bytes: 0=off, else rotate current file to <date>.<seq>.log when it grows past this size
    date_str = get_datetime_str(dateonly=True)
    fpath = os.path.join(rootpath, f"{date_str}.log")
    if indent > 0:
        text = str("    " * indent) + text
    text += "\n"

    with _datelog_lock:
        os.makedirs(rootpath, exist_ok=True)
        if max_bytes > 0 and os.path.exists(fpath) and os.path.getsize(fpath) >= max_bytes:
            seq = 1 # find next free rotation sequence number for today's date
            rotated_pattern = re.compile(fr"^{re.escape(date_str)}\.([0-9]+)\.log$")
            for f in os.listdir(rootpath):
                m = rotated_pattern.match(f)
                if m:
                    seq = max(seq, int(m.group(1)) + 1)
            os.rename(fpath, os.path.join(rootpath, f"{date_str}.{seq}.log"))

        with open(fpath, "a", encoding="utf-8") as file:
            file.write(text)


# #########################################################################
def check_archive(arch_path, extensions):
    if os.path.splitext(arch_path)[1].lower() != ".zip":
        return 0, "Not a ZIP!"

    count = 0
    try:
        with zipfile.ZipFile(arch_path, "r") as zip_file:
            count = len(zip_file.namelist())
            for member in zip_file.infolist():
                name = member.filename.strip()
                ext = os.path.splitext(name)[1].lower()

                if "/" in name or "\\" in name:
                    return 0, f"No subfolders allowed in archive: '{member.filename}'"

                if member.file_size == 0:
                    return 0, f"No empty files allowed in archive: '{member.filename}'"

                if not ext:
                    return 0, f"Unknown file type: '{member.filename}'"
                if ext not in extensions:
                    return 0, f"Unknown file type: '{member.filename}'"
    except Exception as e:
        return 0, f"Unzip error: {e}"

    return count, ""


# #########################################################################
def unpack_archive(arch_path, extr_root, temporary=True):
    extract_path = os.path.join(extr_root, unique_shortid()) if temporary else extr_root
    os.makedirs(extract_path, exist_ok=True)
    try:
        with zipfile.ZipFile(arch_path, "r") as zip_file:
            real_extract_path = os.path.realpath(extract_path)
            for member in zip_file.infolist(): # defensive zip-slip check: reject before extracting anything
                if os.path.isabs(member.filename):
                    return None, "Unsafe path in archive!"
                member_path = os.path.realpath(os.path.join(extract_path, member.filename))
                try:
                    inside = os.path.commonpath([real_extract_path, member_path]) == real_extract_path
                except ValueError: # different drives / unrelated roots -> certainly outside
                    inside = False
                if not inside:
                    return None, "Unsafe path in archive!"
            zip_file.extractall(extract_path)
    except Exception as e:
        return None, f"Unzip error: {e}"

    return extract_path, ""


# #########################################################################
def pack_archive_unique(all_files, fpath): # pack archive + make unique names if duplicate
    try:
        with zipfile.ZipFile(fpath, "w", zipfile.ZIP_DEFLATED) as zipf:
            added_filenames = set()
            for f in all_files:
                fname, fext = get_filenameext(f)
                counter = 1 # prevent name duplicates in ZIP
                new_fname = f"{fname}{fext}"
                while new_fname in added_filenames:
                    new_fname = f"{fname}_{str(counter).zfill(4)}{fext}"
                    counter += 1
                zipf.write(f, new_fname)
                added_filenames.add(new_fname)
        return True

    except Exception:
        return False


# #########################################################################
def rem_arch_tmp(extract_path):
    try:
        shutil.rmtree(extract_path)
    except Exception:
        return False

    return True


# #########################################################################
# ############################## NET UTILS ################################
# #########################################################################

def get_local_ip():  # get client ip-address string
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1)) # fake connection
            #s.connect(("8.8.8.8", 80)) # wait for external DNS / not for LAN
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
