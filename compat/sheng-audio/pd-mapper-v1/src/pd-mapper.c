/*
 * Copyright (c) 2018, Linaro Ltd.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its contributors
 * may be used to endorse or promote products derived from this software without
 * specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */
#include <sys/stat.h>
#include <sys/types.h>
#include <err.h>
#include <errno.h>
#include <dirent.h>
#include <fcntl.h>
#include <libgen.h>
#include <libqrtr.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "assoc.h"
#include "json.h"
#include "servreg_loc.h"

struct pd_map {
	const char *service;
	const char *domain;
	int instance;
};

static struct pd_map *pd_maps;
static const char *map_directory;

static void handle_get_domain_list(int sock, const struct qrtr_packet *pkt)
{
	struct servreg_loc_get_domain_list_resp resp = {};
	struct servreg_loc_get_domain_list_req req = {};
	struct servreg_loc_domain_list_entry *entry;
	DEFINE_QRTR_PACKET(resp_buf, 4096);
	const struct pd_map *pd_map = pd_maps;
	unsigned int txn = 0;
	ssize_t len;
	int ret;

	ret = qmi_decode_message(&req, &txn, pkt, QMI_REQUEST,
				 SERVREG_LOC_GET_DOMAIN_LIST,
				 servreg_loc_get_domain_list_req_ei);
	if (ret < 0) {
		resp.result.result = QMI_RESULT_FAILURE;
		resp.result.error = QMI_ERR_MALFORMED_MSG;
		goto respond;
	}

	req.name[sizeof(req.name)-1] = '\0';
	printf("PD_LOOKUP_REQUEST=%s\n", req.name);

	resp.result.result = QMI_RESULT_SUCCESS;
	resp.db_revision_valid = 1;
	resp.db_revision = 1;

	while (pd_map->service) {
		if (!strcmp(pd_map->service, req.name)) {
			if (resp.domain_list_len >= 255 || strlen(pd_map->domain) >= sizeof(resp.domain_list[0].name)) {
				resp.result.result = QMI_RESULT_FAILURE; resp.result.error = QMI_ERR_INTERNAL;
				resp.domain_list_len = 0; goto respond;
			}
			entry = &resp.domain_list[resp.domain_list_len++];

			strcpy(entry->name, pd_map->domain);
			entry->name_len = strlen(pd_map->domain);
			entry->instance_id = pd_map->instance;
		}

		pd_map++;
	}

	if (resp.domain_list_len)
		resp.domain_list_valid = 1;

	resp.total_domains_valid = 1;
	resp.total_domains = resp.domain_list_len;

respond:
	len = qmi_encode_message(&resp_buf,
				 QMI_RESPONSE, SERVREG_LOC_GET_DOMAIN_LIST,
				 txn, &resp,
				 servreg_loc_get_domain_list_resp_ei);
	if (len < 0) {
		fprintf(stderr,
			"[PD-MAPPER] failed to encode get_domain_list response: %s\n",
			strerror(-len));
		return;
	}

	ret = qrtr_sendto(sock, pkt->node, pkt->port,
			  resp_buf.data, resp_buf.data_len);
	if (ret < 0) {
		fprintf(stderr,
			"[PD-MAPPER] failed to send get_domain_list response: %s\n",
			strerror(-ret));
	}
}

static int pd_load_map(const char *file)
{
	static int num_pd_maps;
	struct json_value *sr_service;
	struct json_value *sr_domain;
	struct json_value *root;
	struct json_value *it;
	const char *subdomain;
	const char *provider;
	const char *service;
	const char *domain;
	const char *soc;
	struct pd_map *newp;
	struct pd_map *map;
	double number;
	int count;
	int ret;

	root = json_parse_file(file);
	if (!root)
		return -1;

	sr_domain = json_get_child(root, "sr_domain");
	if (!sr_domain) { json_free(root); return -1; }
	soc = json_get_string(sr_domain, "soc");
	domain = json_get_string(sr_domain, "domain");
	subdomain = json_get_string(sr_domain, "subdomain");
	ret = json_get_number(sr_domain, "qmi_instance_id", &number);
	if (ret)
		return ret;

	if (!soc || !domain || !subdomain) {
		fprintf(stderr, "failed to parse sr_domain\n");
		return -1;
	}

	sr_service = json_get_child(root, "sr_service");
	if (!sr_service) { json_free(root); return -1; }
	count = json_count_children(sr_service);
	if (count < 0)
		return count;

	newp = realloc(pd_maps, (num_pd_maps + count + 1) * sizeof(*newp));
	if (!newp)
		return -1;
	pd_maps = newp;

	for (it = sr_service->u.value; it; it = it->next) {
		provider = json_get_string(it, "provider");
		service = json_get_string(it, "service");

		if (!provider || !service) {
			fprintf(stderr,
				"failed to parse provdider or service from %s\n",
				file);
			return -1;
		}

		map = &pd_maps[num_pd_maps++];

		map->service = malloc(strlen(provider) + strlen(service) + 2);
		sprintf((char *)map->service, "%s/%s", provider, service);

		map->domain = malloc(strlen(soc) + strlen(domain) + strlen(subdomain) + 3);
		sprintf((char *)map->domain, "%s/%s/%s", soc, domain, subdomain);

		map->instance = number;
		printf("PD_MAP service=%s domain=%s instance=%d\n", map->service, map->domain, map->instance);
	}

	pd_maps[num_pd_maps].service = NULL;

	json_free(root);

	return 0;
}

