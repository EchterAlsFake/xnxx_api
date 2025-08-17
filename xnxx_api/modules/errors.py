class InvalidUrl(Exception):
    def __init__(self, msg):
        self.msg = msg


class InvalidResponse(Exception):
    def __init__(self, msg):
        self.msg = msg


class RegionBlocked(Exception):
    def __init__(self, msg):
        self.msg = msg