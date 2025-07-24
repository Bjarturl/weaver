import time
import requests
import sys
import urllib3
import re
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEBUG_LOGS = True
MAX_RETRIES = 5
EXTRA_VARIABLE_TEMPLATE = "<param><value><string>dummy_value_{}</string></value></param>"


class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def log_to_file(message, filename='listmethods_logs.txt'):
    with open(filename, 'a', encoding="utf-8") as file:
        file.write(message + '\n')


def clear_log_file(filename='listmethods_logs.txt'):
    with open(filename, 'w') as file:
        file.truncate()


def send_request(url, data, custom_header, retries=0):
    headers = {'Content-Type': 'application/xml'}
    if custom_header:
        headers['X-BugBounty'] = custom_header

    try:
        response = requests.post(
            f"{url}/xmlrpc.php", data=data, headers=headers, timeout=10, verify=False)

        if DEBUG_LOGS:
            log_to_file(
                f"Request URL: {url}\nRequest Data: {data}\nResponse: {response.text}")

        if (response.status_code == 400 or "<int>400</int>" in response.text) and "system.multicall" not in data:
            if retries < MAX_RETRIES:
                print(
                    bcolors.WARNING + f"[WARNING] Received 400 error, retrying with extra variables ({retries+1}/{MAX_RETRIES})..." + bcolors.ENDC)
                time.sleep(1)
                new_data = add_extra_variables(data, retries+1)
                return send_request(url, new_data, custom_header, retries + 1)
            else:
                print(
                    bcolors.FAIL + "[ERROR] Maximum retries reached. Could not bypass 400 error." + bcolors.ENDC)
                return None

        return response.text

    except requests.exceptions.RequestException as e:
        error_msg = f"[ERROR] Request failed: {e}"
        if DEBUG_LOGS:
            log_to_file(error_msg)
        print(bcolors.FAIL + error_msg + bcolors.ENDC)
        return None


def add_extra_variables(data, count):
    """Injects additional dummy variables into an XML request."""

    if "system.multicall" in data:
        return data

    extra_vars = "".join(EXTRA_VARIABLE_TEMPLATE.format(i)
                         for i in range(count))

    updated_data = data.replace("</params>", f"{extra_vars}</params>")
    return updated_data


def check_response(content):
    if content is None:
        return False
    error_pattern = re.compile(r'<int>(-32700|400|403|405)</int>')
    return error_pattern.search(content) is None


def create_listmethods_payload():
    return '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName><params></params></methodCall>'


def create_multicall_payload(methods):
    xml = '<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName><params><param><value><array><data>'
    for method in methods:
        xml += f"""
        <value>
          <struct>
            <member><name>methodName</name><value><string>{method}</string></value></member>
            <member><name>params</name><value><array><data>
              <value><string></string></value>
              <value><string></string></value>
              <value><string></string></value>
            </data></array></value></member>
          </struct>
        </value>
        """
    xml += '</data></array></value></param></params></methodCall>'
    return xml


def create_single_method_payload(method, param_count=0):
    xml = f'<?xml version="1.0"?><methodCall><methodName>{method}</methodName><params>'
    for i in range(param_count):
        xml += '<param><value><string></string></value></param>'
    xml += '</params></methodCall>'
    return xml


def create_multicall_payload_with_params(methods, param_count=0):
    xml = '<?xml version="1.0"?><methodCall><methodName>system.multicall</methodName><params><param><value><array><data>'
    for method in methods:
        xml += f"""
        <value>
          <struct>
            <member><name>methodName</name><value><string>{method}</string></value></member>
            <member><name>params</name><value><array><data>"""

        for i in range(param_count):
            xml += '<value><string></string></value>'

        xml += """</data></array></value></member>
          </struct>
        </value>
        """
    xml += '</data></array></value></param></params></methodCall>'
    return xml


