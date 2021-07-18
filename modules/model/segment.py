class Segment:
    segment_id = ''

    def get_elements(self, line, delimiter, terminator):
        elements = []
        # print('segment line: '+line)
        index = 0
        while index != -1:
            index = line.find(delimiter)
            elements.append(line[0:index])
            line = line[index + 1:len(line)]
            # print(line)
        self.segment_id = elements[0]
        elements[len(elements) - 1] = line.replace(terminator, '')  # remove terminator string
        # print(self.segment_id)
        # for element in elements:
        # print(element)
        return elements