/* Local integration: scan only the explicitly staged original descriptors. */
static int pd_enumerate_jsons(struct assoc *json_set)
{
    struct dirent *de;
    char path[PATH_MAX];
    DIR *dir = opendir(map_directory);
    int count = 0;
    if (!dir) return -1;
    while ((de = readdir(dir))) {
        size_t n = strlen(de->d_name);
        if (n <= 4 || strcmp(de->d_name + n - 4, ".jsn")) continue;
        if (snprintf(path, sizeof(path), "%s/%s", map_directory, de->d_name) >= (int)sizeof(path)) {
            closedir(dir); return -1;
        }
        struct stat st;
        if (lstat(path, &st) || !S_ISREG(st.st_mode) || st.st_size <= 0 || st.st_size > 65536) {
            closedir(dir); return -1;
        }
        assoc_set(json_set, path, NULL);
        count++;
    }
    closedir(dir);
    printf("PD_DESCRIPTOR_FILES=%d\n", count);
    return count ? 0 : -1;
}

static int pd_load_maps(void)
{
	struct assoc json_set;
	unsigned long it;
	const char *jsn;
	int ret = 0;

	assoc_init(&json_set, 20);

	if (pd_enumerate_jsons(&json_set) < 0) { assoc_destroy(&json_set); return -1; }

	assoc_foreach(jsn, NULL, &json_set, it) {
		ret = pd_load_map(jsn);
		if (ret < 0)
			break;
	}

	assoc_destroy(&json_set);

	return ret;
}

int main(int argc, char **argv)
{
	struct sockaddr_qrtr sq;
	struct qrtr_packet pkt;
	unsigned int msg_id;
	socklen_t sl;
	char buf[4096];
	int ret;
	int fd;

	setvbuf(stdout, NULL, _IOLBF, 0);
	if ((argc != 3 && argc != 4) || strcmp(argv[1], "--maps-dir") || argv[2][0] != '/' ||
	    (argc == 4 && strcmp(argv[3], "--validate"))) {
		fprintf(stderr, "usage: pd-mapper --maps-dir /absolute/directory [--validate]\n"); return 2;
	}
	map_directory = argv[2];
	ret = pd_load_maps();
	if (ret)
		exit(1);

	if (!pd_maps) {
		fprintf(stderr, "no pd maps available\n");
		exit(1);
	}

	if (argc == 4) { puts("PD_MAP_VALIDATION_OK=1"); return 0; }
	fd = qrtr_open(0);
	if (fd < 0) {
		fprintf(stderr, "failed to open qrtr socket\n");
		exit(1);
	}

	ret = qrtr_publish(fd, SERVREG_QMI_SERVICE,
			   SERVREG_QMI_VERSION, SERVREG_QMI_INSTANCE);
	if (ret < 0) {
		fprintf(stderr, "failed to publish service registry service\n");
		exit(1);
	}

	puts("PD_LOCATOR_PUBLISHED=64:257:0");
	for (;;) {
		ret = qrtr_poll(fd, -1);
		if (ret < 0) {
			if (errno == EINTR) {
				continue;
			} else {
				fprintf(stderr, "qrtr_poll failed\n");
				break;
			}
		}

		sl = sizeof(sq);
		ret = recvfrom(fd, buf, sizeof(buf), 0, (void *)&sq, &sl);
		if (ret < 0) {
			ret = -errno;
			if (ret != -ENETRESET)
				fprintf(stderr, "[PD-MAPPER] recvfrom failed: %d\n", ret);
			return ret;
		}

		ret = qrtr_decode(&pkt, buf, ret, &sq);
		if (ret < 0) {
			fprintf(stderr, "[PD-MAPPER] unable to decode qrtr packet\n");
			return ret;
		}

		switch (pkt.type) {
		case QRTR_TYPE_DATA:
			ret = qmi_decode_header(&pkt, &msg_id);
			if (ret < 0)
				continue;

			switch (msg_id) {
			case SERVREG_LOC_GET_DOMAIN_LIST:
				handle_get_domain_list(fd, &pkt);
				break;
			case SERVREG_LOC_PFR:
				printf("[PD-MAPPER] pfr\n");
				break;
			};
			break;
		};
	}

	close(fd);

	return 0;
}
