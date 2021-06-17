import ROOT,os
if not 'DLPGENERATOR_DIR' in os.environ:
    print('$DLPGENERATOR_DIR shell env. var. not found (run configure.sh)')
    raise ImportError
from ROOT import DLPGenerator
from .config_parser import create_generator, EXAMPLE_CONFIG
