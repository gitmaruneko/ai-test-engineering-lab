from anthropic import Anthropic


def analyze_log(log):
    # TODO: Claude API integration
    pass


def main():
    log = """
    BMC reset triggered
    Redfish connection lost
    Reconnect failed after 400 sec
    """

    result = analyze_log(log)

    print(result)


if __name__ == "__main__":
    main()