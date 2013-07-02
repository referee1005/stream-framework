

class SerializationException(Exception):

    '''
    Raised when encountering invalid data for serialization
    '''
    pass


class DuplicateActivityException(Exception):

    '''
    Raised when someone sticks a duplicate activity in the aggregated activity
    '''
    pass
