import html


def bold(text):
    """Generates a html formatted bold text"""
    return "<b>{text}</b>".format(text=text)


def link(url, name):
    """Generates a html formatted named link"""
    return "<a href=\"{url}\">{name}</a>".format(url=url, name=html.escape(name))


def price(price_value):
    """Generates a formatted price tag from a value"""
    return "{price:+.2f} €".format(price=price_value)
