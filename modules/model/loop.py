class Loop:
    loop_id = ''
    segments = []

    def loop(self, loop_id):
        self.loop_id = loop_id

    def process_loop(self, elements, segments_in_loop):
        index = 0
        segment_id = elements[0]
        try:
            index = segments_in_loop.index(segment_id)
            self.segments.append(elements)
            return 1
        except ValueError:
            # print(str(index) + ' value error raised.')
            return 0
