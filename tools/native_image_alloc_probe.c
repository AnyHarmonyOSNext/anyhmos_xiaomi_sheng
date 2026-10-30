/* Exercise the original public native-buffer allocation and mapper path. */
#include <native_buffer/native_buffer.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
int main(void){
 setbuf(stdout,NULL);alarm(12);
 void *lib=dlopen("libnative_buffer.so",RTLD_NOW|RTLD_LOCAL);
 if(!lib){puts(dlerror());return 2;}
 OH_NativeBuffer*(*alloc)(const OH_NativeBuffer_Config*)=dlsym(lib,"OH_NativeBuffer_Alloc");
 int(*map)(OH_NativeBuffer*,void**)=dlsym(lib,"OH_NativeBuffer_Map");
 int(*unmap)(OH_NativeBuffer*)=dlsym(lib,"OH_NativeBuffer_Unmap");
 int(*unref)(OH_NativeBuffer*)=dlsym(lib,"OH_NativeBuffer_Unreference");
 if(!alloc||!map||!unmap||!unref)return 3;
 OH_NativeBuffer_Config c={.width=192,.height=192,.format=20,.usage=0xc00002b,.stride=0};
 OH_NativeBuffer *b=alloc(&c);printf("NATIVE_IMAGE_ALLOC buffer=%p\n",(void*)b);
 FILE *f=fopen("/proc/self/maps","r");char line[1024];
 if(f){while(fgets(line,sizeof(line),f))if(strstr(line,"mapper_service")||strstr(line,"buffer_vdi")||strstr(line,"libhdi_base"))fputs(line,stdout);fclose(f);}
 if(!b)return 4;
 void *p=NULL;int result=map(b,&p);printf("NATIVE_IMAGE_MAP result=%d address=%p\n",result,p);
 if(result||!p)return 5;
 memset(p,0x57,192*192*4);if(((unsigned char*)p)[192*192*4-1]!=0x57)return 6;
 int u=unmap(b),v=unref(b);printf("NATIVE_IMAGE_RELEASE unmap=%d unref=%d\n",u,v);
 return u||v?7:0;
}
