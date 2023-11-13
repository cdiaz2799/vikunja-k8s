import pulumi
from pulumi_kubernetes import apps, core, meta

from config import app_label, app_name, namespace

# Setup Vars
component_name = 'redis'
component_label = {'component': component_name}
prefix = f'{app_name}-{component_name}'

app_labels = {**app_label, **component_label}
volume_name = 'redis-data'

# Setup Deployment
redis_deployment = apps.v1.Deployment(
    f'{prefix}-deployment',
    metadata={
        'name': prefix,
        'namespace': namespace.metadata['name'],
        'labels': app_labels,
    },
    spec=apps.v1.DeploymentSpecArgs(
        selector=meta.v1.LabelSelectorArgs(
            match_labels=app_labels,
        ),
        replicas=1,
        template=core.v1.PodTemplateSpecArgs(
            metadata=meta.v1.ObjectMetaArgs(labels=app_labels),
            spec=core.v1.PodSpecArgs(
                containers=[
                    core.v1.ContainerArgs(
                        name=component_name,
                        image='redis',
                        ports=[
                            core.v1.ContainerPortArgs(
                                container_port=6379, name=component_name
                            )
                        ],
                    )
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(delete_before_replace=True),
)

# Setup Service
redis_service = core.v1.Service(
    f'{prefix}-service',
    metadata={
        'name': prefix,
        'namespace': namespace.metadata['name'],
        'labels': app_labels,
    },
    spec=core.v1.ServiceSpecArgs(
        selector=app_labels,
        ports=[
            core.v1.ServicePortArgs(
                name=component_name,
                protocol='TCP',
                port=6379,
                target_port=component_name,
            )
        ],
    ),
    opts=pulumi.ResourceOptions(
        parent=redis_deployment, delete_before_replace=True
    ),
)
