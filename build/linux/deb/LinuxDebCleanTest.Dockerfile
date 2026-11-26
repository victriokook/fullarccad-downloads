FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates python3 python3-pil xdotool xvfb xauth libgl1-mesa-dri libglx-mesa0 mesa-utils dbus-x11 fonts-noto-cjk fonts-dejavu-core && useradd -m -u 1001 -s /bin/bash fac-test
ENTRYPOINT ["/bin/bash"]
