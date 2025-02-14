#     Copyright 2020 Dynatrace LLC
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import os
from os import listdir
from os.path import isfile
from typing import List, Dict

import yaml

from lib.context import LoggingContext
from lib.metrics import GCPService

HOSTNAME = os.environ.get("HOSTNAME", "")

K8S_CONTAINER_NAME_PREFIX = "dynatrace-gcp-monitor"


def chunks(full_list: List, chunk_size: int) -> List[List]:
    chunk_size = max(1, chunk_size)
    return [full_list[i:i + chunk_size] for i in range(0, len(full_list), chunk_size)]


def read_activation_yaml():
    activation_file_path = '/code/config/activation/gcp_services.yaml'
    try:
        with open(activation_file_path, encoding="utf-8") as activation_file:
            activation_yaml = yaml.safe_load(activation_file)
    except Exception:
        activation_yaml = yaml.safe_load(os.environ.get("ACTIVATION_CONFIG", ""))
    if not activation_yaml:
        activation_yaml = {}
    return activation_yaml


def get_activation_config_per_service(activation_yaml):
    return {service_activation.get('service'): service_activation for service_activation in
            activation_yaml['services']} if activation_yaml and activation_yaml['services'] else {}


def load_activated_feature_sets(logging_context: LoggingContext, activation_yaml) -> List[str]:
    services_allow_list = []
    for service in activation_yaml.get("services", []):
        feature_sets = service.get("featureSets", [])
        for feature_set in feature_sets:
            services_allow_list.append(f"{service.get('service')}/{feature_set}")
        if not feature_sets:
            logging_context.error(f"No feature set in given {service} service.")

    return services_allow_list


def is_yaml_file(f: str) -> bool:
    return f.endswith(".yml") or f.endswith(".yaml")


def extract_technology_name(config_yaml):
    technology_name = config_yaml.get("technology", {})
    if isinstance(technology_name, Dict):
        technology_name = technology_name.get("name", "N/A")
    return technology_name

# For test_integration_metric.py
def load_supported_services() -> List[GCPService]:
    context = LoggingContext(None)
    activation_yaml = read_activation_yaml()
    activation_config_per_service = get_activation_config_per_service(activation_yaml)
    feature_sets_from_activation_config = load_activated_feature_sets(context, activation_yaml)

    working_directory = os.path.dirname(os.path.realpath(__file__))
    config_directory = os.path.join(working_directory, "config")
    config_files = [
        file for file
        in listdir(config_directory)
        if isfile(os.path.join(config_directory, file)) and is_yaml_file(file)
    ]

    services = []
    for file in config_files:
        config_file_path = os.path.join(config_directory, file)
        try:
            with open(config_file_path, encoding="utf-8") as config_file:
                config_yaml = yaml.safe_load(config_file)
                technology_name = extract_technology_name(config_yaml)

                for service_yaml in config_yaml.get("gcp", {}):
                    service_name = service_yaml.get("service", "None")
                    feature_set = service_yaml.get("featureSet", "default_metrics")
                    # If allow_list of services exists and current service is not present in it, skip
                    # If allow_list is empty - no services explicitly selected - load all available
                    allow_list_exists = feature_sets_from_activation_config.__len__() > 0
                    if f'{service_name}/{feature_set}' in feature_sets_from_activation_config or not allow_list_exists:
                        activation = activation_config_per_service.get(service_name, {})
                        services.append(GCPService(tech_name=technology_name, **service_yaml, activation=activation))

        except Exception as error:
            context.log(f"Failed to load configuration file: '{config_file_path}'. Error details: {error}")
            continue
    feature_sets = [f"{service.name}/{service.feature_set}" for service in services]
    if feature_sets:
        context.log("Selected feature sets: " + ", ".join(feature_sets))
    else:
        context.log("Empty feature sets. GCP services not monitored.")
    return services
