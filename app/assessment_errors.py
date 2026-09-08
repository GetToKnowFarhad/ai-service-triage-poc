"""Errors that the assessment service can safely show on the ticket page."""


class AssessmentError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code
