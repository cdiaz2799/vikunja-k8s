import pulumi
import pulumi_kubernetes as k8s

# Setup Config
config = pulumi.Config('vikunja')

# Setup Vars
app_name = 'vikunja'
app_label = {'app': app_name}

# Setup Namespace
namespace = k8s.core.v1.Namespace(
    f'{app_name}-namespace',
    metadata=k8s.meta.v1.ObjectMetaArgs(name='vikunja', labels=app_label),
)

# Setup Outputs
pulumi.export('namespace', namespace.metadata.apply(lambda x: x.name))