def test_methods_with_multicall_params(url, methods, custom_header, max_params=10):
    """Test methods with multicall, incrementally adding parameters until they work."""
    remaining_methods = methods.copy()
    successful_methods = []

    for param_count in range(max_params + 1):
        if not remaining_methods:
            break

        multicall_payload = create_multicall_payload_with_params(
            remaining_methods, param_count)
        multicall_response = send_request(
            url, multicall_payload, custom_header)

        if multicall_response is None:
            break

        results = re.findall(
            r'<name>faultString</name><value><string>(.*?)</string></value>', multicall_response)

        methods_to_remove = []

        for i, method in enumerate(remaining_methods):
            if i < len(results):
                error_msg = results[i]
                if "Ónægur breytufjöldi" not in error_msg:

                    print(
                        bcolors.FAIL + f"[-] Method {method} is not accessible without authentication ({param_count} params)." + bcolors.ENDC)
                    methods_to_remove.append(method)
            else:

                print(
                    bcolors.OKGREEN + f"[+] Method {method} is accessible without authentication ({param_count} params)." + bcolors.ENDC)
                successful_methods.append((method, param_count))
                methods_to_remove.append(method)

        remaining_methods = [
            m for m in remaining_methods if m not in methods_to_remove]

    for method in remaining_methods:
        print(bcolors.FAIL +
              f"[-] Method {method} is not accessible without authentication ({max_params} params)." + bcolors.ENDC)

    return successful_methods


def check_methods(url, custom_header):
    response = send_request(url, create_listmethods_payload(), custom_header)
    if response is None:
        print(bcolors.FAIL +
              "[ERROR] Failed to retrieve methods list." + bcolors.ENDC)
        return

    methods = re.findall(r'<string>(.*?)</string>', response)
    print(bcolors.OKBLUE +
          f"[*] Retrieved {len(methods)} methods." + bcolors.ENDC)

    system_methods = {'system.multicall', 'system.listMethods'}

    if 'system.multicall' not in methods:
        print(bcolors.WARNING +
              "[!] system.multicall not available, only listing methods:" + bcolors.ENDC)
        for method in methods:
            print(bcolors.OKBLUE + f"[*] Method: {method}" + bcolors.ENDC)
        return

    test_methods = [m for m in methods if m not in system_methods]

    for method in methods:
        if method in system_methods:
            print(bcolors.OKGREEN +
                  f"[+] Method {method} is accessible without authentication (0 params)." + bcolors.ENDC)

    if test_methods:
        multicall_payload = create_multicall_payload(test_methods)
        multicall_response = send_request(
            url, multicall_payload, custom_header)

        if multicall_response is None:
            print(bcolors.FAIL +
                  "[ERROR] Failed to execute multicall." + bcolors.ENDC)
            return

        results = re.findall(
            r'<name>faultString</name><value><string>(.*?)</string></value>', multicall_response)

        param_error_methods = []
        remaining_methods = []

        for i, method in enumerate(test_methods):
            if i < len(results):
                error_msg = results[i]
                if "Ónægur breytufjöldi" in error_msg:
                    param_error_methods.append(method)
                else:
                    print(
                        bcolors.FAIL + f"[-] Method {method} is not accessible without authentication (0 params)." + bcolors.ENDC)
            else:
                print(bcolors.OKGREEN +
                      f"[+] Method {method} is accessible without authentication (0 params)." + bcolors.ENDC)

        if param_error_methods:
            successful_methods = test_methods_with_multicall_params(
                url, param_error_methods, custom_header)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='WordPress XML-RPC Method Enumeration')
    parser.add_argument('url', help='Target WordPress URL')
    parser.add_argument(
        '--header', help='Custom HTTP header (format: "Key: Value")')

    args = parser.parse_args()

    start_time = time.time()

    # Parse the header argument
    custom_header = ""
    if args.header:
        if args.header.startswith("X-BugBounty:"):
            custom_header = args.header[12:].strip()
        else:
            custom_header = args.header

    if DEBUG_LOGS:
        clear_log_file()

    check_methods(args.url, custom_header)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(bcolors.OKBLUE +
          f"\n[*] Total execution time: {elapsed_time:.2f} seconds" + bcolors.ENDC)
