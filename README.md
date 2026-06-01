# gu_funclib

GU Functions Library — personal Python utilities for everyday scripting tasks.

## Install

```bash
pip install git+https://github.com/alexguryev/gu_funclib.git
```

## Usage

```python
from gu_funclib import conlog, get_datetime_str, make_unique_filename
```

## Functions

### MISC UTILS
| Function | Description |
|---|---|
| `conclear()` | Clear console |
| `conlog(s)` | Colored print — `^R` red, `^G` green, `^B` blue, `~` reset |
| `conlog_arr(arr)` | Pretty-print list/dict |
| `arr_unify(arr)` | Remove duplicates, preserve order |
| `split_list_into_chunks(lst, n)` | Split list into chunks of size n |
| `get_key_by_value(dict, value)` | Reverse dict lookup |

### STRING UTILS
| Function | Description |
|---|---|
| `get_datetime_str(dateonly, timeonly, filesafe, utcplus)` | Datetime string, UTC+ time shift |
| `sec_to_hms(s)` | Seconds → `hh:mm:ss` |
| `safe_string(s, forfile)` | Replace illegal chars for filename or prompt |
| `check_arr_elem_in_str(arr, s)` | Check if any array element is substring of s |
| `strlist_to_str(lst)` | Join list with `, ` |
| `int_2_str_z(i, zeros)` | Integer with leading zeros |
| `illeg_in_name(s)` | Detect illegal filename chars |
| `legalize_name(s, CutNum)` | Replace illegal chars with `_` |
| `camelcase_name(s)` | Convert to CamelCase |
| `get_str_tail_number(s)` | Extract trailing number from string |
| `unique_shortid(length)` | UUID-based short ID (1–32 chars) |

### FILE UTILS
| Function | Description |
|---|---|
| `get_filenameext(path)` | `(name, ext)` tuple |
| `get_pathsplit(path)` | `(dir, name, ext)` tuple |
| `get_filedir(path)` | Directory of file or path itself if dir |
| `make_unique_filename(path, digits)` | Auto-numbered filename to avoid overwrite |
| `is_media_file(path)` | Check for `.png .jpg .wav .mp3 .mp4` |
| `calc_SHA256(path)` | SHA-256 hex digest |
| `write_datelog(rootpath, text, indent)` | Append to daily `.log` file |
| `check_archive(path, extensions)` | Validate ZIP contents |
| `unpack_archive(path, dest, temporary)` | Extract ZIP |
| `pack_archive_unique(files, path)` | Create ZIP with deduplicated filenames |
| `rem_arch_tmp(path)` | Remove temp extraction folder |

### NET UTILS
| Function | Description |
|---|---|
| `get_local_ip()` | Local IP address string |

## License

MIT
