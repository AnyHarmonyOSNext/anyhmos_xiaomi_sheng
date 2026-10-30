/* Development fallback for absent WiFi SA. No connected/enabled state is fabricated.
 * SceneBoard calls these synchronously on its UI thread. Other processes retain
 * the donor implementation. Remove this fallback when the real service works.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
static int is_scene_board(void)
{
 char s[80]={0};int fd=open("/proc/self/cmdline",O_RDONLY|O_CLOEXEC);
 if(fd<0)return 0;
 ssize_t n=read(fd,s,sizeof(s)-1);close(fd);
 return n>0 && strcmp(s,"com.ohos.sceneboard")==0;
}
int wifi_load(void *self,int id) __asm__("_ZN4OHOS4Wifi17WifiSaLoadManager10LoadWifiSaEi");
int wifi_load(void *self,int id)
{
 if(id>=1120 && id<=1125 && is_scene_board())return 1;
 typedef int (*next_fn)(void *,int);
 next_fn next=(next_fn)dlsym(RTLD_NEXT,"_ZN4OHOS4Wifi17WifiSaLoadManager10LoadWifiSaEi");
 return next?next(self,id):1;
}
