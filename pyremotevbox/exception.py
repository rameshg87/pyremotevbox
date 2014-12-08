

class PyRemoteVBoxException(Exception):

    message = "An exception occured in PyRemoteVBox Module."

    def __init__(self, message=None):
        super(PyRemoteVBoxException, self).__init__(message)


