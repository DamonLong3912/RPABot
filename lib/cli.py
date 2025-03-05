import argparse
import json

def cli(obj):
  arg_parser = argparse.ArgumentParser()
  # python x.x task_name [params]
  arg_parser.add_argument('method', type=str)
  arg_parser.add_argument('--method', type=str, default='run')
  arg_parser.add_argument('--params', type=str, default='')
  args = arg_parser.parse_args()
  params_str = args.params
  if params_str:
    try:
      params = json.loads(params_str)
    except Exception as e:
      params = [params_str]
  else:
    params = []
  method = getattr(obj, args.method)

  if callable(method):
    method(*params)
  else:
    print(f"method {args.method} not found")