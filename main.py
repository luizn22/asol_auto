# This is a sample Python script.
from foo import create_txt


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def run():
    create_txt(
        [r'C:\Users\luiz\PycharmProjects\asol_auto\plusw.txt'],
        [1, 2, 3],
        r'C:\Users\luiz\PycharmProjects\asol_auto',
        rotate_90_in_z=True,
        xy_center=(704.1, -13.75),
        drop_angles=True,
    )


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
