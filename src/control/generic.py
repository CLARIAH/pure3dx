import re
from datetime import datetime as dt, UTC
from functools import cmp_to_key as keyFromComparison

from bson.objectid import ObjectId


VERSION_COMP_RE = re.compile(
    r"""
    ([0-9]*)
    ([a-z]*)
    (-?)
    """,
    re.X,
)

OP_VERSION_RE = re.compile(
    r"""
    ^
    (
        [<>]
        =?
    )
    (
        .*
    )
    $
    """,
    re.X,
)


def utcnow():
    return dt.now(UTC)


def now():
    """The current moment in time as a isolike string value.

    Strips everything after the decimal point,
    (milliseconds and timezone).
    """

    return utcnow().isoformat().split(".")[0].replace(":", "-")


def splitComp(c):
    return [m for m in VERSION_COMP_RE.findall(c) if m[0] or m[1]]


def makeComps(v):
    return [splitComp(c) for c in v.split(".")]


def versionCompare(v1, v2):
    v1comps = makeComps(v1)
    v2comps = makeComps(v2)

    nV2 = len(v2comps)

    for (i, c1) in enumerate(v1comps):
        if i >= nV2:
            return 1

        c2 = v2comps[i]
        nC2 = len(c2)
        for (j, s1) in enumerate(c1):
            if j >= nC2:
                return 1

            s2 = c2[j]
            if s1 < s2:
                return -1
            if s1 > s2:
                return 1
    return 0


def getVersionKeyFunc():
    return keyFromComparison(versionCompare)


def attResolve(attSpec, version):
    default = attSpec.default

    if default is None:
        return attSpec

    for (k, v) in attSpec.items():
        if k == "default":
            continue

        match = OP_VERSION_RE.match(k)
        if not match:
            continue
        (op, cmpVersion) = match.group(1, 2)
        cmp = versionCompare(version, cmpVersion)
        if (
            op == "<"
            and cmp < 0
            or op == "<="
            and cmp <= 0
            or op == ">"
            and cmp > 0
            or op == ">="
            and cmp > 0
        ):
            return v

    return default


class AttrDict(dict):
    """Turn a dict into an object with attributes.

    If non-existing attributes are accessed for reading, `None` is returned.

    See these links on stackoverflow:

    *   [1](https://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute)
    *   [2](https://stackoverflow.com/questions/16237659/python-how-to-implement-getattr)
        especially the remark that

        > `__getattr__` is only used for missing attribute lookup

    We also need to define the `__missing__` method in case we access the underlying
    dict by means of keys, like `xxx["yyy"]` rather then by attribute like `xxx.yyy`.
    """

    def __init__(self, *args, **kwargs):
        """Create the data structure from incoming data."""
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __missing__(self, key, *args, **kwargs):
        """Provide a default when retrieving a non-existent member.

        This method is used when using the `.key` notation for accessing members.
        """
        return None

    def __getattr__(self, key, *args, **kwargs):
        """Provide a default when retrieving a non-existent member.

        This method is used when using the `[key]` notation for accessing members.
        """
        return None

    def deepdict(self):
        return deepdict(self)


def deepdict(info):
    """Turns an `AttrDict` into a `dict`, recursively.

    Parameters
    ----------
    info: any
        The input dictionary. We assume that it is a data structure built by
        `tuple`, `list`, `set`, `frozenset`, `dict` and atomic types such as
        `int`, `str`, `bool`.
        We assume there are no user defined objects in it, and no generators
        and functions.

    Returns
    -------
    dict
        A dictionary containing the same info as the input dictionary, but where
        each value of type `AttrDict` is turned into a `dict`.
    """
    if isinstance(info, dt):
        return info.isoformat()

    if isinstance(info, ObjectId):
        return str(info)

    tp = type(info)

    return (
        dict({k: deepdict(v) for (k, v) in info.items()})
        if tp in {dict, AttrDict}
        else tuple(deepdict(item) for item in info)
        if tp is tuple
        else frozenset(deepdict(item) for item in info)
        if tp is frozenset
        else [deepdict(item) for item in info]
        if tp is list
        else {deepdict(item) for item in info}
        if tp is set
        else info
    )


def deepAttrDict(info, preferTuples=False):
    """Turn a `dict` into an `AttrDict`, recursively.

    Parameters
    ----------
    info: any
        The input dictionary. We assume that it is a data structure built by
        `tuple`, `list`, `set`, `frozenset`, `dict` and atomic types such as
        `int`, `str`, `bool`.
        We assume there are no user defined objects in it, and no generators
        and functions.
    preferTuples: boolean, optional False
        Lists are converted to tuples.

    Returns
    -------
    AttrDict
        An `AttrDict` containing the same info as the input dictionary, but where
        each value of type `dict` is turned into an `AttrDict`.
    """
    tp = type(info)

    return (
        AttrDict(
            {k: deepAttrDict(v, preferTuples=preferTuples) for (k, v) in info.items()}
        )
        if tp in {dict, AttrDict}
        else tuple(deepAttrDict(item, preferTuples=preferTuples) for item in info)
        if tp is tuple or (tp is list and preferTuples)
        else frozenset(deepAttrDict(item, preferTuples=preferTuples) for item in info)
        if tp is frozenset
        else [deepAttrDict(item, preferTuples=preferTuples) for item in info]
        if tp is list
        else {deepAttrDict(item, preferTuples=preferTuples) for item in info}
        if tp is set
        else info
    )
