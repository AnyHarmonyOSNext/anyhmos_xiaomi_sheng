/* Control the existing composer service; no callbacks or DRM ownership. */
#include "display/composer/v1_3/idisplay_composer.h"
#include <cstdio>
#include <unistd.h>
namespace C=OHOS::HDI::Display::Composer;
int main(){
 setbuf(stdout,nullptr);alarm(20);
 auto service=C::V1_3::IDisplayComposer::Get("display_composer_service",false);
 if(!service){printf("POWER_SERVICE_MISSING\n");return 2;}
 C::V1_0::DispPowerStatus status=C::V1_0::POWER_STATUS_ON;
 int ret=service->GetDisplayPowerStatus(0,status);
 printf("POWER_BEFORE result=%d status=%d\n",ret,(int)status);
 int off=service->SetDisplayPowerStatus(0,C::V1_0::POWER_STATUS_OFF);
 printf("POWER_OFF result=%d\n",off);
 usleep(800000);
 int on=service->SetDisplayPowerStatus(0,C::V1_0::POWER_STATUS_ON);
 printf("POWER_ON result=%d\n",on);
 ret=service->GetDisplayPowerStatus(0,status);
 printf("POWER_AFTER result=%d status=%d\n",ret,(int)status);
 return off||on||ret||status!=C::V1_0::POWER_STATUS_ON?3:0;
}
