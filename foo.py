import os
import re
from typing import List, Tuple


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

    def drop_angles(self):
        self.R = '0.00'
        self.P = '0.00'
        self.W = '0.00'
        return self

    def rotate_90_on_xy(self, x, y):
        old_x = self.X
        old_y = self.Y
        local_x = old_x - x
        local_y = old_y - y
        self.X = round(-local_y + x, 2)
        self.Y = round(local_x + y, 2)
        return self

    def to_str(self, idx: int) -> str:
        return f'''P[{idx}]{{
   GP1:
    UF : {self.UF}, UT : {self.UT},		CONFIG : '{self.CONFIG}',
    X =   {self.X:.2f}  mm,	Y =   {self.Y:.2f}  mm,	Z =   {self.Z:.2f}  mm,
    W =     {self.W:.2f} deg,	P =     {self.P:.2f} deg,	R =    {self.R:.2f} deg
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
    droped_headers = [
        'OWNER',
        'COMMENT',
        'CREATE',
        'MODIFIED',
        'FILE_NAME',
        'VERSION',
        'LINE_COUNT',
        'PROTECT',
        'TCD',
        'STACK_SIZE',
        'TASK_PRIORITY',
        'TIME_SLICE',
        'BUSY_LAMP_OFF',
        'ABORT_REQUEST',
        'PAUSE_REQUEST',
        'DEFAULT_GROUP',
        'CONTROL_CODE',
        'PROG_SIZE',
        'MEMORY_SIZE',
    ]

    def __init__(self, src_route_data: List[RouteData], layer_z_delta: List[float], drop_unused_headers=False, 
                 rotate_90_in_z: bool, xy_center: Tuple[float, float], drop_angles: bool):
        if not src_route_data:
            raise ValueError('src_route_data must not be empty')

        self.rotate_90_in_z = rotate_90_in_z
        self.xy_center = xy_center
        self.drop_angles = drop_angles

        self.src_route_data = src_route_data
        self.header_src_route = self.src_route_data[0]

        self.header = self.header_src_route.header
        if drop_unused_headers:
            self.header = self.filter_header(self.header)

        self.layer_z_delta = [0.0] + layer_z_delta

        self.trag_strs = []
        self.prev_trag_idx = 1
        self.dots_strs = []
        self.prev_dot_idx = 1

        self.build_route()

    def filter_header(self, header):
        lines = header.split('\n')  # Split the big string into lines
        filtered_lines = []

        for line in lines:
            if not any(substring in line for substring in self.droped_headers):
                filtered_lines.append(line)

        result = '\n'.join(filtered_lines)  # Join the remaining lines back into a string
        return result

    def build_route(self):
        cur_route_idx = 0
        for z_delta in self.layer_z_delta:
            cur_route = self.src_route_data[cur_route_idx]

            old_to_new_dot_di = {}
            cur_dot_idx = self.prev_dot_idx

            for en_idx, dot in enumerate(cur_route.dots):
                cur_dot_idx = en_idx + self.prev_dot_idx
                old_to_new_dot_di[dot.src_idx] = cur_dot_idx
                if self.drop_angles:
                    dot = dot.drop_angles()
                if self.rotate_90_in_z:
                    dot = dot.rotate_90_on_xy(*self.xy_center)

                self.dots_strs.append(
                    dot.apply_z_delta(z_delta).to_str(cur_dot_idx)
                )

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
                + self.header_src_route.pos_splitter + '\n'
                + '\n'.join(self.dots_strs)
                + self.header_src_route.end_spliter
                + '\n'
        )


def create_txt(src_data: List[str], layer_z_delta: List[float], out_path: str,
               rotate_90_in_z: bool, xy_center: Tuple[float, float], drop_angles: bool):
    r_dat_li = []

    for src_data_item in src_data:
        with open(src_data_item, "r") as file:
            src = file.read()

        r_dat_li.append(RouteData(src))

    new_route = NewRoute(r_dat_li, layer_z_delta, rotate_90_in_z=rotate_90_in_z, xy_center=xy_center,
                         drop_angles=drop_angles)
    new_route_str = new_route.to_str()

    print(new_route_str)

    file_path = os.path.join(out_path, 'prg.txt')
    file = open(file_path, "w")
    file.write(new_route_str)

    file.close()
