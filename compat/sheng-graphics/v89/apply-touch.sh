set -e
B=/busybox
R=/hmos-root
$B tar -xzf /graphics/touch-bundle.tar.gz -C $R/compat
echo "da9accaffbd76a339c12e998757ccc3406973b6bf41f72bca615a81752e5c791  $R/compat/modules/xiaomi_touch.ko" | $B sha256sum -c -
echo "a1f3f907f4519eaf3d63243561fc32c7f75337188a3953b3857bcad60135233f  $R/compat/modules/nt36532_touch.ko" | $B sha256sum -c -
echo "750508bb4d75472d35ce5852ec8470d66afa6bf4a4274c136b3759034260ef59  $R/compat/firmware/novatek_nt36532_n81a_fw_csot.bin" | $B sha256sum -c -
echo "443bbd89dcfcc0359b7dd0d84b70bb18345c5c42877e4efd484dcf2db4796f27  $R/compat/firmware/novatek_nt36532_n81a_mp_csot.bin" | $B sha256sum -c -
$B mkdir -p /compat
$B mount --bind $R/compat /compat
$B insmod /lib/modules/reboot-mode.ko
$B insmod /lib/modules/qcom-pon.ko
$B insmod /lib/modules/spi-msm-geni.ko
$B insmod $R/compat/modules/xiaomi_touch.ko
$B insmod $R/compat/modules/nt36532_touch.ko
echo SHENG_STOCK_TOUCH_STAGED_AND_LOADED_VENDOR_UNTOUCHED
