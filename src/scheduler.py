"""APScheduler 3.x foreground runner: one job at a time, scheduled local timezone."""
import argparse
import os
import json
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from .run_backup import execute
from .runtime import load_environment, ROOT
from .report_manager import write_json


def scheduled_test(seconds, demo=False):
    """One actual scheduled execution, then stop; daily .env stays unchanged."""
    engine = BlockingScheduler(timezone=os.getenv('BACKUP_TIMEZONE', 'Asia/Ho_Chi_Minh'))
    due = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    outcome = {'status': 'FAILED', 'error_type': 'NOT_EXECUTED'}

    def job():
        try:
            result = execute(demo=demo)
            outcome.clear()
            outcome.update(result, scheduled_for_utc=due.isoformat(), trigger='date')
            path = (ROOT / 'demo' if demo else ROOT) / 'reports' / 'scheduled_test.json'
            write_json(path, outcome)
            print(json.dumps(outcome), flush=True)
        except Exception as error:
            outcome.update(status='FAILED', error_type=type(error).__name__)
        finally:
            engine.shutdown(wait=False)

    engine.add_job(job, DateTrigger(run_date=due), id='scheduled_test',
                   max_instances=1, coalesce=True, misfire_grace_time=60)
    print(f'One scheduled backup in {seconds}s ({due.isoformat()} UTC); stops after completion.', flush=True)
    try:
        engine.start()
    except KeyboardInterrupt:
        if engine.running:
            engine.shutdown(wait=False)
        return 1
    return 0 if outcome['status'] == 'SUCCESS' else 1


def main(argv=None):
    load_environment()
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='Run a single backup now')
    parser.add_argument('--demo', action='store_true', help='Offline demo in separate demo/ directory')
    parser.add_argument('--test-after', type=int, metavar='SECONDS', help='Schedule one backup after 1..3600 seconds, then stop')
    args = parser.parse_args(argv)
    if args.test_after is not None:
        if args.once or not 1 <= args.test_after <= 3600:
            parser.error('--test-after requires 1..3600 seconds and cannot be combined with --once')
        return scheduled_test(args.test_after, demo=args.demo)
    if args.once:
        result = execute(demo=args.demo)
        print(result)
        return 0 if result['status'] == 'SUCCESS' else 1
    tz = os.getenv('BACKUP_TIMEZONE', 'Asia/Ho_Chi_Minh')
    hour = int(os.getenv('BACKUP_HOUR', '2'))
    minute = int(os.getenv('BACKUP_MINUTE', '0'))
    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_job(execute, CronTrigger(hour=hour, minute=minute, timezone=tz),
                      kwargs={'demo': args.demo},
                      id='network_backup', replace_existing=True, max_instances=1,
                      coalesce=True, misfire_grace_time=1800)
    print(f'Backup scheduled every day at {hour:02d}:{minute:02d} ({tz}). Ctrl+C to stop.', flush=True)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    raise SystemExit(main())
