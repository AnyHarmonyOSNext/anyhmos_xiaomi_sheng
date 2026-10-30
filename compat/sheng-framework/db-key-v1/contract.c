/* SPDX-License-Identifier: MIT */
#define CONTRACT_MAIN
#include "db_key.c"
#include "hks_param.h"
static void check(int good,const char *label)
{ if(!good) { fprintf(stderr,"DBKEY_CONTRACT_FAILED %s\n",label); exit(1); } }
static struct HksParamSet *make(int gen, int decrypt, unsigned char *tag)
{
    static unsigned char nonce[12]={1,2,3,4,5,6,7,8,9,10,11,12};
    static unsigned char aad[]="RdbClientAAD";
    struct HksParam a[]={
        {.tag=HKS_TAG_ALGORITHM,.uint32Param=HKS_ALG_AES},
        {.tag=HKS_TAG_PURPOSE,.uint32Param=gen?HKS_KEY_PURPOSE_ENCRYPT|HKS_KEY_PURPOSE_DECRYPT:decrypt?HKS_KEY_PURPOSE_DECRYPT:HKS_KEY_PURPOSE_ENCRYPT},
        {.tag=HKS_TAG_DIGEST,.uint32Param=0},
        {.tag=HKS_TAG_BLOCK_MODE,.uint32Param=HKS_MODE_GCM},
        {.tag=HKS_TAG_PADDING,.uint32Param=HKS_PADDING_NONE},
        {.tag=HKS_TAG_AUTH_STORAGE_LEVEL,.uint32Param=HKS_AUTH_STORAGE_LEVEL_DE},
        {.tag=HKS_TAG_KEY_SIZE,.uint32Param=256},
        {.tag=HKS_TAG_NONCE,.blob={12,nonce}},
        {.tag=HKS_TAG_ASSOCIATED_DATA,.blob={sizeof(aad)-1,aad}},
        {.tag=HKS_TAG_AE_TAG,.blob={16,tag}}
    };
    struct HksParamSet *p=NULL;
    check(HksInitParamSet(&p)==0,"param init");
    check(HksAddParams(p,a,gen?7:tag?10:9)==0&&HksBuildParamSet(&p)==0,"original param ABI");
    return p;
}
int main(void)
{
    alarm(15); setbuf(stdout,NULL);
    /* AES-256-GCM known-answer, zero key/IV and 16 zero bytes; no AAD. */
    struct Session known={.purpose=HKS_KEY_PURPOSE_ENCRYPT,.used=16};
    unsigned char zero_result[32]; struct HksBlob z={32,zero_result};
    const unsigned char expected[]={0xce,0xa7,0x40,0x3d,0x4d,0x60,0x6b,0x6e,0x07,0x4e,0xc5,0xd3,0xba,0xf3,0x9d,0x18,
        0xd0,0xd1,0xc8,0xa7,0x99,0x99,0x6b,0xf0,0x26,0x5b,0x98,0xb5,0xd4,0x8a,0xb9,0x19};
    check(aes_gcm(&known,&z)==0&&z.size==32&&!memcmp(z.data,expected,32),"AES256 GCM known answer");
    const char *name="DistributedDataRdb";
    struct HksBlob alias={(uint32_t)strlen(name),(unsigned char *)name};
    struct HksParamSet *gen=make(1,0,NULL),*enc=make(0,0,NULL),*dec=make(0,1,NULL);
    check(SksGenerateKey(&alias,gen,NULL)==0&&SksKeyExist(&alias,gen)==0,"persistent key creation");
    unsigned char first[32],second[32]; check(key(&alias,first,0)==0,"read test key");
    check(SksGenerateKey(&alias,gen,NULL)==0&&key(&alias,second,0)==0&&!memcmp(first,second,32),"key not replaced");
    wipe(first,32); wipe(second,32);
    unsigned char plain[128],cipher[256],decoded[256]; for(unsigned i=0;i<128;i++) plain[i]=(unsigned char)(i*13);
    uint64_t id; struct HksBlob h={8,(unsigned char *)&id},in={64,plain},out={256,cipher};
    check(SksInit(&alias,enc,&h,NULL)==0&&SksUpdate(&h,enc,&in,&out)==0&&out.size==0,"stream buffers input");
    in.data=plain+64; out.size=256;
    check(SksFinish(&h,enc,&in,&out)==0&&out.size==144&&memcmp(plain,cipher,128),"stream encrypt");
    check(SksFinish(&h,enc,&in,&out)!=0,"consumed handle rejected");
    struct HksParamSet *detached=make(0,1,cipher+128);
    check(SksInit(&alias,detached,&h,NULL)==0,"detached tag begin");
    in.data=cipher; out.data=decoded; out.size=256;
    check(SksUpdate(&h,detached,&in,&out)==0&&out.size==0,"no unauthenticated plaintext");
    in.data=cipher+64; out.size=256;
    check(SksFinish(&h,detached,&in,&out)==0&&out.size==128&&!memcmp(plain,decoded,128),"original RDB stream shape");
    in.data=cipher; in.size=144; out.size=256;
    check(SksDecrypt(&alias,dec,&in,&out)==0&&out.size==128&&!memcmp(plain,decoded,128),"single-shot KV shape");
    cipher[143]^=1; out.size=256; memset(decoded,0xa5,256);
    check(SksDecrypt(&alias,dec,&in,&out)!=0&&out.size==0&&decoded[0]==0xa5,"bad tag returns failure without plaintext");
    cipher[143]^=1; out.size=1;
    check(SksDecrypt(&alias,dec,&in,&out)==HKS_ERROR_BUFFER_TOO_SMALL,"short output rejected");
    struct HksBlob bad={7,(unsigned char *)"unknown"};
    check(SksGenerateKey(&bad,gen,NULL)==HKS_ERROR_NOT_SUPPORTED,"other aliases rejected");
    ((struct HksParam *)param(gen,HKS_TAG_KEY_SIZE))->uint32Param=128;
    check(SksGenerateKey(&alias,gen,NULL)==INVALID,"wrong key strength rejected");
    HksFreeParamSet(&gen); HksFreeParamSet(&enc); HksFreeParamSet(&dec); HksFreeParamSet(&detached);
    puts("DBKEY_KNOWN_ANSWER_PERSISTENCE_RDB_STREAM_KV_ROUNDTRIP_CORRUPTION_AND_BOUNDARY_OK");
    return 0;
}
