import pulumi
import pulumi_kubernetes as k8s

from config import app_label, app_name, config, namespace

# Setup Vars
component_name = 'frontend'
app_version = config.get('app_version', default='latest')
component_label = {'component': component_name}
labels = {**app_label, **component_label}
prefix = f'{app_name}-{component_name}'
fqdn = config.require('fqdn')
api_url = f'{fqdn}/api/v1'

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
                        image=f'vikunja/frontend:{app_version}',
                        ports=[
                            k8s.core.v1.ContainerPortArgs(
                                container_port=80,
                                name=component_name,
                            ),
                        ],
                        env=[
                            k8s.core.v1.EnvVarArgs(
                                name='VIKUNJA_API_URL',
                                value=api_url,
                            )
                        ],
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
                name=component_name,
                port=80,
                target_port=80,
            )
        ],
    ),
    opts=pulumi.ResourceOptions(
        parent=deployment, depends_on=[deployment], delete_before_replace=True
    ),
)
