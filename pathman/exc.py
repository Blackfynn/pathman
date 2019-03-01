""" Custom exceptions for Pathman library """


class PathmanException(Exception):
    """ Base exception """


class UnsupportedPathTypeException(PathmanException):
    """ Raised when a path type is not supported """


class UnsupportedCopyOperation(PathmanException):
    """ Raised for an unsupported copy operation """
