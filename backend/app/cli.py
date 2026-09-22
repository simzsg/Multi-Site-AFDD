import argparse

from redis import Redis

from app import db, schema, starter_pack
from app.config import Settings
from app.seed import import_inventory, seed
from app.simulation.demo import demo, pack_demo
from app.simulation.jsonl import replay_jsonl
from app.simulation.live import live_source_simulate
from app.simulation.options import LiveSourceOptions, SourceOptions, SyntheticOptions
from app.simulation.source import source_simulate
from app.simulation.synthetic import simulate
from app.workers.evaluation import EvaluationWorker
from app.workers.ingestion import IngestionWorker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "migrate",
            "reset",
            "seed",
            "ingestion",
            "evaluator",
            "simulate",
            "replay",
            "demo",
            "pack-demo",
            "source-simulate",
            "live-source-simulate",
        ],
    )
    parser.add_argument("--inventory")
    parser.add_argument("--pack", default=str(starter_pack.DEFAULT_PACK))
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--acceleration", type=float, default=60)
    parser.add_argument("--wait-for-rule", action="store_true")
    parser.add_argument("--file")
    parser.add_argument("--confirm-review", action="store_true")
    parser.add_argument("--confirm-reset", action="store_true")
    parser.add_argument(
        "--mode",
        choices=[
            "normal",
            "sustained-fault",
            "OFF",
            "missing-data",
            "recovery",
            "duplicate",
            "invalid",
        ],
        default="normal",
    )
    parser.add_argument("--interval", type=int, choices=[15, 60], default=60)
    parser.add_argument("--steps", type=int, default=0)
    parser.add_argument("--buildings")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "replay" and not args.file:
        parser.error("replay requires --file (JSONL; IDs/timestamps preserved)")
    if args.command == "reset" and not args.confirm_reset:
        parser.error("reset requires --confirm-reset")
    settings = Settings.from_env()
    engine = db.connect(settings.database_url)
    try:
        if args.command == "migrate":
            schema.upgrade(engine)
        elif args.command == "reset":
            schema.reset(engine)
            with db.transaction(engine) as conn:
                import_inventory(conn, starter_pack.inventory(args.pack))
        elif args.command == "seed":
            if args.inventory or args.synthetic:
                seed(engine, args.inventory)
            else:
                with db.transaction(engine) as conn:
                    import_inventory(conn, starter_pack.inventory(args.pack))
        elif args.command in {"demo", "pack-demo"}:
            schema.upgrade(engine)
            if args.command == "demo":
                demo(engine, args.confirm_review)
            else:
                pack_demo(engine, args.pack, args.confirm_review)
        elif args.command == "evaluator":
            EvaluationWorker(engine).run_forever()
        else:
            client = Redis.from_url(settings.redis_url, decode_responses=True)
            try:
                if args.command == "ingestion":
                    IngestionWorker(engine, client, settings.telemetry_stream).run_forever()
                elif args.command == "source-simulate":
                    source_simulate(
                        engine,
                        SourceOptions(
                            pack=args.pack,
                            acceleration=args.acceleration,
                            wait_for_rule=args.wait_for_rule,
                            steps=args.steps,
                            buildings=args.buildings,
                        ),
                        client=client,
                        stream=settings.telemetry_stream,
                    )
                elif args.command == "live-source-simulate":
                    live_source_simulate(
                        engine,
                        LiveSourceOptions(
                            pack=args.pack,
                            interval=args.interval,
                            wait_for_rule=args.wait_for_rule,
                            steps=args.steps,
                            buildings=args.buildings,
                        ),
                        client=client,
                        stream=settings.telemetry_stream,
                    )
                elif args.command == "simulate":
                    simulate(
                        engine,
                        SyntheticOptions(
                            mode=args.mode,
                            interval=args.interval,
                            steps=args.steps,
                            buildings=args.buildings,
                        ),
                        client=client,
                        stream=settings.telemetry_stream,
                    )
                elif args.command == "replay":
                    replay_jsonl(args.file, client=client, stream=settings.telemetry_stream)
            finally:
                client.close()
    finally:
        engine.dispose()
