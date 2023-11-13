import pulumi_kubernetes as k8s

from api import service as api_service
from config import app_name, namespace
from frontend import component_name as frontend_component
from frontend import fqdn
from frontend import service as frontend_service

# Setup Vars
host = fqdn.replace('https://', '')
backend_paths = ['/api', '/dav', '/api/v1']
# Setup Ingress
ingress = k8s.networking.v1.Ingress(
    f'{app_name}-ingress',
    api_version='networking.k8s.io/v1',
    kind='Ingress',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=namespace,
    ),
    spec=k8s.networking.v1.IngressSpecArgs(
        ingress_class_name='nginx',
        rules=[
            k8s.networking.v1.IngressRuleArgs(
                host=host,
                http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                    paths=[
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path='/',
                            path_type='Prefix',
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name=frontend_service.metadata['name'],
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        name=frontend_component,
                                    ),
                                )
                            ),
                        ),
                    ]
                    + [
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path=path,
                            path_type='Prefix',
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name=api_service.metadata['name'],
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=3456,
                                    ),
                                )
                            ),
                        )
                        for path in backend_paths
                    ],
                ),
            ),
            k8s.networking.v1.IngressRuleArgs(
                host='vikunja.local',
                http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                    paths=[
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path='/api/v1',
                            path_type='Prefix',
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name=api_service.metadata['name'],
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=3456,
                                    ),
                                )
                            ),
                        ),
                    ],
                ),
            ),
        ],
    ),
)
