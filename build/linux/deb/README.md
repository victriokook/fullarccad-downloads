# Linux native / deb build

Canonical application source: D:\FullArcCAD\source-runtime
prepare_linux_workspace.py prepares a snapshot without references to historical C-drive source copies. It uses project data, build/linux/platform-source, build/windows/QtBootstrap.txt and the assets in this folder.

Existing SDK image required: fullarccad-private-linux-native:20261031. It contains official FreeCAD 1.1.3 py311, CPython 3.11.14 headers and Cython 3.0.12/setuptools 75.8.2. This image is independent of the historical C-drive source folder.

1. Run prepare_linux_workspace.py (optional --baseline accepts a native-source/stage/audit.json cache; without it all modules are compiled).
2. Build LinuxDebBuilder.Dockerfile as fullarccad-linux-deb-builder:20261101.
3. Mount the prepared workspace at /work. Run build_linux_deb_native.py with /opt/freecad/squashfs-root/AppRun python and PYTHONPATH=/opt/fullarc-build-tools.
4. Run package_linux_deb.py with system python3 in the builder image. It removes compiler RUNPATHs and creates deb/tar, desktop integration, notices and checksums.
5. Build LinuxDebCleanTest.Dockerfile. In a fresh container, mount /work and run test_linux_deb.py as root; the suite installs the deb but runs the GUI/setup as the dedicated unprivileged fac-test account.
6. Run audit_linux_deb.py and retain RESULTS.json, lintian.txt, source/package audit and input hashes.

Final local release: D:\FullArcCAD\releases\linux-10languages-deb-20261101
Build workspace and complete private evidence: D:\FullArcCAD\work\linux-deb-20261101-092059

The top-level legacy Linux scripts outside this deb folder remain historical recipes. Do not use their hardcoded module counts for the new build.
No external publishing is part of these commands.
