import pulumi
import pulumi_kubernetes as k8s
from pulumi_random import RandomPassword

from config import app_label, app_name, config, namespace
from db import database, password
from db import service as db_service
from db import user

# Setup Vars
component_name = 'api'
app_version = config.get('app_version', default='latest')
component_label = {'component': component_name}
labels = {**app_label, **component_label}
prefix = f'{app_name}-{component_name}'
fqdn = config.require('fqdn')
tz = config.get('tz')

# Generate Secret
jwt_secret = RandomPassword(
    f'{prefix}-jwt-secret',
    length=32,
    special=False,
)

# Setup Config Map
config_map = k8s.core.v1.ConfigMap(
    f'{prefix}-config',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=prefix,
        namespace=namespace.metadata['name'],
        labels=labels,
    ),
    data={
        'VIKUNJA_SERVICE_FRONTENDURL': 'http://vikunja-frontend',
        'VIKUNJA_SERVICE_TIMEZONE': tz,
        'VIKUNJA_REDIS_ENABLED': 'true',
        'VIKUNJA_REDIS_HOST': 'vikunja-redis:6379',
    },
)
# Setup Secret
secret = k8s.core.v1.Secret(
    f'{prefix}-secret',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=prefix,
        namespace=namespace.metadata['name'],
        labels=labels,
    ),
    string_data={
        'VIKUNJA_DATABASE_HOST': db_service.metadata['name'],
        'VIKUNJA_DATABASE_PASSWORD': password.result,
        'VIKUNJA_DATABASE_TYPE': 'mysql',
        'VIKUNJA_DATABASE_USER': user,
        'VIKUNJA_DATABASE_DATABASE': database,
        'VIKUNJA_SERVICE_JWTSECRET': jwt_secret.result,
        'VIKUNJA_SERVICE_FRONTENDURL': fqdn,
    },
)

# Setup Deployment
deployment = k8s.apps.v1.Deployment(
    f'{prefix}-deployment',
    api_version='v1',
    kind='Deployment',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=prefix,
        namespace=namespace.metadata['name'],
        labels=labels,
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels=labels,
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels=labels,
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name=prefix,
                        image=f'vikunja/api:{app_version}',
                        image_pull_policy='IfNotPresent',
                        liveness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path='/api/v1/info',
                                port=component_name,
                            ),
                            period_seconds=10,
                            timeout_seconds=1,
                            failure_threshold=3,
                        ),
                        ports=[
                            k8s.core.v1.ContainerPortArgs(
                                container_port=3456, name=component_name
                            ),
                        ],
                        env_from=[
                            k8s.core.v1.EnvFromSourceArgs(
                                secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                                    name=secret.metadata['name'],
                                )
                            ),
                            k8s.core.v1.EnvFromSourceArgs(
                                config_map_ref=k8s.core.v1.ConfigMapEnvSourceArgs(
                                    name=config_map.metadata['name'],
                                )
                            ),
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                mount_path='/app/vikunja/files',
                                name=prefix,
                            )
                        ],
                    ),
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name=prefix,
                        host_path=k8s.core.v1.HostPathVolumeSourceArgs(
                            path=f'/opt/{app_name}/{component_name}',
                        ),
                    ),
                ],
            ),
        ),
    ),
)

# Setup Service
service = k8s.core.v1.Service(
    f'{prefix}-service',
    api_version='v1',
    kind='Service',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=prefix,
        namespace=namespace.metadata['name'],
        labels=labels,
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        type='ClusterIP',
        selector=labels,
        ports=[
            k8s.core.v1.ServicePortArgs(
                port=3456,
            )
        ],
    ),
    opts=pulumi.ResourceOptions(
        parent=deployment, depends_on=[deployment], delete_before_replace=True
    ),
)
