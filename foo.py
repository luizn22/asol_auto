import os
import re


class Dot:
    def __init__(self, data: str):
        pattern = r'P\[\d+\]'

        result = re.findall(pattern, data)
        self.src_idx = result[0]

        li = data.replace('\t', '').split('GP1:\n')[1].replace('\n', '').replace(' ', '').replace('};', '').split(',')
        di = {}
        for item in li:
            if ':' in item:
                key, arg = item.split(':')
            else:
                key, arg = item.split('=')
            arg = arg.replace('mm', '')
            arg = arg.replace("''", '')
            arg = arg.replace('deg', '')

            di[key] = arg
        self.UF = int(di.get('UF'))
        self.UT = int(di.get('UT'))
        self.CONFIG = di.get('CONFIG')
        self.X = float(di.get('X'))
        self.Y = float(di.get('Y'))
        self.Z = float(di.get('Z'))
        self.W = float(di.get('W'))
        self.P = float(di.get('P'))
        self.R = float(di.get('R'))

    def to_str(self, idx: int) -> str:
        return f'''P[{idx}]
   GP1:
    UF : {self.UF}, UT : {self.UT},		CONFIG : {self.CONFIG},
    X =   {self.X}  mm,	Y =   {self.Y}  mm,	Z =   {self.Z}  mm,
    W =     {self.W} deg,	P =     {self.P} deg,	R =    {self.R} deg
}};'''


class TrajectRow:
    def __init__(self, data: str):
        pattern = r'P\[\d+\]'

        self.has_p = 'P[' in data
        if self.has_p:
            result = re.findall(pattern, data)
            self.dot_idx = result[0]
            self.pre, self.pos = re.split(pattern, data)
            self.pre = ':' + self.pre.split(':')[1]
        else:
            self.data = data

    def to_str(self, idx, dot_idx):
        if self.has_p:
            return f' {idx}{self.pre}P[{dot_idx}]{self.pos}'
        else:
            return self.data


def create_txt(src_data: str, out_path: str):
    with open(src_data, "r") as file:
        src = file.read()
    pos = src.split(r'/POS')[1].replace(r'/END', '')
    dots = [Dot(dot_data) for dot_data in pos.split('\n};\n')[:-1]]

    for dot, idx in zip(dots, range(len(dots))):
        dot.Z += 1000
        print(dot.to_str(idx))
    mn = src.split('/MN\n')[1].split('\n/POS')[0]
    trag = [TrajectRow(trag_data) for trag_data in mn.split('\n')]

    for t, idx in zip(trag, range(len(trag))):
        print(t.to_str(idx, idx))

    file_path = os.path.join(out_path, 'prg.txt')
    strings_to_write = [
        '''asdasdasd
        asdasdas
        asdasd''',
        'line_two\n',
        'line_three'
        'line_four?'
    ]

    file = open(file_path, "w")
    for s in strings_to_write:
        file.write(s)

    file.close()
