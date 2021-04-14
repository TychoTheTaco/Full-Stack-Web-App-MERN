class TreeParser:

    def __init__(self, group_open: str, group_close: str, item_separators: [str]):
        self._group_open = group_open
        self._group_close = group_close
        self._item_separators = item_separators

    def tokenize(self, string: str) -> [str]:

        # Add spaces around control strings so we can split the input on spaces
        string = string.replace(self._group_open, f' {self._group_open} ')
        string = string.replace(self._group_close, f' {self._group_close} ')
        for separator in self._item_separators:
            string.replace(separator, f' {separator} ')

        tokens = []
        item_data = []

        def maybe_add_item():
            data = ' '.join(item_data).strip()
            if len(data) > 0:
                tokens.append(data)
                item_data.clear()

        for item in string.split():

            # Ignore empty items
            if len(item) == 0:
                continue

            if item.lower() in [x.lower() for x in [self._group_open, self._group_close] + list(self._item_separators)]:
                maybe_add_item()
                tokens.append(item)
            else:
                item_data.append(item)

        maybe_add_item()

        return tokens
