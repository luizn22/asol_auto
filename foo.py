import os
import re
from typing import List


class Dot:
    pattern = r'P\[\d+\]'
    def __init__(self, data: str):

        result = re.findall(self.pattern, data)
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

    def apply_z_delta(self, z_delta: float):
        self.Z = round(self.Z + z_delta, 2)
        return self

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
            self.data = ':' + data.split(':')[1]

    def to_str(self, idx, dot_idx: int = None):
        if self.has_p:
            if dot_idx is None:
                raise ValueError('trag has dot, hence it must be informed to convert to str')
            return f' {idx}{self.pre}P[{dot_idx}]{self.pos}'
        else:
            return f' {idx}{self.data}'


class RouteData:
    mn_splitter = '/MN\n'
    pos_splitter = '\n/POS'
    end_spliter = '\n/END'

    def __init__(self, route_str: str):
        self.header, body = route_str.split(self.mn_splitter)
        self.mn, self.pos = body.split(self.pos_splitter)

        self.trag = [TrajectRow(trag_data) for trag_data in self.mn.split('\n')]
        self.dots = [Dot(dot_data) for dot_data in self.pos.replace(self.end_spliter, '').split('\n};\n')[:-1]]


class NewRoute:
    def __init__(self, src_route_data: List[RouteData], layer_z_delta: List[float]):
        if not src_route_data:
            raise ValueError('src_route_data must not be empty')
        if not layer_z_delta:
            raise ValueError('layer_delta must not be empty')

        self.src_route_data = src_route_data
        self.header_src_route = self.src_route_data[0]

        self.header = self.header_src_route.header

        self.layer_z_delta = [0.0] + layer_z_delta

        self.trag_strs = []
        self.prev_trag_idx = 1
        self.dots_strs = []
        self.prev_dot_idx = 1

        self.build_route()

    def build_route(self):
        cur_route_idx = 0
        for z_delta in self.layer_z_delta:
            cur_route = self.src_route_data[cur_route_idx]

            old_to_new_dot_di = {}
            cur_dot_idx = self.prev_dot_idx

            for en_idx, dot in enumerate(cur_route.dots):
                cur_dot_idx = en_idx + self.prev_dot_idx
                old_to_new_dot_di[dot.src_idx] = cur_dot_idx
                self.dots_strs.append(dot.apply_z_delta(z_delta).to_str(cur_dot_idx))

            self.prev_dot_idx = cur_dot_idx

            cur_trag_idx = self.prev_trag_idx
            for en_idx, trag in enumerate(cur_route.trag):
                cur_trag_idx = en_idx + self.prev_trag_idx
                if trag.has_p:
                    self.trag_strs.append(trag.to_str(cur_trag_idx, old_to_new_dot_di.get(trag.dot_idx)))
                else:
                    self.trag_strs.append(trag.to_str(cur_trag_idx))

            self.prev_trag_idx = cur_trag_idx

            cur_route_idx += 1
            if cur_route_idx >= len(self.src_route_data):
                cur_route_idx = 0

    def to_str(self) -> str:
        return (
            self.header
            + self.header_src_route.mn_splitter
            + '\n'.join(self.trag_strs)
            + self.header_src_route.pos_splitter
            + '\n'.join(self.dots_strs)
            + self.header_src_route.end_spliter
        )


def create_txt(src_data: List[str], layer_z_delta: List[float], out_path: str):
    r_dat_li = []

    for src_data_item in src_data:
        with open(src_data_item, "r") as file:
            src = file.read()

        r_dat_li.append(RouteData(src))

    new_route = NewRoute(r_dat_li, layer_z_delta)
    new_route_str = new_route.to_str()

    print(new_route_str)

    file_path = os.path.join(out_path, 'prg.txt')
    file = open(file_path, "w")
    file.write(new_route_str)

    file.close()
