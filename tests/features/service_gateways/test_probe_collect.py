import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import AsyncMock

from packages.sing.config import Config

from pallas.product.service_gateways.media_probe import (
    maa_hub_probe_note,
    probe_draw_ai_runtime,
    probe_image_gateways,
    probe_maa_endpoints,
    probe_sing_server,
    sing_probe_urls,
)


def _patch_draw_import_plugin_submodule(
    monkeypatch,
    *,
    settings_factory,
    runtime_factory: Callable[[], SimpleNamespace] | None = None,
) -> None:
    fake_config = SimpleNamespace(active_image_gen_settings=settings_factory)
    fake_probe = SimpleNamespace(
        image_gen_settings_from_draft=lambda _draft: settings_factory(),
        probe_all_backends=AsyncMock(return_value=[]),
    )
    fake_runtime = runtime_factory() if runtime_factory else None

    def fake_import(plugin_id: str, submodule: str):
        if plugin_id == "draw" and submodule == "config":
            return fake_config
        if plugin_id == "draw" and submodule == "gateway_probe":
            return fake_probe
        if plugin_id == "draw" and submodule == "runtime_state" and fake_runtime is not None:
            return fake_runtime
        raise AssertionError(f"unexpected import_plugin_submodule({plugin_id!r}, {submodule!r})")

    monkeypatch.setattr(
        "pallas.product.service_gateways.media_probe.import_plugin_submodule",
        fake_import,
    )
    monkeypatch.setattr(
        "pallas.core.platform.plugin_runtime.resolve.import_plugin_submodule",
        fake_import,
    )


def test_sing_probe_urls() -> None:
    urls = sing_probe_urls("http://127.0.0.1:9099")
    assert urls == [("健康检查", "http://127.0.0.1:9099/health")]


def test_probe_sing_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        "packages.sing.config.get_sing_config",
        lambda: Config(sing_enable=False),
    )
    results = asyncio.run(probe_sing_server())
    assert len(results) == 1
    assert results[0].error == "未启用 sing_enable"
    assert results[0].runtime_state == "disabled"
    assert results[0].capability_id == "media.sing"
    assert results[0].capability_group == "media"
    assert results[0].runtime_type == "media"
    assert results[0].failure_class == "runtime_disabled"


def test_probe_sing_success_sets_runtime_state(monkeypatch) -> None:
    async def fake_probe_http_get(*args, **kwargs):
        _ = args, kwargs
        from pallas.core.shared.service_probe import ServiceProbeResult

        capability = kwargs["capability"]
        assert capability.capability_id == "media.sing"
        return ServiceProbeResult("唱歌", "健康检查", True, 12, 200, None)

    async def fake_media_task_runtime(**kwargs):
        _ = kwargs
        return None

    monkeypatch.setattr(
        "pallas.product.service_gateways.media_probe.probe_http_get",
        fake_probe_http_get,
    )
    monkeypatch.setattr(
        "pallas.product.service_gateways.media_probe.probe_ai_media_task_runtime",
        fake_media_task_runtime,
    )
    results = asyncio.run(probe_sing_server(cfg=Config(sing_enable=True)))
    assert len(results) == 1
    assert results[0].ok is True
    assert results[0].runtime_state == "healthy"
    assert results[0].capability_id == "media.sing"
    assert results[0].capability_group == "media"
    assert results[0].runtime_type == "media"
    assert results[0].health_state == "healthy"


def test_probe_draw_ai_runtime_enabled(monkeypatch) -> None:
    class _Cfg:
        runtime_mode = "ai_service_runtime"
        ai_runtime_fallback_to_plugin = True

    class _State:
        consecutive_failures = 0
        recent_failure_reason = ""

    _patch_draw_import_plugin_submodule(
        monkeypatch,
        settings_factory=lambda: _Cfg(),
        runtime_factory=lambda: SimpleNamespace(
            ai_runtime_circuit_status=lambda: _State(),
            ai_runtime_circuit_is_open=lambda: False,
        ),
    )
    result = probe_draw_ai_runtime()
    assert result.category == "牛牛画画"
    assert result.site == "AI runtime"
    assert result.ok is True
    assert result.runtime_state == "healthy"
    assert result.error == "正常（开启回退）"
    assert result.capability_id == "image.generate"
    assert result.capability_group == "media"
    assert result.runtime_type == "image"
    assert result.health_state == "healthy"
    assert result.circuit_state == "closed"
    assert result.consecutive_failures == 0


