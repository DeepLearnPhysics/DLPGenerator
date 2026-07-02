import os


def __getattr__(name):
    if name == "DLPGenerator":
        if "DLPGENERATOR_DIR" not in os.environ:
            print('$DLPGENERATOR_DIR shell env. var. not found (run configure.sh)')
            raise ImportError
        import ROOT

        return ROOT.DLPGenerator

    if name in {"create_generator", "EXAMPLE_CONFIG"}:
        from .config_parser import EXAMPLE_CONFIG, create_generator

        exports = {
            "create_generator": create_generator,
            "EXAMPLE_CONFIG": EXAMPLE_CONFIG,
        }
        return exports[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["DLPGenerator", "create_generator", "EXAMPLE_CONFIG"]
