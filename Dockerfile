FROM deeplearnphysics/dune-nd-sim:ub20.04-generator

# ROOT
ENV ROOTSYS=/app/root
ENV PATH="${ROOTSYS}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${ROOTSYS}/lib:${LD_LIBRARY_PATH}"
ENV PYTHONPATH="${ROOTSYS}/lib:${PYTHONPATH}"

# DLPGenerator
ENV DLPGENERATOR_ROOT6=1
ENV DLPGENERATOR_CXX=g++
ENV DLPGENERATOR_DIR=/app/DLPGenerator
ENV DLPGENERATOR_INCDIR="${DLPGENERATOR_DIR}/build/include"
ENV DLPGENERATOR_BUILDDIR="${DLPGENERATOR_DIR}/build"
ENV DLPGENERATOR_LIBDIR="${DLPGENERATOR_DIR}/build/lib"
ENV LD_LIBRARY_PATH="${DLPGENERATOR_DIR}/build/lib:${LD_LIBRARY_PATH}"
ENV PYTHONPATH="${DLPGENERATOR_DIR}/python:${PYTHONPATH}"
RUN git clone https://github.com/DeepLearnPhysics/DLPGenerator.git /app/DLPGenerator && \
    cd /app/DLPGenerator && \
    make 

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}
    
# Make sure the contents of our repo are in ${HOME}
WORKDIR /app
COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}

#ENV PYTHONPATH ${PYTHONPATH}:${HOME}/lartpc_mlreco3d
