// Exercise a real consumer window resized after EGL surface creation.
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <unistd.h>
#include "egl_real_window_fixture_v126.h"
#define CHECK(x) do { if (!(x)) { printf("RESIZE_FAIL line=%d %s\n", __LINE__, #x); return 1; } } while (0)
#define LOAD(h,n) auto n=(decltype(&::n))dlsym(h,#n); CHECK(n)
int main(int argc, char **argv)
{
    setbuf(stdout, nullptr); alarm(15);
    void *e=dlopen(argc>1?argv[1]:"/compat/lib64/libEGL_impl.so",RTLD_NOW|RTLD_GLOBAL);
    CHECK(e);
    void *g=dlopen("/compat/lib64/libGLESv2_impl.so",RTLD_NOW|RTLD_GLOBAL); CHECK(g);
    LOAD(e,eglGetDisplay); LOAD(e,eglInitialize); LOAD(e,eglChooseConfig);
    LOAD(e,eglCreateContext); LOAD(e,eglCreateWindowSurface); LOAD(e,eglMakeCurrent);
    LOAD(e,eglQuerySurface); LOAD(e,eglSwapBuffers); LOAD(e,eglDestroySurface);
    LOAD(e,eglDestroyContext); LOAD(e,eglTerminate);
    LOAD(g,glClearColor); LOAD(g,glClear); LOAD(g,glFinish); LOAD(g,glGetString);
    EGLDisplay d=eglGetDisplay(EGL_DEFAULT_DISPLAY); CHECK(d!=EGL_NO_DISPLAY);
    CHECK(eglInitialize(d,nullptr,nullptr));
    EGLint attrs[]={EGL_SURFACE_TYPE,EGL_WINDOW_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE};
    EGLConfig conf; EGLint count=0; CHECK(eglChooseConfig(d,attrs,&conf,1,&count)&&count);
    EGLint ca[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
    EGLContext ctx=eglCreateContext(d,conf,EGL_NO_CONTEXT,ca); CHECK(ctx!=EGL_NO_CONTEXT);
    WindowFixture fixture; CHECK(!fixture.Init());
    bool defaultMode=argc>2 && !strcmp(argv[2],"--default");
    bool lateMode=argc>2 && !strcmp(argv[2],"--late");
    bool noDrawMode=argc>2 && !strcmp(argv[2],"--nodraw");
    bool pendingMode=argc>2 && (!strcmp(argv[2],"--pending") || noDrawMode);
    LOAD(fixture.windowLib,OH_NativeWindow_NativeWindowHandleOpt);
    CHECK(!OH_NativeWindow_NativeWindowHandleOpt(fixture.window,SET_BUFFER_GEOMETRY,defaultMode?0:1,defaultMode?0:1));
    EGLSurface surf=eglCreateWindowSurface(d,conf,(EGLNativeWindowType)fixture.window,nullptr); CHECK(surf!=EGL_NO_SURFACE);
    EGLint w=0,h=0;
    CHECK(eglQuerySurface(d,surf,EGL_WIDTH,&w)&&eglQuerySurface(d,surf,EGL_HEIGHT,&h));
    printf("RESIZE_BEFORE egl=%dx%d\n",w,h);
    if (lateMode || pendingMode) {
        CHECK(eglMakeCurrent(d,surf,surf,ctx));
        if(!noDrawMode) { glClearColor(1,0,0,1); glClear(GL_COLOR_BUFFER_BIT); glFinish(); }
        if(pendingMode) {
            CHECK(!OH_NativeWindow_NativeWindowHandleOpt(fixture.window,SET_BUFFER_GEOMETRY,32,32));
            CHECK(eglQuerySurface(d,surf,EGL_WIDTH,&w)&&eglQuerySurface(d,surf,EGL_HEIGHT,&h));
            printf("RESIZE_PENDING_REQUEST=%dx%d\n",w,h);
        }
        CHECK(eglSwapBuffers(d,surf));
        LOAD(fixture.imageLib,OH_NativeImage_AcquireNativeWindowBuffer);
        LOAD(fixture.imageLib,OH_NativeImage_ReleaseNativeWindowBuffer);
        OHNativeWindowBuffer *first=nullptr; int fence=-1, result=-1;
        for (int i=0;i<200 && result;i++) {
            result=OH_NativeImage_AcquireNativeWindowBuffer(fixture.image,&first,&fence);
            if(result) usleep(10000);
        }
        CHECK(!result && first);
        if(fence>=0) { pollfd p{fence,POLLIN,0}; CHECK(poll(&p,1,3000)>0); close(fence); }
        CHECK(!OH_NativeImage_ReleaseNativeWindowBuffer(fixture.image,first,-1));
        puts("RESIZE_FIRST_1X1_FRAME_DONE");
        if(pendingMode) {
            int pw=0,ph=0;
            CHECK(!OH_NativeWindow_NativeWindowHandleOpt(fixture.window,GET_BUFFER_GEOMETRY,&ph,&pw));
            printf("RESIZE_PENDING_NATIVE_AFTER_SWAP=%dx%d\n",pw,ph);
            CHECK(pw==32 && ph==32);
        }
    }
    if (!defaultMode) CHECK(!OH_NativeWindow_NativeWindowHandleOpt(fixture.window,SET_BUFFER_GEOMETRY,32,32));
    int nw=0,nh=0;
    CHECK(!OH_NativeWindow_NativeWindowHandleOpt(fixture.window,GET_BUFFER_GEOMETRY,&nh,&nw));
    CHECK(eglQuerySurface(d,surf,EGL_WIDTH,&w)&&eglQuerySurface(d,surf,EGL_HEIGHT,&h));
    printf("RESIZE_AFTER native=%dx%d egl=%dx%d\n",nw,nh,w,h);
    CHECK(eglMakeCurrent(d,surf,surf,ctx));
    printf("RESIZE_RENDERER=%s\n",glGetString(GL_RENDERER));
    glClearColor(0,1,0,1); glClear(GL_COLOR_BUFFER_BIT); glFinish();
    CHECK(eglSwapBuffers(d,surf));
    int pixels=fixture.CheckGreen();
    CHECK(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT));
    eglDestroySurface(d,surf); eglDestroyContext(d,ctx); eglTerminate(d);
    printf("EGL_RESIZE_RESULT=%d\n",pixels);
    return pixels;
}
