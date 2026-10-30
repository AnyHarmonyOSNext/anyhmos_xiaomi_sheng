// The public SDK uses __n1. Platform HDI objects in this ROM use __h.
// Use a separate configuration rather than modifying the installed SDK.
// Runtime compatibility must be tested against the original platform libc++.
#ifndef _LIBCPP___CONFIG_SITE
#define _LIBCPP___CONFIG_SITE
#define _LIBCPP_ABI_VERSION 1
#define _LIBCPP_ABI_NAMESPACE __h
#define _LIBCPP_HAS_NO_VENDOR_AVAILABILITY_ANNOTATIONS
#define _LIBCPP_ENABLE_ASSERTIONS_DEFAULT 0
#endif
