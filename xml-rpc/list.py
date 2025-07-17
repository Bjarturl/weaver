import time
import requests
import sys
import urllib3
import re
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EXTRA_VARIABLE_TEMPLATE = "<param><value><string>dummy_value_{}</string></value></param>"


class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def log_to_file(message, filename='listmethods_logs.txt', debug_logs=True):
    if debug_logs:
        with open(filename, 'a', encoding="utf-8") as file:
            file.write(message + '\n')


def clear_log_file(filename='listmethods_logs.txt'):
    with open(filename, 'w') as file:
        file.truncate()


def send_request(url, data, headers=None, max_retries=5, debug_logs=True, log_file='listmethods_logs.txt', retries=0):
    if headers is None:
        headers = {'Content-Type': 'application/xml'}

    try:
        response = requests.post(
            f"{url}/xmlrpc.php", data=data, headers=headers, timeout=10, verify=False)

        if debug_logs:
            log_to_file(
                f"Request URL: {url}\nRequest Data: {data}\nResponse: {response.text}", log_file, debug_logs)

        if response.status_code == 400 or "<int>400</int>" in response.text:
            if retries < max_retries:
                print(
                    bcolors.WARNING + f"[WARNING] Received 400 error, retrying with extra variables ({retries+1}/{max_retries})..." + bcolors.ENDC)
                time.sleep(1)  # Short delay before retrying
                new_data = add_extra_variables(data, retries+1)
                return send_request(url, new_data, headers, max_retries, debug_logs, log_file, retries + 1)
            else:
                print(
                    bcolors.FAIL + "[ERROR] Maximum retries reached. Could not bypass 400 error." + bcolors.ENDC)
                return None

        return response.text

    except requests.exceptions.RequestException as e:
        error_msg = f"[ERROR] Request failed: {e}"
        if debug_logs:
            log_to_file(error_msg, log_file, debug_logs)
        print(bcolors.FAIL + error_msg + bcolors.ENDC)
        return None


def add_extra_variables(data, count):
    """Injects additional dummy variables into an XML request."""
    extra_vars = "".join(EXTRA_VARIABLE_TEMPLATE.format(i)
                         for i in range(count))

    # Locate the position before the closing `</params>` tag and insert extra params
    updated_data = data.replace("</params>", f"{extra_vars}</params>")
    return updated_data


def check_response(content):
    if content is None:
        return False
    error_pattern = re.compile(r'<int>(-32700|400|403|405)</int>')
    return error_pattern.search(content) is None


def create_listmethods_payload():
    return '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'


def create_multicall_payload(methods):
    xml = '<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName><params><param><value><array><data>'
    for method in methods:
        xml += f"""
        <value>
          <struct>
            <member><n>methodName</n><value><string>{method}</string></value></member>
            <member><n>params</n><value><array><data></data></array></value></member>
          </struct>
        </value>
        """
    xml += '</data></array></value></param></params></methodCall>'
    return xml


def check_methods(url, headers=None, max_retries=5, debug_logs=True, log_file='listmethods_logs.txt'):
    response = send_request(url, create_listmethods_payload(
    ), headers, max_retries, debug_logs, log_file)
    if response is None:
        print(bcolors.FAIL +
              "[ERROR] Failed to retrieve methods list." + bcolors.ENDC)
        return

    methods = re.findall(r'<string>(.*?)</string>', response)
    print(bcolors.OKBLUE +
          f"[*] Retrieved {len(methods)} methods." + bcolors.ENDC)

    multicall_payload = create_multicall_payload(methods)
    multicall_response = send_request(
        url, multicall_payload, headers, max_retries, debug_logs, log_file)

    if multicall_response is None:
        print(bcolors.FAIL +
              "[ERROR] Failed to execute multicall." + bcolors.ENDC)
        return

    results = re.findall(
        r'<n>faultString</n><value><string>(.*?)</string></value>', multicall_response)
    for i, method in enumerate(methods):
        if i < len(results):
            print(
                bcolors.FAIL + f"[-] Method {method} is not accessible without authentication: {results[i]}" + bcolors.ENDC)
        else:
            print(bcolors.OKGREEN +
                  f"[+] Method {method} is accessible without authentication." + bcolors.ENDC)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='WordPress XML-RPC Method Enumeration')
    parser.add_argument('url', help='Target WordPress URL')
    parser.add_argument('--header', '-H', action='append', dest='headers',
                        help='Custom HTTP headers (format: "Key: Value")')
    parser.add_argument('--max-retries', type=int, default=5,
                        help='Maximum retry attempts for 400 errors (default: 5)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--log-file', default='listmethods_logs.txt',
                        help='Log file path (default: listmethods_logs.txt)')

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

    check_methods(args.url, custom_headers, args.max_retries,
                  args.debug, args.log_file)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(bcolors.OKBLUE +
          f"\n[*] Total execution time: {elapsed_time:.2f} seconds" + bcolors.ENDC)
