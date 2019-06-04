class PathLike:

    # This dict is populated at runtime by all classes marked with @PathLike
    classes = {}

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, cls):
        self.classes[self.prefix] = cls
        return cls
