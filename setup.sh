#!/bin/bash

# clean up previously set env
if [[ -z $FORCE_DLPGENERATOR_DIR ]]; then
    where="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    export DLPGENERATOR_DIR=${where}
else
    export DLPGENERATOR_DIR=$FORCE_DLPGENERATOR_DIR
fi
export DLPGENERATOR_BINDIR=$DLPGENERATOR_DIR/bin

# set the build dir
unset DLPGENERATOR_BUILDDIR
if [[ -z $DLPGENERATOR_BUILDDIR ]]; then
    export DLPGENERATOR_BUILDDIR=$DLPGENERATOR_DIR/build
fi
export DLPGENERATOR_LIBDIR=$DLPGENERATOR_BUILDDIR/lib
export DLPGENERATOR_INCDIR=$DLPGENERATOR_BUILDDIR/include
mkdir -p $DLPGENERATOR_BUILDDIR;
mkdir -p $DLPGENERATOR_LIBDIR;
mkdir -p $DLPGENERATOR_BINDIR;

# Abort if ROOT not installed. Let's check rootcint for this.
if [ `command -v rootcling` ]; then
    export DLPGENERATOR_ROOT6=1
else
    echo
    echo Looks like you do not have ROOT6 installed.
    echo Aborting.
    echo
    return 1;
fi

# Check Numpy
export DLPGENERATOR_NUMPY=`$DLPGENERATOR_DIR/bin/check_numpy`

# warning for missing support
missing=""
if [ $DLPGENERATOR_NUMPY -eq 0 ]; then
    missing+=" Numpy"
else
    DLPGENERATOR_INCLUDES="${DLPGENERATOR_INCLUDES} -I`python3 -c\"import numpy; print(numpy.get_include())\"`"
fi
if [[ $missing ]]; then
    printf "\033[93mWarning\033[00m ... missing$missing support. Build without them.\n";
fi

echo
printf "\033[93mLArCV\033[00m FYI shell env. may useful for external packages:\n"
printf "    \033[95mDLPGENERATOR_INCDIR\033[00m   = $DLPGENERATOR_INCDIR\n"
printf "    \033[95mDLPGENERATOR_LIBDIR\033[00m   = $DLPGENERATOR_LIBDIR\n"
printf "    \033[95mDLPGENERATOR_BUILDDIR\033[00m = $DLPGENERATOR_BUILDDIR\n"

export PATH=$DLPGENERATOR_BINDIR:$PATH
export LD_LIBRARY_PATH=$DLPGENERATOR_LIBDIR:$LD_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$DLPGENERATOR_LIBDIR:$DYLD_LIBRARY_PATH
export PYTHONPATH=$DLPGENERATOR_DIR/python:$PYTHONPATH

export DLPGENERATOR_CXX=clang++
if [ -z `command -v $DLPGENERATOR_CXX` ]; then
    export DLPGENERATOR_CXX=g++
    if [ -z `command -v $DLPGENERATOR_CXX` ]; then
        echo
        echo Looks like you do not have neither clang or g++!
        echo You need one of those to compile LArCaffe... Abort config...
        echo
        return 1;
    fi
fi

echo
echo "Finish configuration. To build, type:"
echo "> make "
echo
