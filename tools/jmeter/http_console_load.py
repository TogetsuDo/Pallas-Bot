#!/usr/bin/env python3
"""控制台只读 API 并发压测（JMeter 不可用时的等价探针，输出 JTL 风格摘要）。"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]


async def worker(
    client: httpx.AsyncClient,
    paths: list[str],
    stop_at: float,
    samples: list[tuple[str, int, bool]],
) -> None:
    i = 0
    while time.perf_counter() < stop_at:
        path = paths[i % len(paths)]
        i += 1
        t0 = time.perf_counter()
        ok = False
        try:
            resp = await client.get(path)
            ok = resp.status_code == 200
        except httpx.HTTPError:
            ok = False
        ms = int((time.perf_counter() - t0) * 1000)
        samples.append((path, ms, ok))


async def main_async(args: argparse.Namespace) -> int:
    paths = [
        "/pallas/api/shard-observability",
        "/pallas/api/corpus-status",
        "/pallas/api/plugin-run-stats",
        "/pallas/api/system",
    ]
    base = f"http://{args.host}:{args.port}"
    headers = {"X-Pallas-Token": args.token, "Accept": "application/json"}
    samples: list[tuple[str, int, bool]] = []
    stop_at = time.perf_counter() + args.duration_sec

    limits = httpx.Limits(max_connections=args.concurrency * 2, max_keepalive_connections=args.concurrency)
    async with httpx.AsyncClient(base_url=base, headers=headers, timeout=15.0, limits=limits) as client:
        tasks = [asyncio.create_task(worker(client, paths, stop_at, samples)) for _ in range(args.concurrency)]
        await asyncio.gather(*tasks)

    by: dict[str, list[int]] = defaultdict(list)
    ok_count = 0
    for path, ms, ok in samples:
        by[path].append(ms)
        if ok:
            ok_count += 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    summary_path = out_dir / f"summary_http_{stamp}.txt"
    lines = [
        f"# HTTP 并发压测 {base}",
        f"concurrency={args.concurrency} duration_sec={args.duration_sec} total_samples={len(samples)} ok={ok_count}",
        "",
    ]
    for path in sorted(by):
        ms = sorted(by[path])
        p95 = ms[int(len(ms) * 0.95) - 1] if ms else 0
        lines.append(
            f"GET {path}: samples={len(ms)} avg_ms={statistics.mean(ms):.1f} p95_ms={p95}"
        )
    text = "\n".join(lines) + "\n"
    summary_path.write_text(text, encoding="utf-8")
    print(text)
    json_path = out_dir / f"http_load_{stamp}.json"
    json_path.write_text(
        json.dumps({"samples": len(samples), "ok": ok_count, "by_path": {k: len(v) for k, v in by.items()}}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {summary_path}")
    return 0 if ok_count > len(samples) * 0.95 else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8088)
    p.add_argument("--token", required=True)
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--duration-sec", type=int, default=60)
    p.add_argument("--out-dir", default=str(ROOT / "data" / "bot" / "jmeter"))
    return asyncio.run(main_async(p.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
