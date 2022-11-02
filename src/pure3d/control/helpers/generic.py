def htmlEsc(val):
    """Escape certain HTML characters by HTML entities.

    To prevent them to be interpreted as HTML
    in cases where you need them literally.
    """

    return (
        ""
        if val is None
        else (
            str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
        )
    )


class AttrDict(dict):
    """Turn a dict into an object with attributes

    If non-existing attributes are accessed for reading, `None` is returned.

    See:
    https://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute

    And:
    https://stackoverflow.com/questions/16237659/python-how-to-implement-getattr
    (especially the remark that

    > `__getattr__` is only used for missing attribute lookup

    )
    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, key, *args, **kwargs):
        return None
