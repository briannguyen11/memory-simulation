class logical_addr:
    def __init__(self, page_num: int, offset: int):
        # Instance attributes (unique to each instance)
        self.page_num = page_num
        self.offset = offset