def test_probe_draw_ai_runtime_prefers_ai_health_circuit() -> None:
    result = probe_draw_ai_runtime(
        type("Cfg", (), {"runtime_mode": "ai_service_runtime", "ai_runtime_fallback_to_plugin": True})(),
        ai_health={
            "image": {
                "backends": [
                    {
                        "circuit_state": "open",
                        "consecutive_failures": 2,
                        "recent_failure_class": "timeout",
                    },
                ],
            },
        },
    )
    assert result.ok is False
    assert result.circuit_state == "open"
    assert "AI 服务熔断中" in (result.error or "")


def test_probe_draw_ai_runtime_circuit_open(monkeypatch) -> None:
    class _Cfg:
        runtime_mode = "ai_service_runtime"
        ai_runtime_fallback_to_plugin = False

    class _State:
        consecutive_failures = 3
        recent_failure_reason = "超时"

    _patch_draw_import_plugin_submodule(
        monkeypatch,
        settings_factory=lambda: _Cfg(),
        runtime_factory=lambda: SimpleNamespace(
            ai_runtime_circuit_status=lambda: _State(),
            ai_runtime_circuit_is_open=lambda: True,
        ),
    )
    result = probe_draw_ai_runtime()
    assert result.ok is False
    assert result.runtime_state == "degraded"
    assert result.error == "熔断中（连续失败 3 次，不回退）"
    assert result.capability_id == "image.generate"
    assert result.capability_group == "media"
    assert result.runtime_type == "image"
    assert result.failure_class == "runtime_degraded"
    assert result.health_state == "degraded"
    assert result.circuit_state == "open"
    assert result.consecutive_failures == 3


def test_probe_image_gateways_unconfigured_capability_metadata(monkeypatch) -> None:
    class _Settings:
        def api_backends(self):
            return []

    _patch_draw_import_plugin_submodule(
        monkeypatch,
        settings_factory=lambda: _Settings(),
    )
    results = asyncio.run(probe_image_gateways())
    assert len(results) == 1
    assert results[0].capability_id == "image.generate"
    assert results[0].capability_group == "media"
    assert results[0].runtime_type == "image"
    assert results[0].failure_class == "runtime_unavailable"


def test_maa_hub_probe_note_sets_runtime_detail() -> None:
    from pallas.core.shared.service_probe import ServiceProbeResult

    results = maa_hub_probe_note([
        ServiceProbeResult(
            "MAA远控",
            "获取任务",
            True,
            8,
            200,
            None,
            capability_id="automation.maa",
            capability_group="automation",
            runtime_type="automation",
        )
    ])
    assert results[0].runtime_state == "healthy"
    assert "hub 入口已响应" in (results[0].runtime_detail or "")
    assert results[0].capability_id == "automation.maa"
    assert results[0].capability_group == "automation"
    assert results[0].runtime_type == "automation"


def test_probe_maa_endpoints_sets_runtime_state(monkeypatch) -> None:
    from pallas.core.shared.service_probe import ServiceProbeResult

    class _Cfg:
        pass

    class _Endpoints:
        get_task_url = "http://127.0.0.1:9000/get"
        report_status_url = "http://127.0.0.1:9000/report"

    async def fake_probe_http_post_json(*args, **kwargs):
        site = kwargs["site"]
        capability = kwargs["capability"]
        assert capability.capability_id == "automation.maa"
        return ServiceProbeResult(
            "MAA远控",
            site,
            True,
            9,
            200,
            None,
            capability_id="automation.maa",
            capability_group="automation",
            runtime_type="automation",
        )

    monkeypatch.setattr(
        "packages.maa.endpoints.resolve_maa_probe_http_endpoints",
        lambda cfg=None: _Endpoints(),
    )
    monkeypatch.setattr(
        "pallas.product.service_gateways.media_probe.probe_http_post_json",
        fake_probe_http_post_json,
    )
    monkeypatch.setattr(
        "pallas.core.platform.shard.context.sharding_active",
        lambda: False,
    )
    results = asyncio.run(probe_maa_endpoints(cfg=_Cfg()))
    assert len(results) == 2
    assert all(item.runtime_state == "healthy" for item in results)
    assert all(item.capability_id == "automation.maa" for item in results)
    assert all(item.capability_group == "automation" for item in results)
    assert all(item.runtime_type == "automation" for item in results)
    assert all(item.health_state == "healthy" for item in results)
