from modules.utility import Utility
from modules.model.loop import Loop
from modules.model.segment import Segment


class Transaction:
    process__identification_loop = False
    loop = Loop()

    def __init__(self):
        self.complete = False
        self.identification = ''

    def process_transaction(self, transaction, delimiter, terminator):
        # 01 Prefix, 02 First Name, 03 First Middle name, 04 Second middle name, 05 Last Name
        name_parts = ['01', '02', '03', '04', '05']
        try:
            for segment in transaction:
                seg = Segment()
                elements = seg.get_elements(segment, delimiter, terminator)
                # print(elements)
                if not seg.segment_id:  # blank line
                    continue
                if (seg.segment_id == 'IN1') & (self.process__identification_loop is False):  # identification
                    if len(elements) > 2:
                        if elements[2] == str('04') or elements[2] == str('02'):
                            # print(elements)
                            if len(elements) > 4:
                                if elements[6] == '51':
                                    self.process__identification_loop = True
                            else:
                                # print(elements)
                                self.process__identification_loop = True
                if self.process__identification_loop:
                    if self.loop.process_loop(elements, ['IN1', 'IN2']) == 1:
                        if seg.segment_id != 'IN1':
                            try:
                                name_parts.remove(elements[1])
                                if len(elements) > 2:
                                    self.identification = self.identification + elements[2].strip(' ').title() + ' '
                            except ValueError:
                                pass  # do nothing
                    else:
                        name_parts.clear()
                        # print(self.identification)
                        self.process__identification_loop = False
                # print(elements)
            if not self.identification:
                self.identification = 'Unrecognized Transaction'
            self.complete = True
            return self.complete
        except Exception as e:
            print(e)
            print(len(elements))
            Utility.show_error('Transaction Error', e)
