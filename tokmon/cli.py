import asyncio
import argparse
import json
import sys
import pkg_resources

from tokmon.tokmon import TokenMonitor
from typing import Dict

PROG_NAME = "tokmon"

BOLD = "\033[1m"
RESET = "\033[0m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"
GREEN = "\033[32m"

def bold(s:str):
    return f"{BOLD}{s}{RESET}"

def color(s:str, color:str, bold:bool = True):
    if bold:
        return f"{BOLD}{color}{s}{RESET}"
    else:
        return f"{color}{s}{RESET}"

def generate_usage_report(monitored_invocation:str ,model:str, usage_data:Dict, pricing:Dict, total_cost:float):
    model_pricing = pricing[model]

    cost_str = f"${total_cost:.6f}"
    report_header = f"{PROG_NAME} cost report:"

    return f"""
{color(report_header, GREEN)}
{color('='*80, GRAY, bold=False)}
{bold("Monitored invocation")}: {monitored_invocation}
{bold("Model")}: {model}
{bold("Usage")}: {usage_data}
{bold("Pricing")}: {model_pricing}
{color("Cost", MAGENTA)}: {color(cost_str, MAGENTA)}
{color('='*80, GRAY, bold=False)}
"""

OPENAI_API_PATH = "https://api.openai.com"

def cli():
    """
    The {PROG_NAME} utility can be used to monitor the cost of OpenAI API calls made by a program.
    After te program has finished running, the {PROG_NAME} will print the total cost of the program.
    """

    parser = argparse.ArgumentParser(description="A utility to monitor OpenAI token cost of a target program.",
                                     add_help=False)

    parser.add_argument("program_name", nargs="?", help="The name of the monitored program")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="The command and arguments to run the monitored program")
    parser.add_argument("-p", "--pricing", type=str, help="Path to a custom pricing JSON file", default=None)
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")



    args = parser.parse_args()

    if not args.program_name:
        parser.print_help()
        sys.exit(1)

    # Note: pricing data may go out of date
    if args.pricing:
        pricing_json = args.pricing
    else:
        pricing_json = pkg_resources.resource_filename("tokmon", "pricing.json")

    with open(pricing_json, "r") as f:
        pricing = json.load(f)

    monitored_prog = f"{args.program_name} { ' '.join(args.args) if args.args else ''}"
    model, usage_data, total_cost = None, None, 0

    # Instantiate the token monitor
    tokmon = TokenMonitor(OPENAI_API_PATH, pricing, args.program_name, *args.args)

    try:
        monitoring_str = f"[{PROG_NAME}] Monitoring program for token costs for {color(monitored_prog, GREEN)} ..."
        print(f"{color(monitoring_str, MAGENTA)}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(tokmon.start_monitoring())
    except KeyboardInterrupt:
        interrupted_str = f"\n[{PROG_NAME}] Interrupted. Generating token usage report ..."
        print(f"{color(interrupted_str, MAGENTA)}")
    finally:
        tokmon.stop_monitoring()
        model, usage_data, total_cost = tokmon.calculate_usage()
        if model and usage_data:
            monitored_invocation = [args.program_name] + [arg for arg in args.args]
            report = generate_usage_report(monitored_invocation, model, usage_data, pricing, total_cost)
            print(f"\n{report}")
        else:
            status_str = f"[{PROG_NAME}] No OpenAI API calls detected for `{monitored_prog}`."
            print(f"{color(status_str, MAGENTA)}")

if __name__ == '__main__':
    cli()