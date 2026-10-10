"""Exercise the running SDK server through HTTP (no test doubles)."""
import argparse
import json
from urllib.request import Request, urlopen


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://localhost:5055')
    args=parser.parse_args()
    with urlopen(args.url+'/health',timeout=10) as response:
        assert response.status==200
    for action,text,slots,expected in [
        ('action_tinh_khoi_va_goi_y_nganh','8 điểm Toán, 8 điểm Hóa và 9 điểm Anh',{},'D07: 25/30'),
        ('action_tra_loi_diem_chuan_nganh','điểm chuẩn năm 2026',{'ten_nganh':'CNTT'},'UTHUIT05A'),
        ('action_tra_loi_diem_chuan_nganh','điểm chuẩn năm 2024',{'ten_nganh':'CNTT'},'Chưa có'),
        ('action_tra_loi_thong_tin_truong','học phí',{},'KHÔNG áp dụng chung'),
    ]:
        body=dict(next_action=action,sender_id='smoke-test',domain={},version='3.6.21',
                  tracker=dict(sender_id='smoke-test',slots=slots,latest_message=dict(text=text,intent={'name':'hoi_hoc_phi'}),
                               events=[],paused=False,latest_action_name='action_listen',active_loop={}))
        request=Request(args.url+'/webhook',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=10) as response:
            result=json.load(response)
        messages='\n'.join(item.get('text','') for item in result['responses'])
        assert expected in messages,(action,messages)
        print('PASS',action)


if __name__=='__main__':main()
