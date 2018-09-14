# Python program to print
# colored text and background


def prRed(skk, end=None): print("\033[91m {}\033[00m".format(skk), end=end)


def prGreen(skk, end=None): print("\033[92m {}\033[00m".format(skk), end=end)


def prYellow(skk, end=None): print("\033[93m {}\033[00m".format(skk), end=end)


def prLightPurple(skk, end=None): print("\033[94m {}\033[00m".format(skk), end=end)


def prPurple(skk, end=None): print("\033[95m {}\033[00m".format(skk), end=end)


def prCyan(skk, end=None): print("\033[96m {}\033[00m".format(skk), end=end)


def prLightGray(skk, end=None): print("\033[97m {}\033[00m".format(skk), end=end)


def prBlack(skk, end=None): print("\033[98m {}\033[00m".format(skk), end=end)


if __name__ == "__main__":
    prCyan("Hello World, ")
    prYellow("It's")
    prGreen("Geeks")
    prRed("For", end="")
    prGreen("[OK]")
