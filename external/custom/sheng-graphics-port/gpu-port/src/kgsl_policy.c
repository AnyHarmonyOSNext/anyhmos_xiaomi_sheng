/* Extend existing GPU clients with the KGSL requests used by Turnip.
 * No new domains, ordinary permissions, permissive flags or token changes. */
#include <stdio.h>
#include <stdlib.h>
#include <sepol/policydb/policydb.h>
#include <sepol/policydb/hashtab.h>
int main(int argc,char**argv){if(argc!=3)return 2;policydb_t p;policy_file_t pf;policydb_init(&p);policy_file_init(&pf);pf.type=PF_USE_STDIO;pf.fp=fopen(argv[1],"rb");if(!pf.fp||policydb_read(&p,&pf,0))return 3;fclose(pf.fp);
 type_datum_t*t=hashtab_search(p.p_types.table,"gpu_device");class_datum_t*c=hashtab_search(p.p_classes.table,"chr_file");if(!t||!c)return 4;
 avtab_key_t keys[2048];unsigned count=0;for(unsigned i=0;i<p.te_avtab.nslot;i++)for(avtab_ptr_t n=p.te_avtab.htable[i];n;n=n->next){avtab_key_t*k=&n->key;avtab_extended_perms_t*x=n->datum.xperms;if(k->target_type==t->s.value&&k->target_class==c->s.value&&k->specified==AVTAB_XPERMS_ALLOWED&&x&&x->specified==AVTAB_XPERMS_IOCTLFUNCTION&&x->driver==0x50){if(count>=2048)return 5;keys[count++]=*k;}}
 const unsigned requests[]={0x02,0x07,0x13,0x14,0x33,0x34,0x35,0x3b,0x47,0x48,0x4a};
 for(unsigned i=0;i<count;i++){avtab_extended_perms_t x={0};x.specified=AVTAB_XPERMS_IOCTLFUNCTION;x.driver=0x09;for(unsigned j=0;j<sizeof(requests)/sizeof(requests[0]);j++)x.perms[requests[j]/32]|=1u<<(requests[j]%32);avtab_datum_t d={0};d.xperms=&x;if(!avtab_insert_nonunique(&p.te_avtab,&keys[i],&d))return 6;printf("GPU_CLIENT %s KGSL=0902,0907,0913,0914,0933,0934,0935,093b,0947,0948,094a\n",p.p_type_val_to_name[keys[i].source_type-1]);}
 pf.fp=fopen(argv[2],"wb");if(!pf.fp||policydb_write(&p,&pf))return 7;fclose(pf.fp);printf("ADDED_XPERMS_RULES=%u\n",count);policydb_destroy(&p);return count?0:8;}
