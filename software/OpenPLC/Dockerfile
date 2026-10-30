FROM debian:12-slim

COPY ./OpenPLC_v3/ /CybICS/OpenPLC_v3/
WORKDIR /CybICS/OpenPLC_v3/
RUN export GNUMAKEFLAGS=-j$(nproc --all) \
    && alias make='make -j$(nproc --all)' \
    && ./install.sh docker \
    && apt-get update && apt-get install -y --no-install-recommends iptables \
    && rm -rf /var/lib/apt/lists/*

# Fixes to the runtime core that are not in the OpenPLC_v3 submodule yet.
# compile_program.sh below builds core/*.cpp, so applying them here keeps the
# install layer above cached. git apply fails the build if a patch no longer
# applies, e.g. after a submodule bump that already contains the fix.
COPY patches/ /CybICS/patches/
# Applied from /CybICS: the submodule's .git file was copied along and points
# at a repository that is not in the image.
RUN cd /CybICS && for p in /CybICS/patches/*.patch; do \
        git apply --verbose --directory=OpenPLC_v3 "$p" || exit 1; done

# copy files after compile the main part to reduce re-compile time on changes on cybICS.st
WORKDIR /CybICS/OpenPLC_v3/webserver
COPY cybICS.st st_files/424345.st
COPY openplc.db openplc.db
RUN ./scripts/compile_program.sh 424345.st

EXPOSE 8080
EXPOSE 502
EXPOSE 44818
EXPOSE 20000
EXPOSE 102
CMD ["/CybICS/OpenPLC_v3/start_openplc.sh"]
