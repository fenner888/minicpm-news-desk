import argparse
import json
import os
from pathlib import Path
from .workflow import article_report, read_json, snapshot_report
from . import selector


def main():
    parser=argparse.ArgumentParser(description='Local, review-required news reports. No scheduler or publishing.')
    commands=parser.add_subparsers(dest='command',required=True)
    demo=commands.add_parser('demo',help='Offline synthetic selector example, zero model calls')
    demo.add_argument('--out',required=True,type=Path)
    snap=commands.add_parser('snapshot',help='Render a saved collector snapshot; no network')
    snap.add_argument('--input',required=True,type=Path); snap.add_argument('--out',required=True,type=Path)
    article=commands.add_parser('article',help='Explicit one-article fetch, or saved HTML import')
    article.add_argument('--source',required=True,choices=['openai','xai','spacexai','github'])
    article.add_argument('--url',required=True); article.add_argument('--html',type=Path)
    article.add_argument('--snapshot',type=Path,help='Optional collector snapshot to retain known publication/discovery dates')
    article.add_argument('--out',required=True,type=Path)
    prepare=commands.add_parser('prepare',help='Retain source details without inference')
    prepare.add_argument('--article',required=True,type=Path);prepare.add_argument('--out',required=True,type=Path)
    model=commands.add_parser('select',help='One explicit local ID-selection request; no retry/fallback')
    model.add_argument('--article',required=True,type=Path); model.add_argument('--config',required=True,type=Path)
    model.add_argument('--out',required=True,type=Path)
    model.add_argument('--allow-local-inference',action='store_true',required=True)
    saved=commands.add_parser('apply-selection',help='Validate a saved response; no inference; origin unverified')
    saved.add_argument('--article',required=True,type=Path);saved.add_argument('--config',required=True,type=Path)
    saved.add_argument('--response',required=True,type=Path);saved.add_argument('--packet-sha256',required=True)
    saved.add_argument('--out',required=True,type=Path)
    args=parser.parse_args(); os.umask(0o077)
    try:
        if args.command=='demo':
            result=selector.demo(args.out)
        elif args.command=='prepare':
            result=selector.prepare_report(read_json(args.article,500000),args.out)
        elif args.command=='apply-selection':
            result=selector.selection_report(read_json(args.article,500000),read_json(args.config,4000),args.out,
                saved_response=read_json(args.response,1000000),expected_packet=args.packet_sha256)
        elif args.command=='snapshot':
            result=snapshot_report(read_json(args.input),args.out)
        elif args.command=='article':
            raw=None
            if args.html:
                with args.html.open('rb') as f: raw=f.read(2_000_001)
            metadata=None
            if args.snapshot:
                from .core import normalize_snapshot,source_id
                matches=[i for i in normalize_snapshot(read_json(args.snapshot)) if i['source']==source_id(args.source) and i['url'].rstrip('/')==args.url.rstrip('/')]
                if len(matches)!=1: raise ValueError('snapshot_article_identity_mismatch')
                metadata=matches[0]
            result=article_report(args.source,args.url,args.out,raw=raw,metadata=metadata)
        else:
            result=selector.selection_report(read_json(args.article,500000),read_json(args.config,4000),args.out)
        print(json.dumps({'status':result['status'],'model_attempts':result['model_attempts'],
                          'fetch_attempts':result['fetch_attempts'],'report':str(args.out/'index.html')}))
        return 0
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__,
                          'detail':'No retries or fallback; inspect the output manifest if created.'}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
