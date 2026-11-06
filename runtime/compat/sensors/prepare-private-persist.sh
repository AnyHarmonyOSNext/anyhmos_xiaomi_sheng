#!/busybox sh
# 按原init规则准备独立副本的现存元数据
set -eu
B=/busybox
R=${SENSOR_COLD_BASE:?}
P=$R/root/mnt/vendor/persist/sensors

# 仅处理已准备的私有副本，拒绝目录外的链接
[ -d "$P" ]
[ "$($B readlink -f "$P")" = "$P" ]
# 私有目录内不得存在指向真实持久区的挂载别名
$B awk -v stage="$R" '
    $5 == stage || index($5, stage "/") == 1 { bound = 1 }
    END { if (bound) exit 1 }
' /proc/self/mountinfo

existing_private()
{
    target=$P/$1
    [ -e "$target" ] || [ -L "$target" ] || return 1
    resolved=$($B readlink -f "$target")
    case "$resolved" in
        "$P"|"$P"/*) return 0 ;;
        *) echo PRIVATE_PERSIST_PATH_OUTSIDE >&2; exit 2 ;;
    esac
}

# 仅处理原 init 列出的现存项，不递归改写属主
for item in . sns.reg sensors_list.txt registry registry/registry \
    registry/registry/sensors_registry sensors_settings registry/sns_reg_config \
    registry/sns_reg_version registry/config; do
    if existing_private "$item"; then
        $B chown 1000:1000 "$target"
    fi
done
for pair in '.:0775' 'sensors_list.txt:0644' 'sensors_settings:0664'; do
    item=${pair%:*}
    mode=${pair#*:}
    if existing_private "$item"; then
        $B chmod "$mode" "$target"
    fi
done
echo PRIVATE_SENSOR_PERSIST_METADATA_ONLY
