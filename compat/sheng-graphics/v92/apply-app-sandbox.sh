set -e
B=/busybox
R=/hmos-root
$B mkdir -p $R/compat/etc/sandbox
echo "4076b9b25f4d132ff26457170e763c6215901b00a882924bbd3ffa1c16c62ead  $R/system/etc/sandbox/appdata-sandbox.json" | $B sha256sum -c -
$B gzip -dc /graphics/appdata-sandbox.json.gz > $R/compat/etc/sandbox/appdata-sandbox.json
echo "e51c63b4e099a2f927d17f70d037e2687aeff63f84aad2af74a63c4c923329b0  $R/compat/etc/sandbox/appdata-sandbox.json" | $B sha256sum -c -
$B chmod 0644 $R/compat/etc/sandbox/appdata-sandbox.json
$B mount --bind $R/compat/etc/sandbox/appdata-sandbox.json $R/system/etc/sandbox/appdata-sandbox.json
echo "d71faa9318f2b8829fdbf67d09153d92573aa4d2275043569bd6e62f9b4370fa  $R/system/etc/sandbox/appdata-sandbox-isolated.json" | $B sha256sum -c -
$B gzip -dc /graphics/appdata-sandbox-isolated.json.gz > $R/compat/etc/sandbox/appdata-sandbox-isolated.json
echo "0199560a89c4f6a8ea3606fc990627ae84daef6760462d5cb0c8862371563505  $R/compat/etc/sandbox/appdata-sandbox-isolated.json" | $B sha256sum -c -
$B chmod 0644 $R/compat/etc/sandbox/appdata-sandbox-isolated.json
$B mount --bind $R/compat/etc/sandbox/appdata-sandbox-isolated.json $R/system/etc/sandbox/appdata-sandbox-isolated.json
echo APP_SANDBOX_COMPAT_MOUNT_CONFIGURED
