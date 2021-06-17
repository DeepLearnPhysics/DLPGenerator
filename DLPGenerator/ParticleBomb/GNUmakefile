#
# This is an example GNUmakefile for my packages
#
NAME = ParticleBomb

# specific names for this package
SOURCES = $(wildcard *.cxx)
FMWK_HEADERS = LinkDef.h
HEADERS = $(filter-out $(FMWK_HEADERS), $(wildcard *.h))

# include options for this package
INCFLAGS  = -I.                       #Include itself

# platform-specific options
OSNAME          = $(shell uname -s)
HOST            = $(shell uname -n)
OSNAMEMODE      = $(OSNAME)

# call kernel specific compiler setup
include $(DLPGENERATOR_DIR)/Makefile/Makefile.${OSNAME}

LDFLAGS += -L$(shell root-config --libdir) -lEG


# call the common GNUmakefile
include $(DLPGENERATOR_DIR)/Makefile/GNUmakefile.CORE
