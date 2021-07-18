import sys

from modules.utility import Utility
from modules.controller import EdiViewerController


def launch_application():
    try:
        controller = EdiViewerController()
        controller.start_application()

    except Exception as e:
        Utility.show_error('Error Starting Application', e)


if __name__ == '__main__':
    launch_application()
