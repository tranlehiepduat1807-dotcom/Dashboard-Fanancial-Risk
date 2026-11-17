"""Configurable, offline FSS FLEX export mapper. No undocumented endpoint is assumed."""
import json
from decimal import Decimal, InvalidOperation

def normalize(payload, spec):
    path=spec.get('rows_path',[]); items=payload
    for key in path: items=items[key]
    if not isinstance(items,list): raise ValueError('rows_path phải trỏ tới một mảng')
    out=[]
    for i,item in enumerate(items):
        row={}
        for dest,rule in spec['fields'].items():
            if 'constant' in rule: value=rule['constant']
            else:
                value=item
                try:
                    for key in rule['path']: value=value[key]
                except (KeyError,TypeError): raise ValueError(f'Dòng {i+1}: thiếu trường ánh xạ {dest}')
            if 'scale' in rule:
                try:
                    number=Decimal(str(value))*Decimal(str(rule['scale']))
                    if not number.is_finite(): raise ValueError('non-finite')
                    value=float(number)
                except (InvalidOperation,ValueError,TypeError): raise ValueError(f'Dòng {i+1}: {dest} không phải số hữu hạn')
            if 'values' in rule:
                if str(value) not in rule['values']: raise ValueError(f'Dòng {i+1}: chưa ánh xạ giá trị {dest}')
                value=rule['values'][str(value)]
            row[dest]=value
        out.append(row)
    return out

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description='Chuyển JSON export FLEX sang schema chuẩn. Không kết nối mạng.')
    p.add_argument('--input',required=True);p.add_argument('--mapping',required=True);p.add_argument('--output',required=True)
    args=p.parse_args()
    from pathlib import Path
    payload=json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
    spec=json.loads(Path(args.mapping).read_text(encoding='utf-8-sig'))
    result=normalize(payload,spec)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Normalized {len(result)} rows; submit through authenticated import API for validation and approval.')
