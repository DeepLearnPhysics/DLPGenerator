
ifndef DLPGENERATOR_DIR
ERROR_MESSAGE := $(error DLPGENERATOR_DIR is not set... run configure.sh!)
endif

OSNAME          = $(shell uname -s)
HOST            = $(shell uname -n)
OSNAMEMODE      = $(OSNAME)

include $(DLPGENERATOR_DIR)/Makefile/Makefile.${OSNAME}

SUBDIRS := ParticleBomb

.phony: all clean

all:
	@echo "Start building..."
	@for i in $(SUBDIRS); do ( echo "" && echo "Compiling $$i..." && $(MAKE) --directory=DLPGenerator/$$i) || exit $$?; done
	@echo "Done!"
clean:
	@echo "Cleaning..."
	@for i in $(SUBDIRS); do ( echo "" && echo "Cleaning $$i..." && $(MAKE) clean --directory=DLPGenerator/$$i) || exit $$?; done
	@echo "Done!"

