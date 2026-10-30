/* Read only KMS timing/capability evidence. No modeset or master ownership. */
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#define N 256
static void properties(int fd,uint32_t object,uint32_t type){
 uint32_t ids[N];uint64_t vals[N];
 struct drm_mode_obj_get_properties p={.props_ptr=(uintptr_t)ids,.prop_values_ptr=(uintptr_t)vals,.count_props=N,.obj_id=object,.obj_type=type};
 if(ioctl(fd,DRM_IOCTL_MODE_OBJ_GETPROPERTIES,&p)||p.count_props>N)return;
 for(unsigned i=0;i<p.count_props;i++){
  struct drm_mode_get_property prop={.prop_id=ids[i]};
  if(ioctl(fd,DRM_IOCTL_MODE_GETPROPERTY,&prop))continue;
  printf("PROP obj=%u id=%u name=%s value=%llu flags=0x%x\n",object,ids[i],prop.name,(unsigned long long)vals[i],prop.flags);
  if(!(prop.flags&DRM_MODE_PROP_BLOB)||!vals[i]||strcmp(prop.name,"mode_properties"))continue;
  struct drm_mode_get_blob b={.blob_id=(uint32_t)vals[i]};
  if(ioctl(fd,DRM_IOCTL_MODE_GETPROPBLOB,&b)||b.length>32768)continue;
  char *data=calloc(1,b.length+1);if(!data)continue;b.data=(uintptr_t)data;
  if(!ioctl(fd,DRM_IOCTL_MODE_GETPROPBLOB,&b))printf("MODE_PROPERTIES_BEGIN\n%.*s\nMODE_PROPERTIES_END\n",(int)b.length,data);
  free(data);
 }
}
int main(void){
 alarm(10);setbuf(stdout,NULL);
 int fd=open("/dev/dri/card0",O_RDWR|O_CLOEXEC);if(fd<0)return 2;
 if(ioctl(fd,DRM_IOCTL_DROP_MASTER,0)&&errno!=EACCES&&errno!=EINVAL)return 3;
 struct drm_set_client_cap cap={.capability=DRM_CLIENT_CAP_ATOMIC,.value=1};
 if(ioctl(fd,DRM_IOCTL_SET_CLIENT_CAP,&cap))return 4;
 uint32_t conns[N],crtcs[N];struct drm_mode_card_res r={.connector_id_ptr=(uintptr_t)conns,.crtc_id_ptr=(uintptr_t)crtcs,.count_connectors=N,.count_crtcs=N};
 if(ioctl(fd,DRM_IOCTL_MODE_GETRESOURCES,&r)||r.count_connectors>N||r.count_crtcs>N)return 5;
 for(unsigned i=0;i<r.count_connectors;i++){
  struct drm_mode_modeinfo modes[N];uint32_t props[N],encs[N];uint64_t vals[N];
  struct drm_mode_get_connector c={.connector_id=conns[i],.modes_ptr=(uintptr_t)modes,.count_modes=N,.props_ptr=(uintptr_t)props,.prop_values_ptr=(uintptr_t)vals,.count_props=N,.encoders_ptr=(uintptr_t)encs,.count_encoders=N};
  if(ioctl(fd,DRM_IOCTL_MODE_GETCONNECTOR,&c)||c.count_modes>N||c.connector_type!=DRM_MODE_CONNECTOR_DSI)continue;
  printf("CONNECTOR id=%u connected=%u\n",c.connector_id,c.connection);
  for(unsigned j=0;j<c.count_modes;j++){
   struct drm_mode_modeinfo *m=&modes[j];
   printf("MODE index=%u name=%s hz=%u clock=%u h=%u,%u,%u,%u skew=%u v=%u,%u,%u,%u flags=0x%x type=0x%x\n",j,m->name,m->vrefresh,m->clock,m->hdisplay,m->hsync_start,m->hsync_end,m->htotal,m->hskew,m->vdisplay,m->vsync_start,m->vsync_end,m->vtotal,m->flags,m->type);
  }
  properties(fd,c.connector_id,DRM_MODE_OBJECT_CONNECTOR);
 }
 for(unsigned i=0;i<r.count_crtcs;i++)properties(fd,crtcs[i],DRM_MODE_OBJECT_CRTC);
 close(fd);return 0;
}
