FROM fullarccad-private-linux-native:20261031
USER root
RUN apt-get update && apt-get install -y --no-install-recommends desktop-file-utils shared-mime-info zenity lintian patchelf && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/bin/bash"]
