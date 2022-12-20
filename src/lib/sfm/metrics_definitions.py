import enum
from abc import abstractmethod
from typing import List

from lib.metric_descriptor import SELF_MONITORING_METRIC_PREFIX
from lib.sfm.metrics_timeserie import create_time_serie


class SfmKeys(enum.Enum):
    dynatrace_request_count = 1
    gcp_metric_request_count = 2
    dynatrace_ingest_lines_ok_count = 3
    dynatrace_ingest_lines_invalid_count = 4
    dynatrace_ingest_lines_dropped_count = 5
    setup_execution_time = 6
    fetch_gcp_data_execution_time = 7
    push_to_dynatrace_execution_time = 8
    dynatrace_connectivity = 9


class SfmMetric:
    @abstractmethod
    def generate_time_series(self, context, interval) -> List[dict]:
        pass


class SFMMetricDynatraceRequestCount(SfmMetric):
    name_for_key = "request_count"
    value = {}
    description = "GCP Monitoring API request count [per project]"

    def increment(self, status):
        self.value[status] = self.value.get(status, 0) + 1

    def generate_time_series(self, context, interval):
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key

        for status_code, count in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "response_code": str(status_code),
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url
                },
                [{
                    "interval": interval,
                    "value": {"int64Value": count}
                }]
            ))

        return time_series


class SFMMetricGCPMetricRequestCount(SfmMetric):
    name_for_key = None
    value = {}
    description = "GCP Monitoring API request count [per project]"

    def increment(self, project):
        self.value[project] = self.value.get(project, 0) + 1

    def generate_time_series(self, context, interval):
        # no timeseries generated before, preserving behaviour!!!
        return []


class SFMMetricDynatraceIngestLinesOkCount(SfmMetric):
    name_for_key = "ingest_lines"
    value = {}
    description = "Dynatrace MINT accepted lines count [per project]"

    def update(self, project, lines: int):
        self.value[project] = self.value.get(project, 0) + lines

    def generate_time_series(self, context, interval) -> List[dict]:
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key

        for project_id, count in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url,
                    "status": "Ok",
                    "project_id": project_id,
                },
                [{
                    "interval": interval,
                    "value": {"int64Value": count}
                }]))
        return time_series


class SFMMetricDynatraceIngestLinesInvalidCount(SfmMetric):
    name_for_key = "ingest_lines"
    value = {}
    description = "Dynatrace MINT invalid lines count [per project]"

    def update(self, project, lines: int):
        self.value[project] = self.value.get(project, 0) + lines

    def generate_time_series(self, context, interval):
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key
        for project_id, count in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url,
                    "status": "Invalid",
                    "project_id": project_id,
                },
                [{
                    "interval": interval,
                    "value": {"int64Value": count}
                }]))
        return time_series


class SFMMetricDynatraceIngestLinesDroppedCount(SfmMetric):
    name_for_key = "ingest_lines"
    value = {}
    description = "Dynatrace MINT dropped lines count [per project]"

    def update(self, project, lines: int):
        self.value[project] = self.value.get(project, 0) + lines

    def generate_time_series(self, context, interval):
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key
        for project_id, count in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url,
                    "status": "Dropped",
                    "project_id": project_id,
                },
                [{
                    "interval": interval,
                    "value": {"int64Value": count}
                }]))
        return time_series


class SFMMetricSetupExecutionTime(SfmMetric):
    name_for_key = "phase_execution_time"
    value = {}
    description = "Setup execution time"

    def update(self, project, time):
        self.value[project] = time

    def generate_time_series(self, context, interval):
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key
        for project_id, time in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url,
                    "phase": "setup",
                    "project_id": project_id,
                },
                [{
                    "interval": interval,
                    "value": {"doubleValue": time}
                }],
                "DOUBLE"))
        return time_series


class SFMMetricFetchGCPDataExecutionTime(SfmMetric):
    name_for_key = "phase_execution_time"
    value = {}
    description = "Fetch GCP data execution time [per project]"

    def update(self, project, time):
        self.value[project] = time

    def generate_time_series(self, context, interval):
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key
        for project_id, time in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url,
                    "phase": "fetch_gcp_data",
                    "project_id": project_id,
                },
                [{
                    "interval": interval,
                    "value": {"doubleValue": time}
                }],
                "DOUBLE"))
        return time_series


class SFMMetricPushToDynatraceExecutionTime(SfmMetric):
    name_for_key = "phase_execution_time"
    value = {}
    description = "Push data to Dynatrace execution time [per project]"

    def update(self, project, time):
        self.value[project] = time

    def generate_time_series(self, context, interval):
        time_series = []
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key
        for project_id, time in self.value.items():
            time_series.append(create_time_serie(
                context, key,
                {
                    "function_name": context.function_name,
                    "dynatrace_tenant_url": context.dynatrace_url,
                    "phase": "push_to_dynatrace",
                    "project_id": project_id,
                },
                [{
                    "interval": interval,
                    "value": {"doubleValue": time}
                }],
                "DOUBLE"))
        return time_series


class SFMMetricDynatraceConnectivity(SfmMetric):
    name_for_key = "connectivity"
    value = None
    description = "Dynatrace Connectivity"

    def update(self, value):
        self.value = value

    def generate_time_series(self, context, interval):
        key = SELF_MONITORING_METRIC_PREFIX + "/" + self.name_for_key
        return [create_time_serie(
            context, key,
            {
                "function_name": context.function_name,
                "dynatrace_tenant_url": context.dynatrace_url,
                "reason": self.value.name,
            },
            [{
                "interval": interval,
                "value": {"int64Value": 1}
            }])]
