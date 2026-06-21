from __future__ import annotations
import argparse
import asyncio
import json
import logging
from .client import MykoPlusClient

async def _run(args: argparse.Namespace) -> int:
    async with MykoPlusClient(args.email, args.password) as client:
        await client.login()
        if args.command == 'login':
            print('Login OK — user_id:', client.user_id)
            return 0
        if args.command == 'homes':
            for h in await client.get_homes():
                print(h.home_id, '\t', h.name, '\t devices:', h.device_ids)
            return 0
        if args.command == 'devices':
            for d in await client.get_devices():
                print(d.device_id, '\t', d.name, '\t', d.reference, '\t power=', d.is_on, '\t connected=', d.connected)
            return 0
        if args.command in ('on', 'off'):
            await client.async_set_power(args.device, args.command == 'on')
            print(f'{args.device} -> {args.command}')
            return 0
    return 1

def main() -> int:
    p = argparse.ArgumentParser(prog='mykoplus')
    p.add_argument('command', choices=['login', 'homes', 'devices', 'on', 'off'])
    p.add_argument('--email', required=True)
    p.add_argument('--password', required=True)
    p.add_argument('--device')
    p.add_argument('-v', '--verbose', action='store_true')
    args = p.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    return asyncio.run(_run(args))
if __name__ == '__main__':
    raise SystemExit(main())
