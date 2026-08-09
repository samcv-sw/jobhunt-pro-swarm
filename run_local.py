import sys
import os
import uvicorn

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)
os.environ['FORCE_SQLITE'] = '1'

if __name__ == '__main__':
    uvicorn.run("web.app_v2:app", host='127.0.0.1', port=8000)
