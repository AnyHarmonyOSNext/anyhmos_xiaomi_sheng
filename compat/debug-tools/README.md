# Local diagnostic utility

BusyBox 1.36.1, GPL-2.0, built statically for AArch64 with the installed
aarch64-linux-gnu-gcc. Official source:
https://busybox.net/downloads/busybox-1.36.1.tar.bz2

SHA256 b8cc24c9574d809e7279c3be349795c5d5ceb6fdf19ca709f80cde50e47de314
was checked against the official .sha256 file before building.

Source, full GPL license and configuration are retained in
/root/hmos-work/busybox-tools/busybox-1.36.1. Start with defconfig, set
CONFIG_STATIC=y and CONFIG_FEATURE_SH_STANDALONE=y, then build with
ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j8. No services are started by
including this executable. It is invoked only by explicit local USB commands.

The command worker accepts base64 UTF-8 scripts with request IDs, captures
stdout/stderr through a pipe, and limits each process group to 60 seconds.
It is a temporary root diagnostic facility for this already-unlocked test
device, not a production ROM interface. No files are uploaded or committed.
