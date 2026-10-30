#!/bin/sh
set -eu
B=/busybox
R=/hmos-root
h=$($B sha256sum "$R/system/lib64/libaccountmgr.z.so"); case "$h" in 5b2173e6f641a7608bc39c5a1b4755bc39b7755b806dc4c83439bfcdee912e44*) ;; *) echo ACCOUNT_HMAC_DONOR_MISMATCH_libaccountmgr.z.so; exit 51;; esac
h=$($B sha256sum "$R/system/lib64/chipset-sdk/libhukssdk.z.so"); case "$h" in 3541cfb288bd149d10f5a401703358c2f2c4c92a1802352903cd44a2e4f56b89*) ;; *) echo ACCOUNT_HMAC_DONOR_MISMATCH_libhukssdk.z.so; exit 51;; esac
h=$($B sha256sum "$R/system/lib64/chipset-sdk-sp/libcrypto_openssl.z.so"); case "$h" in 6a61befa16ace41b044af17472c42d45ce4f22c1c41a6fd9841e917e8fb6f8ac*) ;; *) echo ACCOUNT_HMAC_DONOR_MISMATCH_libcrypto_openssl.z.so; exit 51;; esac
$B cp /graphics/libsheng_account_hmac.so "$R/compat/lib64/libsheng_account_hmac.so"
$B chmod 0644 "$R/compat/lib64/libsheng_account_hmac.so"
$B cp /graphics/account_hmac_contract "$R/data/local/tmp/account_hmac_contract"
$B chmod 0755 "$R/data/local/tmp/account_hmac_contract"
h=$($B sha256sum "$R/compat/lib64/libsheng_account_hmac.so"); case "$h" in 5e66b2ba082bd1b81bff30b71c302368d505114dff59fe92adcd8dffc60fed19*) ;; *) echo ACCOUNT_HMAC_OUTPUT_MISMATCH; exit 52;; esac
echo SHENG_ACCOUNT_HMAC_STAGED_NO_TEE_OR_AUTH_CLAIM
