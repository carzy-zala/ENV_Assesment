class PipelineError(Exception):
    """Base exception for the pipeline."""


class ExtractionError(PipelineError):
    """Raised when data extraction fails."""


class TransformationError(PipelineError):
    """Raised when transformation fails."""


class LoadError(PipelineError):
    """Raised when database load fails."""


class ValidationError(PipelineError):
    """Raised when data validation fails."""