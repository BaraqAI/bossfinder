from .models.person import CompanySearchResult, PersonContact

__all__ = ["run_bossfinder", "CompanySearchResult", "PersonContact"]


def __getattr__(name: str):
    if name == "run_bossfinder":
        from .crew import run_bossfinder
        return run_bossfinder
    raise AttributeError(name)
