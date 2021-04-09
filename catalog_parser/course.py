
class Prerequisite:

    def __init__(self, children: [], operation='and'):
        self._children = []  # courses or prerequisites
        self._operation = operation  # and / or

    def __repr__(self):
        return self._operation.join(self._children)
