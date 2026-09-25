from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / 'deploy' / 'compose.yaml'


def _compose() -> dict[str, object]:
    return yaml.safe_load(COMPOSE.read_text(encoding='utf-8'))


def test_deploy_services_do_not_publish_host_ports_or_use_latest_images() -> None:
    compose = _compose()
    services = compose['services']
    assert isinstance(services, dict)
    for service in services.values():
        assert isinstance(service, dict)
        assert 'ports' not in service
        image = str(service.get('image', ''))
        assert ':latest' not in image


def test_redis_is_tls_only_private_and_fail_closed_api_uses_distributed_backend() -> None:
    compose = _compose()
    services = compose['services']
    redis = services['redis']
    api = services['api']
    assert '--port' in redis['command']
    assert redis['command'][redis['command'].index('--port') + 1] == '0'
    assert '--tls-port' in redis['command']
    assert redis['user'] == '999:1000'
    assert 'uid=999,gid=1000' in redis['tmpfs'][0]
    assert api['environment']['RATE_LIMIT_BACKEND'] == 'distributed'
    assert api['environment']['RATE_LIMIT_BACKEND_CA_CERT_PATH'].startswith('/run/secrets/')
    assert 'redis' in api['depends_on']
    assert compose['networks']['backend']['internal'] is True


def test_runtime_secrets_are_files_not_environment_values() -> None:
    compose = _compose()
    api = compose['services']['api']
    migrate = compose['services']['migrate']
    redis = compose['services']['redis']
    serialized_environment = str(api['environment']).lower()
    assert 'database_url' not in serialized_environment
    assert 'rate_limit_backend_url' not in serialized_environment
    assert {'database_url', 'rate_limit_backend_url'} <= set(api['secrets'])
    expected_group = '${SERDIAL21_SECRETS_GID:?Defina SERDIAL21_SECRETS_GID}'
    assert api['group_add'] == [expected_group]
    assert migrate['group_add'] == [expected_group]
    assert redis['group_add'] == [expected_group]


def test_deploy_frontend_is_real_bridge_while_factory_default_stays_synthetic() -> None:
    deploy_config = (ROOT / 'deploy' / 'web' / 'config.js').read_text(encoding='utf-8')
    factory_config = (ROOT / 'app' / 'config.js').read_text(encoding='utf-8')
    assert "dataMode: 'real'" in deploy_config
    assert "authMode: 'bridge'" in deploy_config
    assert "dataMode: 'synthetic'" in factory_config
    assert "authMode: 'synthetic'" in factory_config


def test_public_deploy_example_uses_confirmed_domain_and_bridge_identity() -> None:
    environment = (ROOT / 'deploy' / '.env.example').read_text(encoding='utf-8')
    assert 'SERDIAL21_PUBLIC_HOST=contabilidade.serdial21.com' in environment
    assert (
        'OIDC_ISSUER=https://lgohzjneyvdtonpeapvd.functions.supabase.co/'
        'sistema-b-bridge'
    ) in environment
    assert 'OIDC_AUDIENCE=serdial21-sistema-b' in environment
    assert (
        'OIDC_JWKS_URL=https://lgohzjneyvdtonpeapvd.functions.supabase.co/'
        'sistema-b-jwks'
    ) in environment


def test_api_container_runs_as_non_root_and_loads_only_named_secret_files() -> None:
    dockerfile = (ROOT / 'deploy' / 'api' / 'Dockerfile').read_text(encoding='utf-8')
    entrypoint = (ROOT / 'deploy' / 'api' / 'entrypoint.sh').read_text(encoding='utf-8')
    assert 'USER 10001:10001' in dockerfile
    assert '/run/secrets/database_url' in entrypoint
    assert '/run/secrets/rate_limit_backend_url' in entrypoint
    assert '.env' not in entrypoint
