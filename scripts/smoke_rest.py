"""Check Rasa + SDK + data together through the REST channel."""
import argparse
import json
from urllib.request import Request, urlopen


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://localhost:5005')
    args=parser.parse_args()
    cases=[
        ('UTH đào tạo những ngành gì','Công nghệ thông tin'),
        ('điểm chuẩn ngành Công nghệ thông tin năm 2026','UTHUIT05A'),
        ('Em có 8 điểm Toán, 8 điểm Hóa và 9 điểm Anh','D07: 25/30'),
        ('học phí của trường','KHÔNG áp dụng chung'),
    ]
    for i,(text,expected) in enumerate(cases):
        request=Request(args.url+'/webhooks/rest/webhook',data=json.dumps(dict(sender=f'e2e-{i}',message=text)).encode(),headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=60) as response:
            data=json.load(response)
        answer='\n'.join(item.get('text','') for item in data)
        assert expected in answer,(text,answer)
        print('PASS REST',text)


if __name__=='__main__':main()
