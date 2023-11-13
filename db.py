import pulumi
import pulumi_kubernetes as k8s
from pulumi_random import RandomPassword

from config import app_label, app_name, config, namespace

# Setup Vars
component_name = 'mariadb'
component_label = {'component': component_name}
labels = {**app_label, **component_label}
prefix = f'{app_name}-{component_name}'
user = config.get('db-user', default=app_name)
database = config.get('db-name', default=app_name)

# Setup Secret
password = RandomPassword(
    f'{prefix}-password',
    length=16,
    special=False,
)
root_password = RandomPassword(
    f'{prefix}-root-password',
    length=16,
    special=False,
)
secret = k8s.core.v1.Secret(
    f'{prefix}-secret',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=prefix,
        namespace=namespace.metadata['name'],
        labels=labels,
    ),
    string_data={
        'MYSQL_USER': user,
        'MYSQL_PASSWORD': password.result,
        'MYSQL_ROOT_PASSWORD': root_password.result,
        'MYSQL_DATABASE': database,
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
                        name='mariadb',
                        image='mariadb:10',
                        args=[
                            '--character-set-server=utf8mb4',
                            '--collation-server=utf8mb4_unicode_ci',
                        ],
                        env_from=[
                            k8s.core.v1.EnvFromSourceArgs(
                                secret_ref=k8s.core.v1.SecretReferenceArgs(
                                    name=secret.metadata['name'],
                                ),
                            )
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                mount_path='/var/lib/mysql',
                                name=component_name,
                            )
                        ],
                        ports=[
                            k8s.core.v1.ContainerPortArgs(
                                container_port=3306,
                                name=component_name,
                                protocol='TCP',
                            )
                        ],
                    )
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name=component_name,
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
                port=3306,
                target_port=component_name,
            )
        ],
    ),
    opts=pulumi.ResourceOptions(
        parent=deployment, depends_on=[deployment], delete_before_replace=True
    ),
)
