class UTAError(Exception):
    pass

class DatabaseError(UTAError):
    pass

class InvalidTranscriptError(UTAError):
    pass

class InvalidIntervalError(UTAError):
    pass

class InvalidHGVSVariantError(UTAError):
    pass
