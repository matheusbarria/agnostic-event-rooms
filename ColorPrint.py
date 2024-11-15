# START_STR = "\033["
START_STR = "\u001b["

# ANSI escape codes for text colors
COLORS = {
    'gray': '30m',
    'red': '31m',
    'bright_red': '91m',
    'green': '32m',
    'yellow': '33m',
    'blue': '34m',
    'bright_blue': '94m',
    'purple': '35m',
    'cyan': '36m',
    'white': '37m',
    'reset': '0m',
    'bold': '1m',
    'italics': '3m',
    'italic': '3m',
    'underline': '4m',
    '': '0m'
}

BACKGROUND_COLORS = {
    'black': '40;',
    'red': '41;',
    'green': '42;',
    'yellow': '43;',
    'blue': '44;',
    'purple': '45;',
    'cyan': '46;',
    'white': '47;',
    '': '0;'
}

@staticmethod
def color_print(text, color="", background="", end='\n'):
    """
    Print text in the specified color.
    
    text: text to be printed
    color (optional): the color to print the text
    background (optional): the background color on which to print
    end (optional): same arg as in print()
    """
    if background and not color:
        color = "white"
    try:
        print(f"{START_STR}{BACKGROUND_COLORS[background]}{COLORS[color]}{text}{START_STR}{COLORS['reset']}",end=end)
    except KeyError as ex:
        print(text, end=end)

def display_options():
    print()
    color_print("Color Options:", color="underline", background="black")
    for color in COLORS.keys():
        if not color or color == "reset":
            continue
        color_print(f"{color}",end='; ',color=color)
    print("\n")
    color_print("Background Options:", color="underline", background="black")
    for background in BACKGROUND_COLORS.keys():
        if not background:
            continue
        color_print(f"{background}",end='; ',background=background)
    print()

if __name__ == '__main__':
    display_options()
    # Example usage:
    # color_print("This text is in gray.",'gray')
    # color_print("This text is in white.",'white')
    # color_print("This text is in red.",'red')
    # color_print("This text is in bright red.",'bright_red')
    # color_print("This text is in green.",'green')
    # color_print("This text is in yellow.",'yellow')
    # color_print("This text is in bright blue.",'bright_blue')
    # color_print("This text is in blue.",'blue')
    # color_print("This text is in cyan.",'cyan')
    # color_print("This text is in purple.",'purple')
    # color_print("The background is red.",background="red")
    # color_print("The background is green.",background="green")
    # color_print("This text is bold.",color="bold", background="black")
    # color_print("This text is italic.",color="italics", background="black")
    # color_print("This text is underlined.",color="underline", background="black")
