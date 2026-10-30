set -e
B=/busybox
R=/hmos-root
source=$R/compat/lib64/librender_service_base.z.so
p=$R/data/local/tmp/librosen-renderable.so
echo "d423413ec1fc58f40c5b04846b00530a4d82d0929eee769ede3bf5c605e5a77d  $source" | $B sha256sum -c -
$B test ! -e "$p"
$B cp "$source" "$p"
echo 6QKAUg== | $B base64 -d | $B dd of="$p" bs=1 seek=9162080 conv=notrunc
echo "7f4fdf74cc0897ed322af94835a76fa3f5dd8fa82f44f75f5ab47cfa7a91f57b  $p" | $B sha256sum -c -
$B chmod 0644 "$p"
echo SURFACE_USAGE_CANDIDATE_CREATED
