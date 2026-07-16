FROM rootproject/root:6.32.02-ubuntu22.04

SHELL ["/bin/bash", "-lc"]

ARG DEBIAN_FRONTEND=noninteractive
ARG NB_USER=dlp
ARG NB_UID=1000
ARG NB_GID=1000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3 \
        python3-numpy \
        python3-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid ${NB_GID} ${NB_USER} \
    && useradd --uid ${NB_UID} --gid ${NB_GID} --create-home --shell /bin/bash ${NB_USER}

ENV DLPGENERATOR_DIR=/opt/DLPGenerator
ENV DLPGENERATOR_BINDIR=${DLPGENERATOR_DIR}/bin
ENV DLPGENERATOR_BUILDDIR=${DLPGENERATOR_DIR}/build
ENV DLPGENERATOR_LIBDIR=${DLPGENERATOR_BUILDDIR}/lib
ENV DLPGENERATOR_INCDIR=${DLPGENERATOR_BUILDDIR}/include
ENV DLPGENERATOR_CXX=g++
ENV DLPGENERATOR_CXXSTDFLAG=-std=c++17
ENV LD_LIBRARY_PATH=
ENV PATH=${DLPGENERATOR_BINDIR}:${PATH}
ENV PYTHONPATH=${DLPGENERATOR_DIR}/python:${PYTHONPATH}
ENV LD_LIBRARY_PATH=${DLPGENERATOR_LIBDIR}:${LD_LIBRARY_PATH}
ENV ROOT_INCLUDE_PATH=${DLPGENERATOR_INCDIR}/DLPGenerator/ParticleBomb

WORKDIR ${DLPGENERATOR_DIR}
COPY . ${DLPGENERATOR_DIR}

RUN source setup.sh \
    && make test \
    && chmod +x ${DLPGENERATOR_BINDIR}/dlpgen \
    && chown -R ${NB_UID}:${NB_GID} ${DLPGENERATOR_DIR}

USER ${NB_USER}
WORKDIR /home/${NB_USER}

CMD ["/bin/bash"]
