"""Backend-specific implementation of the pathman.Path interface"""
from .blackfynn import BlackfynnPath
from .s3 import S3Path
from .local import LocalPath
